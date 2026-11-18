import json
import numpy as np
import pytest
from projects.demandcast.src.forecast import forecast, score, scenario, ROOT


def test_seasonal_naive_exact_lags():
    y = np.arange(60.0)
    np.testing.assert_array_equal(forecast(y, "seasonal_naive"), [8, 9, 10, 11])


def test_moving_average_only_last_four():
    np.testing.assert_array_equal(
        forecast(np.arange(60.0), "moving_average"), [57.5] * 4
    )


def test_future_changes_not_used():
    full = np.arange(100.0)
    first = forecast(full[:60], "holt")
    full[60:] = 99999
    np.testing.assert_array_equal(first, forecast(full[:60], "holt"))


def test_hand_metrics():
    r = score([1, 3], [2, 1], scale=2)
    assert r["mae"] == 1.5
    assert r["rmse"] == pytest.approx(np.sqrt(2.5))
    assert r["wape"] == 0.75
    assert r["mase"] == 0.75


def test_undefined_denominators():
    r = score([0, 0], [1, 2], scale=0)
    assert r["wape"] is None and r["mase"] is None


@pytest.mark.parametrize(
    "values", [np.arange(20), np.repeat(-1.0, 60), np.repeat(np.nan, 60)]
)
def test_invalid_training(values):
    with pytest.raises(ValueError):
        forecast(values, "holt")


def test_scenario_hand_calculation():
    r = scenario(100, 0, 2, 0.95, 0.2)
    assert r["reorder_point"] == 200
    assert r["safety_stock"] == 0
    with pytest.raises(ValueError):
        scenario(100, 1, 0)


def test_chronology_and_selection():
    d = json.loads((ROOT / "docs/data/demandcast.json").read_text())
    assert max(d["origins"]["validation"]) + d["horizon"] <= min(d["origins"]["test"])
    for p in d["products"]:
        for r in p["test_predictions"]:
            assert r["train_end"] < r["week"]
            assert r["origin"] in d["origins"]["test"]


def test_nonnegative_forecast():
    assert (forecast(np.ones(60), "holt") >= 0).all()


def test_aggregation_zero_weeks_returns_and_selection_cutoff():
    import sqlite3
    from projects.demandcast.src.forecast import aggregate

    with sqlite3.connect(":memory:") as con:
        con.execute(
            "CREATE TABLE fact(product_key TEXT,date_key TEXT,quantity INTEGER)"
        )
        con.executemany(
            "INSERT INTO fact VALUES (?,?,?)",
            [(f"{i:05}", "2010-01-04", i + 1) for i in range(12)]
            + [
                ("99999", "2011-10-03", 999999),
                ("00001", "2010-01-05", -100),
                ("00001", "2011-12-09", 999999),
            ],
        )
        con.execute("CREATE VIEW sales AS SELECT * FROM fact WHERE quantity>0")
        d = aggregate(con)
        assert len(d) == 104
        assert "99999" not in d.columns
        assert d["00001"].sum() == 2
        assert d["00001"].iloc[0] == 0
