import pandas as pd
import pytest
import sqlite3, json
from projects.marketscope.src.warehouse import classify, ROOT, FOLDER


def toy():
    return pd.DataFrame(
        [
            ["100001", "12345", "Widget", 2, "2010-01-01", 1.25, 1, "UK"],
            ["C100002", "12345", "Widget", -1, "2010-01-02", 1.25, 1, "UK"],
            ["100003", "POST", "Postage", 1, "2010-01-02", 3, None, "UK"],
        ],
        columns=[
            "Invoice",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "Price",
            "Customer ID",
            "Country",
        ],
    )


def test_sales_returns_grain():
    d = classify(toy())
    c = d[d.reason == "accepted"]
    assert len(c) == 2
    assert c.amount_micro.sum() == 1250000


def test_duplicate_removed():
    d = classify(pd.concat([toy(), toy().iloc[:1]], ignore_index=True))
    assert (d.reason == "exact duplicate").sum() == 1


def test_unknown_customer_retained():
    d = toy()
    d.loc[0, "Customer ID"] = None
    assert classify(d).loc[0, "customer_key"] == "UNKNOWN"
    assert classify(d).loc[0, "reason"] == "accepted"


@pytest.mark.parametrize(
    "column,value,reason",
    [
        ("Price", 0, "invalid/zero price"),
        ("Quantity", 0, "invalid quantity"),
        ("Quantity", 0.5, "invalid quantity"),
        ("InvoiceDate", "bad", "invalid date"),
        ("Invoice", "C100001", "inconsistent cancellation"),
    ],
)
def test_bad_lines(column, value, reason):
    d = toy()
    d[column] = d[column].astype(object)
    d.loc[0, column] = value
    assert classify(d).loc[0, "reason"] == reason


def test_executed_sql_qa():
    d = json.loads((ROOT / "docs/data/marketscope.json").read_text())
    assert all(d["qa"].values())
    assert d["raw_rows"] == sum(d["exclusion_counts"].values())
    assert d["clean_rows"] == d["totals"]["lines"]


def test_money_exact_with_fractional_price():
    d = toy()
    d.loc[0, "Price"] = 0.001
    assert classify(d).loc[0, "amount_micro"] == 2000


def test_customer_and_cohort_bounds():
    with sqlite3.connect(FOLDER / "warehouse.sqlite") as con:
        assert (
            con.execute(
                "SELECT COUNT(*) FROM cohort_retention WHERE rate<0 OR rate>1 OR age_month<0"
            ).fetchone()[0]
            == 0
        )
        assert (
            con.execute(
                "SELECT COUNT(*) FROM customer_rfm WHERE recency_days<0 OR frequency<1"
            ).fetchone()[0]
            == 0
        )
