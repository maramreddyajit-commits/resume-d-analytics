"""Historical retail warehouse with reconciled integer-money arithmetic."""

from pathlib import Path
import sqlite3, json, hashlib
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = ROOT / "projects/marketscope/data"


def classify(raw):
    d = raw.copy()
    required = [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    ]
    if not set(required).issubset(d):
        raise ValueError("Retail schema mismatch")
    duplicate = d.duplicated(subset=required)
    d["duplicate"] = duplicate
    d["invoice"] = d.Invoice.astype(str).str.upper()
    d["product_key"] = d.StockCode.astype(str).str.upper()
    d["date_key"] = pd.to_datetime(
        d.InvoiceDate, errors="coerce", format="mixed"
    ).dt.strftime("%Y-%m-%d")
    d["quantity"] = pd.to_numeric(d.Quantity, errors="coerce")
    price = pd.to_numeric(d.Price, errors="coerce")
    d["customer_key"] = d["Customer ID"].apply(
        lambda x: "UNKNOWN" if pd.isna(x) else str(int(x))
    )
    d["location_key"] = d.Country.fillna("Unknown").astype(str)
    d["reason"] = "accepted"
    d.loc[~d.product_key.str.match(r"^\d{5}[A-Z]{0,2}$"), "reason"] = (
        "non-merchandise/adjustment"
    )
    d.loc[d.invoice.str.startswith("C") & (d.quantity >= 0), "reason"] = (
        "inconsistent cancellation"
    )
    d.loc[(price <= 0) | price.isna() | ~np.isfinite(price), "reason"] = (
        "invalid/zero price"
    )
    d.loc[
        (d.quantity == 0)
        | d.quantity.isna()
        | ~np.isfinite(d.quantity)
        | (d.quantity % 1 != 0),
        "reason",
    ] = "invalid quantity"
    d.loc[d.date_key.isna(), "reason"] = "invalid date"
    d.loc[duplicate, "reason"] = "exact duplicate"
    d["unit_micro"] = (price.fillna(0) * 1000000).round().astype("int64")
    d["amount_micro"] = d.unit_micro * d.quantity.fillna(0).astype("int64")
    d["line_id"] = np.arange(1, len(d) + 1)
    return d


