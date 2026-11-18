"""Seeded randomized experiment; all units and outcomes are synthetic."""

from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from scipy.stats import norm, chi2, fisher_exact

ROOT = Path(__file__).resolve().parents[3]
SEED = 20261117


def wilson(x, n, z=1.959963984540054):
    p = x / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0, center - half), min(1, center + half)


def proportions(xc, nc, xt, nt, seed=SEED, draws=10000):
    if (
        any(not isinstance(x, (int, np.integer)) for x in [xc, nc, xt, nt])
        or min(nc, nt) <= 0
        or xc < 0
        or xt < 0
        or xc > nc
        or xt > nt
    ):
        raise ValueError("Invalid counts or denominators")
    pc = xc / nc
    pt = xt / nt
    delta = pt - pc
    pooled = (xc + xt) / (nc + nt)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / nc + 1 / nt))
    z = delta / se_null if se_null else 0
    p = float(2 * norm.sf(abs(z))) if se_null else 1.0
    lc, uc = wilson(xc, nc)
    lt, ut = wilson(xt, nt)
    ci = [
        max(-1, delta - math.sqrt((pt - lt) ** 2 + (uc - pc) ** 2)),
        min(1, delta + math.sqrt((ut - pt) ** 2 + (pc - lc) ** 2)),
    ]
    rng = np.random.default_rng(seed)
    boot = rng.binomial(nt, pt, draws) / nt - rng.binomial(nc, pc, draws) / nc
    return {
        "control_n": int(nc),
        "treatment_n": int(nt),
        "control_events": int(xc),
        "treatment_events": int(xt),
        "control_rate": pc,
        "treatment_rate": pt,
        "absolute_lift": delta,
        "relative_lift": delta / pc if pc else None,
        "null_standard_error": se_null,
        "unpooled_standard_error": math.sqrt(pc * (1 - pc) / nc + pt * (1 - pt) / nt),
        "z": z,
        "p_value": p,
        "ci95_newcombe": ci,
        "bootstrap_ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
        "bootstrap_draws": draws,
        "fisher_two_sided": float(fisher_exact([[xt, nt - xt], [xc, nc - xc]]).pvalue),
        "normal_approximation_ok": min(xc, nc - xc, xt, nt - xt) >= 5,
    }


def srm(nc, nt, expected_treatment=0.5):
    if nc + nt <= 0 or min(nc, nt) < 0 or not 0 < expected_treatment < 1:
        raise ValueError("Invalid assignment counts")
    total = nc + nt
    et = total * expected_treatment
    ec = total - et
    stat = (nc - ec) ** 2 / ec + (nt - et) ** 2 / et
    return {
        "chi_square": stat,
        "p_value": float(chi2.sf(stat, 1)),
        "flag_at_001": bool(chi2.sf(stat, 1) < 0.001),
    }


def sample_size(baseline, mde, alpha=0.05, power=0.8):
    if (
        not 0 < baseline < 1
        or not 0 < mde < 1 - baseline
        or not 0 < alpha < 1
        or not 0.5 < power < 1
    ):
        raise ValueError("Invalid design assumptions")
    p1 = baseline
    p2 = baseline + mde
    pb = (p1 + p2) / 2
    return math.ceil(
        (
            norm.ppf(1 - alpha / 2) * math.sqrt(2 * pb * (1 - pb))
            + norm.ppf(power) * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        )
        ** 2
        / mde**2
    )


def mde_for_n(baseline, n):
    lo = 1e-7
    hi = (1 - baseline) * 0.999
    if sample_size(baseline, hi) > n:
        return None
    for _ in range(70):
        mid = (lo + hi) / 2
        if sample_size(baseline, mid) > n:
            lo = mid
        else:
            hi = mid
    return hi


def generate(n=20000, seed=SEED):
    rng = np.random.default_rng(seed)
    group = rng.integers(0, 2, n)
    p = 0.12 + 0.015 * group
    return pd.DataFrame(
        {
            "unit_id": [f"sim_{i:05}" for i in range(n)],
            "treatment": group,
            "converted": rng.binomial(1, p),
            "platform": rng.choice(["mobile", "desktop"], n),
            "exposed_at": pd.Timestamp("2026-10-01", tz="UTC")
            + pd.to_timedelta(rng.integers(0, 28 * 86400, n), unit="s"),
            "latency_ms": np.round(rng.lognormal(np.log(180), 0.3, n) + group * 15, 2),
        }
    )


