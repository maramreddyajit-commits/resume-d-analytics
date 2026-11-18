"""Weekly observed-sales forecasts with fixed expanding-window validation/test origins."""

from pathlib import Path
import sqlite3, json, math
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[3]
FOLDER = ROOT / "projects/demandcast/data"
HORIZON = 4


def aggregate(con):
    d = pd.read_sql_query(
        "SELECT product_key,date_key,SUM(quantity) units FROM sales GROUP BY product_key,date_key",
        con,
    )
    d["week"] = (
        pd.to_datetime(d.date_key).dt.to_period("W-SUN").dt.end_time.dt.normalize()
    )
    # Discard incomplete first and last calendar weeks of the source.
    d = d[
        (d.week >= pd.Timestamp("2009-12-13")) & (d.week <= pd.Timestamp("2011-12-04"))
    ]
    weeks = pd.date_range("2009-12-13", "2011-12-04", freq="W-SUN")
    pivot = d.pivot_table(
        index="week", columns="product_key", values="units", aggfunc="sum", fill_value=0
    ).reindex(weeks, fill_value=0)
    # Select SKUs using initial training period only, before any validation/test observations.
    selected = (
        pivot.iloc[:52]
        .sum()
        .sort_values(ascending=False, kind="stable")
        .head(12)
        .index.tolist()
    )
    return pivot[selected].astype(float)


def holt(train, h):
    y = np.asarray(train, float)

    def smooth(params, forecast=False):
        alpha, beta = params
        level = y[0]
        trend = 0.0
        errors = []
        for actual in y[1:]:
            guess = level + trend
            errors.append(actual - guess)
            new = alpha * actual + (1 - alpha) * guess
            trend = beta * (new - level) + (1 - beta) * trend
            level = new
        return (
            np.maximum(0, level + np.arange(1, h + 1) * trend)
            if forecast
            else np.mean(np.square(errors))
        )

    fit = minimize(
        smooth, [0.2, 0.05], method="L-BFGS-B", bounds=[(0.001, 0.999), (0.001, 0.999)]
    )
    if not fit.success or not np.isfinite(fit.x).all():
        raise RuntimeError("Holt optimization failed")
    return smooth(fit.x, True)


def forecast(train, name, h=HORIZON):
    y = np.asarray(train, float)
    if len(y) < 53 or not np.isfinite(y).all() or (y < 0).any():
        raise ValueError("Need 53+ nonnegative finite training observations")
    if name == "seasonal_naive":
        return np.array([y[-52 + i] for i in range(h)])
    if name == "moving_average":
        return np.repeat(y[-4:].mean(), h)
    if name == "holt":
        return holt(y, h)
    raise ValueError("Unknown model")


def score(actual, pred, scale=None):
    a = np.asarray(actual, float)
    p = np.asarray(pred, float)
    if (
        a.shape != p.shape
        or not len(a)
        or not np.isfinite(a).all()
        or not np.isfinite(p).all()
    ):
        raise ValueError("Invalid evaluation arrays")
    e = np.abs(a - p)
    return {
        "mae": float(e.mean()),
        "rmse": float(np.sqrt(np.mean((a - p) ** 2))),
        "wape": float(e.sum() / np.abs(a).sum()) if np.abs(a).sum() > 0 else None,
        "mase": float(e.mean() / scale) if scale is not None and scale > 0 else None,
        "n": len(a),
        "absolute_error_sum": float(e.sum()),
        "actual_sum": float(a.sum()),
    }


def scenario(mean, weekly_sigma, lead_weeks=2, service=0.95, holding=0.2):
    from scipy.stats import norm

    if (
        mean < 0
        or weekly_sigma < 0
        or lead_weeks <= 0
        or not 0.5 < service < 1
        or holding < 0
    ):
        raise ValueError("Invalid inventory assumptions")
    safety = float(norm.ppf(service) * weekly_sigma * np.sqrt(lead_weeks))
    reorder = float(mean * lead_weeks + safety)
    return {
        "safety_stock": safety,
        "reorder_point": reorder,
        "modeled_weekly_holding_cost": safety * holding,
    }


