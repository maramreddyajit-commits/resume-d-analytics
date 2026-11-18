"""Leakage-aware cross-sectional benchmark on IBM fictional Telco sample."""

from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
)

SEED = 20261117
ROOT = Path(__file__).resolve().parents[3]
NUM = ["tenure", "MonthlyCharges", "TotalCharges"]
CAT = [
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]
FEATURES = NUM + CAT


def clean(raw):
    d = raw.copy()
    if not set(FEATURES + ["customerID", "Churn", "gender", "SeniorCitizen"]).issubset(
        d.columns
    ):
        raise ValueError("Missing required columns")
    if d.customerID.isna().any() or d.customerID.duplicated().any():
        raise ValueError("Invalid or duplicate customer ID")
    if not d.Churn.isin(["Yes", "No"]).all():
        raise ValueError("Invalid target")
    for c in NUM:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    if (d[NUM] < 0).any().any():
        raise ValueError("Negative measurements")
    d["target"] = (d.Churn == "Yes").astype(int)
    return d


def split(d):
    tr, rest = train_test_split(
        np.arange(len(d)), test_size=0.4, stratify=d.target, random_state=SEED
    )
    va, te = train_test_split(
        rest, test_size=0.5, stratify=d.target.iloc[rest], random_state=SEED
    )
    return tr, va, te


def pipeline(model):
    num = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    cat = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return Pipeline(
        [
            ("prepare", ColumnTransformer([("num", num, NUM), ("cat", cat, CAT)])),
            ("model", model),
        ]
    )


def threshold_metrics(y, p, t):
    y = np.asarray(y, dtype=int)
    pred = np.asarray(p) >= t
    tp = int(((y == 1) & pred).sum())
    fp = int(((y == 0) & pred).sum())
    fn = int(((y == 1) & ~pred).sum())
    tn = int(((y == 0) & ~pred).sum())
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {
        "threshold": float(t),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall)
        if precision + recall
        else 0,
        "selected": tp + fp,
    }


def metrics(y, p, t):
    bins = []
    p = np.asarray(p)
    y = np.asarray(y)
    for lo, hi in zip(np.arange(0, 1, 0.1), np.arange(0.1, 1.1, 0.1)):
        mask = (p >= lo) & ((p < hi) if hi < 0.999 else (p <= 1))
        if mask.any():
            bins.append(
                {
                    "count": int(mask.sum()),
                    "predicted": float(p[mask].mean()),
                    "observed": float(y[mask].mean()),
                }
            )
    return {
        **threshold_metrics(y, p, t),
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "prevalence": float(y.mean()),
        "calibration": bins,
        "ece": float(
            sum(b["count"] * abs(b["predicted"] - b["observed"]) for b in bins) / len(y)
        ),
    }


def independent(y, p, t):
    """Pairwise tie-aware ROC, grouped-threshold AP, manual squared error."""
    y = np.asarray(y)
    p = np.asarray(p)
    pos = p[y == 1]
    neg = p[y == 0]
    auc = float(
        ((pos[:, None] > neg).sum() + 0.5 * (pos[:, None] == neg).sum())
        / (len(pos) * len(neg))
    )
    ap = 0
    previous = 0
    for score in sorted(set(p), reverse=True):
        keep = p >= score
        tp = int(y[keep].sum())
        ap += (tp - previous) / sum(y) * (tp / sum(keep))
        previous = tp
    return {
        "roc_auc": auc,
        "average_precision": float(ap),
        "brier": float(np.mean((p - y) ** 2)),
        **threshold_metrics(y, p, t),
    }


