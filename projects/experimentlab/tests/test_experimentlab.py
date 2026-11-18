import numpy as np
import pytest
from scipy.stats import chi2_contingency
from projects.experimentlab.src.analysis import (
    proportions,
    srm,
    sample_size,
    mde_for_n,
    generate,
    validate,
    peeking,
)


def test_tiny_fixture():
    r = proportions(1, 4, 3, 4)
    assert r["absolute_lift"] == 0.5
    assert r["relative_lift"] == 2
    assert r["fisher_two_sided"] == pytest.approx(0.48571428571428565)
    assert not r["normal_approximation_ok"]


def test_independent_chi_square_matches_z():
    r = proportions(100, 1000, 140, 1000)
    p = chi2_contingency([[100, 900], [140, 860]], correction=False).pvalue
    assert r["p_value"] == pytest.approx(p)


@pytest.mark.parametrize("x,n", [(0, 20), (20, 20)])
def test_edge_probabilities(x, n):
    r = proportions(x, n, x, n)
    assert r["p_value"] == 1
    assert np.isfinite(r["ci95_newcombe"]).all()
    assert r["absolute_lift"] == 0


@pytest.mark.parametrize(
    "args", [(1, 0, 2, 10), (11, 10, 1, 10), (-1, 10, 1, 10), (1.5, 10, 1, 10)]
)
def test_invalid_denominators(args):
    with pytest.raises(ValueError):
        proportions(*args)


def test_imbalanced_sizes():
    assert proportions(10, 100, 100, 1000)["p_value"] == 1


def test_bootstrap_reproducible():
    assert (
        proportions(12, 100, 19, 100)["bootstrap_ci95"]
        == proportions(12, 100, 19, 100)["bootstrap_ci95"]
    )


def test_srm_flags():
    assert srm(1000, 1500)["flag_at_001"]
    assert not srm(1000, 1000)["flag_at_001"]


def test_assignment_integrity():
    d = generate(20)
    validate(d)
    d.loc[0, "treatment"] = 2
    with pytest.raises(ValueError):
        validate(d)


def test_duplicates_rejected():
    d = generate(20)
    d.loc[1, "unit_id"] = d.loc[0, "unit_id"]
    with pytest.raises(ValueError):
        validate(d)


def test_power_monotonic_and_inverse():
    assert sample_size(0.12, 0.01) > sample_size(0.12, 0.02)
    m = mde_for_n(0.12, 10000)
    assert sample_size(0.12, m) <= 10000
    with pytest.raises(ValueError):
        sample_size(0.99, 0.1)


def test_peeking_not_fixed_horizon():
    r = peeking(100)
    assert r["any_peek_false_positive_rate"] >= r["fixed_horizon_false_positive_rate"]