def run():
    FOLDER.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(ROOT / "projects/marketscope/data/warehouse.sqlite") as con:
        series = aggregate(con)
        names = dict(
            con.execute("SELECT product_key,description FROM dim_product").fetchall()
        )
    series.to_csv(FOLDER / "weekly_units.csv")
    records = []
    origins = {"validation": [60, 68, 76], "test": [88, 92, 96]}
    models = ["seasonal_naive", "moving_average", "holt"]
    assert origins["validation"][-1] + HORIZON <= origins["test"][0]
    for split, starts in origins.items():
        for origin in starts:
            for sku in series.columns:
                train = series[sku].iloc[:origin].to_numpy()
                actual = series[sku].iloc[origin : origin + HORIZON].to_numpy()
                scale = float(np.abs(train[52:] - train[:-52]).mean())
                for name in models:
                    pred = forecast(train, name)
                    for h, (a, p) in enumerate(zip(actual, pred), 1):
                        records.append(
                            {
                                "split": split,
                                "origin": origin,
                                "train_end": str(series.index[origin - 1].date()),
                                "week": str(series.index[origin + h - 1].date()),
                                "sku": sku,
                                "model": name,
                                "horizon": h,
                                "actual": float(a),
                                "prediction": float(p),
                                "scale": scale,
                            }
                        )
    df = pd.DataFrame(records)
    df.to_csv(FOLDER / "backtest_predictions.csv", index=False)

    def report(group):
        result = score(group.actual, group.prediction)
        scales = group.scale.to_numpy()
        mask = scales > 0
        result["mase"] = (
            float(
                np.mean(
                    np.abs(
                        group.actual.to_numpy()[mask]
                        - group.prediction.to_numpy()[mask]
                    )
                    / scales[mask]
                )
            )
            if mask.any()
            else None
        )
        result["mase_defined_n"] = int(mask.sum())
        return result

    validation = {
        n: report(df[(df.split == "validation") & (df.model == n)]) for n in models
    }
    baseline = min(models[:2], key=lambda n: validation[n]["wape"])
    chosen = (
        "holt"
        if validation["holt"]["wape"] < validation[baseline]["wape"] * 0.95
        else baseline
    )
    test = {n: report(df[(df.split == "test") & (df.model == n)]) for n in models}
    v = df[(df.split == "validation") & (df.model == chosen)]
    t = df[(df.split == "test") & (df.model == chosen)]
    residual = np.abs(v.actual - v.prediction).to_numpy()
    radius = float(np.quantile(residual, 0.9, method="higher"))
    coverage = float(
        (
            (t.actual >= np.maximum(0, t.prediction - radius))
            & (t.actual <= t.prediction + radius)
        ).mean()
    )
    products = []
    future = []
    for sku in series.columns:
        y = series[sku].to_numpy()
        rows = t[t.sku == sku]
        forecast_values = forecast(y, chosen)
        rmse = float(
            np.sqrt(
                np.mean(
                    (v.loc[v.sku == sku, "actual"] - v.loc[v.sku == sku, "prediction"])
                    ** 2
                )
            )
        )
        item = {
            "sku": sku,
            "name": names.get(sku, sku),
            "weekly_units": y.tolist(),
            "test_metrics": report(rows),
            "test_predictions": rows.to_dict("records"),
            "forecast": forecast_values.tolist(),
            "validation_rmse": rmse,
            "scenario": scenario(float(forecast_values.mean()), rmse),
            "zero_weeks": int((y == 0).sum()),
        }
        products.append(item)
        for h, p in enumerate(forecast_values, 1):
            future.append(
                {
                    "sku": sku,
                    "week": str((series.index[-1] + pd.Timedelta(weeks=h)).date()),
                    "forecast": float(p),
                    "lower": max(0, float(p) - radius),
                    "upper": float(p) + radius,
                    "model": chosen,
                }
            )
    # Independent arithmetic via Python scalar accumulation (not score()).
    independent = {
        "mae": sum(abs(r.actual - r.prediction) for r in t.itertuples()) / len(t),
        "rmse": math.sqrt(
            sum((r.actual - r.prediction) ** 2 for r in t.itertuples()) / len(t)
        ),
        "wape": sum(abs(r.actual - r.prediction) for r in t.itertuples())
        / sum(r.actual for r in t.itertuples()),
    }
    for k, val in independent.items():
        assert abs(val - test[chosen][k]) < 1e-10
    pd.DataFrame(future).to_csv(
        ROOT / "docs/data/demandcast-forecasts.csv", index=False
    )
    result = {
        "source": "Derived from curated UCI Online Retail II positive merchandise quantities; CC BY 4.0",
        "sku_count": len(products),
        "weeks": len(series),
        "week_start": str(series.index[0].date()),
        "week_end": str(series.index[-1].date()),
        "selection": "Top 12 units sold in first 52 complete weeks only; fixed before validation",
        "origins": origins,
        "horizon": HORIZON,
        "chosen_model": chosen,
        "selection_rule": "Best validation WAPE baseline; Holt requires at least 5% relative validation WAPE improvement over that baseline",
        "validation": validation,
        "test": test,
        "independent": independent,
        "uncertainty": {
            "absolute_radius_units": radius,
            "nominal_level": 0.9,
            "test_coverage": coverage,
            "method": "Pooled validation absolute-residual 90th percentile; heuristic, no calibrated coverage guarantee across heterogeneous SKUs",
        },
        "by_horizon": {str(h): report(g) for h, g in t.groupby("horizon")},
        "products": products,
        "forecast_rows": future,
        "limitations": "Units sold are constrained by unknown stock and demand. Missing sale weeks are zero observed sales, not confirmed in-stock zero demand. Returns excluded. No inventory, costs or lead times observed. Scenarios use assumptions; no actual savings or stockouts measured.",
    }
    (ROOT / "docs/data/demandcast.json").write_text(
        json.dumps(result, indent=2, allow_nan=False)
    )
    (ROOT / "evidence/demandcast-metrics.json").write_text(
        json.dumps(
            {k: v for k, v in result.items() if k not in ["products", "forecast_rows"]},
            indent=2,
        )
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ["products", "forecast_rows"]},
            indent=2,
        )
    )
    return result


if __name__ == "__main__":
    run()