def validate(d):
    if not set(
        ["unit_id", "treatment", "converted", "exposed_at", "latency_ms", "platform"]
    ).issubset(d.columns):
        raise ValueError("Missing fields")
    if d.isna().any().any() or d.unit_id.duplicated().any():
        raise ValueError("Missing or duplicate units")
    if not d.treatment.isin([0, 1]).all() or not d.converted.isin([0, 1]).all():
        raise ValueError("Invalid labels")
    if (d.latency_ms < 0).any() or not np.isfinite(d.latency_ms).all():
        raise ValueError("Invalid latency")
    times = pd.to_datetime(d.exposed_at, utc=True, errors="raise")
    if (times < pd.Timestamp("2026-10-01", tz="UTC")).any() or (
        times >= pd.Timestamp("2026-10-29", tz="UTC")
    ).any():
        raise ValueError("Exposure outside experiment")
    if set(d.treatment.unique()) != {0, 1}:
        raise ValueError("Both arms required")
    return True


def analyze(d):
    c = d[d.treatment == 0]
    t = d[d.treatment == 1]
    r = proportions(int(c.converted.sum()), len(c), int(t.converted.sum()), len(t))
    r["srm"] = srm(len(c), len(t))
    r["latency_mean_control"] = float(c.latency_ms.mean())
    r["latency_mean_treatment"] = float(t.latency_ms.mean())
    r["latency_delta_ms"] = r["latency_mean_treatment"] - r["latency_mean_control"]
    return r


def peeking(trials=1000):
    rng = np.random.default_rng(SEED + 1)
    tc = np.zeros(trials)
    tt = np.zeros(trials)
    any_sig = np.zeros(trials, dtype=bool)
    looks = []
    for n in range(500, 10001, 500):
        tc += rng.binomial(500, 0.12, trials)
        tt += rng.binomial(500, 0.12, trials)
        pc = tc / n
        pt = tt / n
        pool = (tc + tt) / (2 * n)
        se = np.sqrt(pool * (1 - pool) * 2 / n)
        p = 2 * norm.sf(np.abs((pt - pc) / se))
        any_sig |= p < 0.05
        looks.append(
            {"per_arm_n": n, "cumulative_false_positive_rate": float(any_sig.mean())}
        )
    return {
        "trials": trials,
        "looks": looks,
        "fixed_horizon_false_positive_rate": float((p < 0.05).mean()),
        "any_peek_false_positive_rate": float(any_sig.mean()),
        "truth": "No treatment effect in either arm; independent Bernoulli p=0.12",
    }


def run():
    d = generate()
    validate(d)
    folder = ROOT / "projects/experimentlab/data"
    folder.mkdir(exist_ok=True, parents=True)
    d.to_csv(folder / "synthetic-rct.csv", index=False)
    r = analyze(d)
    segments = {name: analyze(g) for name, g in d.groupby("platform")}
    result = {
        "label": "SYNTHETIC EXPERIMENT",
        "seed": SEED,
        "rows": len(d),
        "truth": {
            "control_conversion": 0.12,
            "treatment_conversion": 0.135,
            "absolute_effect": 0.015,
            "latency_added_ms": 15,
        },
        "overall": r,
        "segments_exploratory": segments,
        "quality": {
            "duplicate_units": 0,
            "missing_fields": 0,
            "assignment": "Independent Bernoulli 50/50 at unit level",
            "exposure_start": str(d.exposed_at.min()),
            "exposure_end": str(d.exposed_at.max()),
            "outliers_latency_above_1000ms": int((d.latency_ms > 1000).sum()),
            "exposure_semantics": "Each row is one assigned and exposed unit; simulated completed binary outcome; no observation censoring",
        },
        "design": {
            "alpha": 0.05,
            "power": 0.8,
            "baseline": 0.12,
            "absolute_mde": 0.015,
            "required_per_arm": sample_size(0.12, 0.015),
            "mde_at_10000_per_arm": mde_for_n(0.12, 10000),
        },
        "peeking": peeking(),
        "tiny_fixture": proportions(1, 4, 3, 4),
        "decision": "Do not ship under the declared guardrail: treatment increases mean simulated latency by more than 10 ms. Conversion significance alone is insufficient. Design a latency-reduced variant and a new fixed-horizon test.",
    }
    for dest in [
        ROOT / "docs/data/experimentlab.json",
        ROOT / "evidence/experimentlab-metrics.json",
    ]:
        dest.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(
        json.dumps(
            {k: result[k] for k in ["rows", "overall", "design", "decision"]}, indent=2
        )
    )
    return result


if __name__ == "__main__":
    run()