def scenario(probabilities, threshold, budget=500, cost=10, effect=0.1, value=300):
    if min(budget, cost, effect, value) < 0 or cost == 0 or effect > 1:
        raise ValueError("Invalid scenario")
    selected = sorted(
        [float(p) for p in probabilities if p >= threshold], reverse=True
    )[: int(budget // cost)]
    return {
        "contacts": len(selected),
        "spend": len(selected) * cost,
        "assumed_prevented_churn": sum(selected) * effect,
        "modeled_net_value": sum(selected) * effect * value - len(selected) * cost,
    }


def run():
    folder = ROOT / "projects/churniq/data"
    raw_path = folder / "raw.csv"
    raw = pd.read_csv(raw_path)
    d = clean(raw)
    tr, va, te = split(d)
    folder.mkdir(parents=True, exist_ok=True)
    d.to_csv(folder / "processed.csv", index=False)
    for name, ix in [("train", tr), ("validation", va), ("test", te)]:
        d.iloc[ix][["customerID", "target"]].to_csv(
            folder / (name + "_ids.csv"), index=False
        )
    models = {
        "logistic": pipeline(LogisticRegression(max_iter=2000, C=1, random_state=SEED)),
        "random_forest": pipeline(
            RandomForestClassifier(
                n_estimators=240,
                max_depth=8,
                min_samples_leaf=12,
                max_features="sqrt",
                random_state=SEED,
                n_jobs=1,
            )
        ),
    }
    val = {}
    test = {}
    preds = {}
    thresholds = {}
    base = np.full(len(va), d.target.iloc[tr].mean())
    val["majority"] = metrics(d.target.iloc[va], base, 0.5)
    for name, model in models.items():
        model.fit(d.iloc[tr][FEATURES], d.target.iloc[tr])
        p = model.predict_proba(d.iloc[va][FEATURES])[:, 1]
        candidates = [
            threshold_metrics(d.target.iloc[va], p, t)
            for t in np.arange(0.05, 0.951, 0.01)
        ]
        best = max(candidates, key=lambda x: (x["f1"], x["threshold"]))
        thresholds[name] = best["threshold"]
        val[name] = metrics(d.target.iloc[va], p, best["threshold"])
    # Freeze model choice from validation AP. Test performance does not choose anything.
    chosen = max(models, key=lambda n: val[n]["average_precision"])
    threshold = thresholds[chosen]
    for name, model in models.items():
        p = model.predict_proba(d.iloc[te][FEATURES])[:, 1]
        preds[name] = p
        test[name] = metrics(d.target.iloc[te], p, thresholds[name])
    test["majority"] = metrics(
        d.target.iloc[te], np.full(len(te), d.target.iloc[tr].mean()), 0.5
    )
    check = independent(d.target.iloc[te], preds[chosen], threshold)
    for key in ["roc_auc", "average_precision", "brier"]:
        assert abs(check[key] - test[chosen][key]) < 1e-12
    rows = d.iloc[te][
        [
            "customerID",
            "gender",
            "SeniorCitizen",
            "Contract",
            "tenure",
            "MonthlyCharges",
            "target",
        ]
    ].copy()
    rows["probability"] = preds[chosen]
    rows.to_csv(folder / "predictions.csv", index=False)
    # Public scores omit source IDs and demographics; demographics only in aggregate audit.
    public = rows[
        ["Contract", "tenure", "MonthlyCharges", "target", "probability"]
    ].to_dict("records")
    segments = {}
    for col in [
        "Contract",
        "PaymentMethod",
        "InternetService",
        "PaperlessBilling",
        "TechSupport",
    ]:
        segments[col] = [
            {
                "name": str(k),
                "count": len(g),
                "churned": int(g.target.sum()),
                "rate": float(g.target.mean()),
            }
            for k, g in d.groupby(col)
        ]
    for label, values in [
        (
            "Tenure",
            pd.cut(
                d.tenure,
                [-1, 12, 24, 48, 100],
                labels=["0–12", "13–24", "25–48", "49+"],
            ),
        ),
        (
            "Monthly charge",
            pd.cut(d.MonthlyCharges, [0, 35, 70, 200], labels=["≤35", "35–70", ">70"]),
        ),
    ]:
        segments[label] = [
            {
                "name": str(k),
                "count": len(g),
                "churned": int(g.target.sum()),
                "rate": float(g.target.mean()),
            }
            for k, g in d.groupby(values, observed=True)
        ]
    subgroup = {}
    for col in ["gender", "SeniorCitizen"]:
        subgroup[col] = [
            {
                "group": str(k),
                "n": len(g),
                **metrics(g.target, g.probability, threshold),
            }
            for k, g in rows.groupby(col)
        ]
    logistic = models["logistic"]
    names = logistic.named_steps["prepare"].get_feature_names_out()
    coef = logistic.named_steps["model"].coef_[0]
    explain = sorted(
        [{"feature": str(n), "coefficient": float(v)} for n, v in zip(names, coef)],
        key=lambda r: abs(r["coefficient"]),
        reverse=True,
    )[:15]
    report = {
        "seed": SEED,
        "rows": len(d),
        "excluded": 0,
        "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "missing": d[FEATURES].isna().sum().to_dict(),
        "target_counts": d.target.value_counts().to_dict(),
        "splits": {"train": len(tr), "validation": len(va), "test": len(te)},
        "split_overlap": 0,
        "chosen_model": chosen,
        "threshold": threshold,
        "selection": "Highest validation average precision; threshold maximizes validation F1 on fixed 0.01 grid; test untouched until frozen",
        "validation": val,
        "test": test,
        "independent": check,
        "segments": segments,
        "subgroups": subgroup,
        "logistic_coefficients": explain,
        "scenario": scenario(preds[chosen], threshold),
        "test_rows": public,
        "limitations": "IBM fictional sample; cross-sectional split, no event timestamps. Associations are not causes. Scenario effect and value are assumptions, not measured retention or savings.",
    }
    out = ROOT / "docs/data/churniq.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False))
    (ROOT / "evidence/churniq-metrics.json").write_text(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k
                not in ["test_rows", "segments", "subgroups", "logistic_coefficients"]
            },
            indent=2,
        )
    )
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "rows",
                    "splits",
                    "chosen_model",
                    "threshold",
                    "test",
                    "independent",
                ]
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    run()