def run():
    FOLDER.mkdir(parents=True, exist_ok=True)
    cache = FOLDER / "raw.pkl"
    source_hash = hashlib.sha256((FOLDER / "retail.xlsx").read_bytes()).hexdigest()
    cache_hash = FOLDER / "raw.cache.sha256"
    if cache.exists() and cache_hash.exists() and cache_hash.read_text() == source_hash:
        raw = pd.read_pickle(cache)
    else:
        sheets = pd.read_excel(
            FOLDER / "retail.xlsx", sheet_name=None, engine="openpyxl"
        )
        raw = pd.concat(sheets.values(), ignore_index=True)
        raw.to_pickle(cache)
        cache_hash.write_text(source_hash)
    d = classify(raw)
    clean = d[d.reason == "accepted"].copy()
    db = FOLDER / "warehouse.sqlite"
    if db.exists():
        db.unlink()
    with sqlite3.connect(db) as con:
        d[
            [
                "line_id",
                "invoice",
                "product_key",
                "date_key",
                "quantity",
                "unit_micro",
                "amount_micro",
                "customer_key",
                "location_key",
                "reason",
            ]
        ].to_sql("raw_classified", con, index=False)
        cols = [
            "line_id",
            "invoice",
            "product_key",
            "date_key",
            "quantity",
            "unit_micro",
            "amount_micro",
            "customer_key",
            "location_key",
        ]
        clean[cols].to_sql("fact_lines", con, index=False)
        clean[["product_key", "Description"]].drop_duplicates(
            "product_key", keep="last"
        ).rename(columns={"Description": "description"}).to_sql(
            "dim_product", con, index=False
        )
        pd.DataFrame({"customer_key": sorted(clean.customer_key.unique())}).to_sql(
            "dim_customer", con, index=False
        )
        pd.DataFrame({"location_key": sorted(clean.location_key.unique())}).to_sql(
            "dim_location", con, index=False
        )
        dates = pd.DataFrame({"date_key": sorted(clean.date_key.unique())})
        dates["month"] = dates.date_key.str[:7]
        dates.to_sql("dim_date", con, index=False)
        con.executescript((ROOT / "projects/marketscope/sql/models.sql").read_text())
        q = lambda sql: pd.read_sql_query(sql, con)
        totals = (
            q(
                "SELECT COUNT(*) lines,SUM(CASE WHEN quantity>0 THEN amount_micro ELSE 0 END) gross_micro,-SUM(CASE WHEN quantity<0 THEN amount_micro ELSE 0 END) returns_micro,SUM(amount_micro) net_micro,COUNT(DISTINCT CASE WHEN quantity>0 THEN invoice END) orders,COUNT(DISTINCT CASE WHEN customer_key != 'UNKNOWN' THEN customer_key END) known_customers FROM fact_lines"
            )
            .iloc[0]
            .to_dict()
        )
        for key in totals:
            totals[key] = int(totals[key])
        assert (
            totals["gross_micro"] - totals["returns_micro"]
            == totals["net_micro"]
            == int(clean.amount_micro.sum())
        )
        monthly = q("SELECT * FROM monthly ORDER BY month,country")
        products = q(
            "SELECT r.*,p.description FROM product_rank r JOIN dim_product p USING(product_key) ORDER BY rank LIMIT 30"
        )
        rfm = q(
            "SELECT segment,COUNT(*) customers,SUM(monetary) historical_gross FROM customer_rfm GROUP BY segment"
        )
        cohorts = q("SELECT * FROM cohort_retention ORDER BY cohort,month")
        cohort_rows = []
        for cohort, g in cohorts.groupby("cohort"):
            size = int(g.cohort_size.iloc[0])
            observed = {r.month: r for r in g.itertuples()}
            for month in pd.period_range(cohort, "2011-11", freq="M"):
                key = str(month)
                age = (month - pd.Period(cohort, freq="M")).n
                r = observed.get(key)
                returned = int(r.returned) if r is not None else 0
                cohort_rows.append(
                    {
                        "cohort": cohort,
                        "month": key,
                        "cohort_size": size,
                        "returned": returned,
                        "age_month": age,
                        "rate": returned / size,
                    }
                )
        cohorts = pd.DataFrame(cohort_rows)
        for name, frame in [
            ("monthly", monthly),
            ("products", products),
            ("rfm_segments", rfm),
            ("cohorts", cohorts),
        ]:
            frame.to_csv(FOLDER / (name + ".csv"), index=False)
        qa = {}
        qa["money_reconciliation"] = (
            totals["gross_micro"] - totals["returns_micro"] == totals["net_micro"]
        )
        qa["independent_pandas_net"] = (
            int(clean.amount_micro.sum()) == totals["net_micro"]
        )
        qa["independent_orders"] = (
            int(clean.loc[clean.quantity > 0, "invoice"].nunique()) == totals["orders"]
        )
        qa["monthly_reconciliation"] = (
            int(monthly.net_micro.sum()) == totals["net_micro"]
        )
        qa["monthly_order_reconciliation"] = (
            int(monthly.orders.sum()) == totals["orders"]
        )
        qa["unique_line_grain"] = (
            q("SELECT COUNT(*) n,COUNT(DISTINCT line_id) u FROM fact_lines").iloc[0].n
            == q("SELECT COUNT(*) n,COUNT(DISTINCT line_id) u FROM fact_lines")
            .iloc[0]
            .u
        )
        for dim, key in [
            ("dim_product", "product_key"),
            ("dim_customer", "customer_key"),
            ("dim_location", "location_key"),
            ("dim_date", "date_key"),
        ]:
            qa[dim + "_referential"] = (
                int(
                    q(
                        f"SELECT COUNT(*) n FROM fact_lines f LEFT JOIN {dim} d USING({key}) WHERE d.{key} IS NULL"
                    )
                    .iloc[0]
                    .n
                )
                == 0
            )
        qa = {k: bool(v) for k, v in qa.items()}
        assert all(qa.values())
        # Exports are aggregate only, suitable for Power BI without publishing customer IDs.
        export = ROOT / "docs/data/marketscope"
        export.mkdir(exist_ok=True)
        for name in ["monthly", "products", "rfm_segments", "cohorts"]:
            (export / (name + ".csv")).write_bytes(
                (FOLDER / (name + ".csv")).read_bytes()
            )
        result = {
            "source": "UCI Online Retail II; Chen (2012), DOI 10.24432/C5CG6D; CC BY 4.0",
            "sha256": hashlib.sha256((FOLDER / "retail.xlsx").read_bytes()).hexdigest(),
            "raw_rows": len(raw),
            "clean_rows": len(clean),
            "exclusion_counts": d.reason.value_counts().to_dict(),
            "date_start": min(clean.date_key),
            "date_end": max(clean.date_key),
            "currency": "GBP",
            "timezone": "Unspecified source local time; no invented UTC conversion",
            "missing_customer_raw": int(raw["Customer ID"].isna().sum()),
            "missing_customer_clean": int((clean.customer_key == "UNKNOWN").sum()),
            "raw_cancellation_lines": int(d.invoice.str.startswith("C").sum()),
            "raw_negative_quantity_lines": int((d.quantity < 0).sum()),
            "raw_missing_description": int(raw.Description.isna().sum()),
            "totals": totals,
            "top10_gross_share": float(
                products.iloc[:10].gross_micro.sum() / totals["gross_micro"]
            ),
            "sensitivity": {
                "including_exact_duplicates_net_micro": int(
                    classify(raw.drop_duplicates())
                    .query("reason=='accepted'")
                    .amount_micro.sum()
                )
                + int(
                    d.loc[
                        (d.reason == "exact duplicate")
                        & d.product_key.str.match(r"^\d{5}[A-Z]{0,2}$")
                        & (d.unit_micro > 0)
                        & ~(d.invoice.str.startswith("C") & (d.quantity >= 0)),
                        "amount_micro",
                    ].sum()
                ),
                "all_deduplicated_positive_price_transactions_net_micro": int(
                    d.loc[~d.duplicate & (d.unit_micro > 0), "amount_micro"].sum()
                ),
            },
            "monthly": monthly.to_dict("records"),
            "top_products": products.to_dict("records"),
            "rfm": rfm.to_dict("records"),
            "cohorts": cohorts.to_dict("records"),
            "qa": qa,
            "limitations": "Historical observed invoice lines, not current business performance. Merchandise-only curated definition; exact duplicates removed with sensitivity. Partial December 2011; no margins, advertising, inventory or forward CLV.",
        }
    (ROOT / "docs/data/marketscope.json").write_text(
        json.dumps(result, indent=2, allow_nan=False)
    )
    (ROOT / "evidence/marketscope-metrics.json").write_text(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ["monthly", "top_products", "rfm", "cohorts"]
            },
            indent=2,
        )
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ["monthly", "top_products", "rfm", "cohorts"]
            },
            indent=2,
        )
    )
    return result


if __name__ == "__main__":
    run()
