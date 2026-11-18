# ChurnIQ — retention decision engine

**Question:** Which fictional sample accounts merit investigation, and how would a limited outreach budget change a proposed policy?

From the repository root:
```sh
python scripts/download_telco.py
python -m projects.churniq.src.pipeline
python -m pytest projects/churniq/tests -q
python -m http.server 8780 --directory docs
```
Open http://localhost:8780/#churniq. Filters, threshold exploration, budget assumptions and CSV download work in the browser. Public hosting serves precomputed results; preprocessing and training run in Python. No live customer system is connected.

[Data provenance](DATA_PROVENANCE.md) · [Case study](CASE_STUDY.md) · [Metrics](METRICS.md)

Architecture: immutable source CSV → schema/ID/target validation → numeric cleaning → stratified train/validation/test split → training-only ColumnTransformer → majority/logistic/random-forest comparison → validation-only model/threshold selection → test predictions and independent arithmetic → browser dashboard. Core source: src/pipeline.py. Local data artifacts include processed.csv, split IDs and predictions.csv; they are not committed.

All demographic exclusions, limitations and assumed scenario parameters are visible. Synthetic/sample performance is not evidence of reduced churn. Built with AI coding assistance; learning exercises accompany the implementation.
