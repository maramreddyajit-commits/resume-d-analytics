import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from projects.churniq.src.pipeline import (
    clean,
    split,
    pipeline,
    FEATURES,
    NUM,
    threshold_metrics,
    independent,
    scenario,
    ROOT,
)


def sample():
    return clean(pd.read_csv(ROOT / "projects/churniq/data/raw.csv"))


def test_duplicate_ids_rejected():
    d = pd.read_csv(ROOT / "projects/churniq/data/raw.csv").iloc[:2].copy()
    d.loc[1, "customerID"] = d.loc[0, "customerID"]
    with pytest.raises(ValueError):
        clean(d)


def test_invalid_target_rejected():
    d = pd.read_csv(ROOT / "projects/churniq/data/raw.csv").iloc[:2].copy()
    d.loc[0, "Churn"] = "maybe"
    with pytest.raises(ValueError):
        clean(d)


def test_blank_charges_not_zero():
    d = sample()
    assert d.TotalCharges.isna().sum() == 11
    assert (d.loc[d.TotalCharges.isna(), "tenure"] == 0).all()


def test_disjoint_stratified_split():
    d = sample()
    tr, va, te = split(d)
    assert len(set(tr) | set(va) | set(te)) == len(d)
    assert not set(tr) & set(te)
    assert not set(tr) & set(va)
    assert not set(va) & set(te)
    for ix in [tr, va, te]:
        assert abs(d.target.iloc[ix].mean() - d.target.mean()) < 0.002


def test_target_id_demographics_not_features():
    assert not set(
        [
            "customerID",
            "Churn",
            "target",
            "gender",
            "SeniorCitizen",
            "Partner",
            "Dependents",
        ]
    ) & set(FEATURES)


def test_training_only_imputation_and_unknown_categories():
    d = sample()
    tr, va, _ = split(d)
    m = pipeline(LogisticRegression(max_iter=2000))
    m.fit(d.iloc[tr][FEATURES], d.target.iloc[tr])
    stats = (
        m.named_steps["prepare"]
        .named_transformers_["num"]
        .named_steps["impute"]
        .statistics_.copy()
    )
    np.testing.assert_allclose(stats, d.iloc[tr][NUM].median())
    x = d.iloc[va[:2]][FEATURES].copy()
    x["TotalCharges"] = np.nan
    x["PaymentMethod"] = "unseen method"
    p = m.predict_proba(x)
    assert np.isfinite(p).all()
    np.testing.assert_array_equal(
        stats,
        m.named_steps["prepare"]
        .named_transformers_["num"]
        .named_steps["impute"]
        .statistics_,
    )


@pytest.mark.parametrize(
    "y,p",
    [
        ([0, 1], [0.1, 0.9]),
        ([0, 1, 1, 0], [0.5] * 4),
        ([1, 0, 1, 0, 0], [0.2, 0.8, 0.9, 0.3, 0.3]),
    ],
)
def test_independent_metric_parity(y, p):
    a = independent(y, p, 0.5)
    assert a["roc_auc"] == pytest.approx(roc_auc_score(y, p))
    assert a["average_precision"] == pytest.approx(average_precision_score(y, p))


def test_threshold_exact_boundary():
    m = threshold_metrics([1, 0, 1, 0], [0.5, 0.5, 0.1, 0.1], 0.5)
    assert [m[x] for x in ["tp", "fp", "fn", "tn"]] == [1, 1, 1, 1]


def test_no_positive_predictions():
    assert threshold_metrics([1, 0], [0.1, 0.2], 0.9)["precision"] == 0


def test_budget_ranking_and_arithmetic():
    m = scenario([0.9, 0.8, 0.7], 0.5, budget=25, cost=10, effect=0.1, value=300)
    assert m["contacts"] == 2
    assert m["modeled_net_value"] == pytest.approx(31)


def test_invalid_scenario():
    with pytest.raises(ValueError):
        scenario([0.5], 0.2, cost=0)
