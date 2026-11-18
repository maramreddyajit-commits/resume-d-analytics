# Data provenance

Publisher: IBM, https://github.com/IBM/telco-customer-churn-on-icp4d . Immutable revision d5371f5d83a446ad5673cbcca3b814b926491f8a. Accessed 2026-11-17. Repository Apache-2.0 license inspected; acquisition saves its exact text alongside raw data. Raw CSV is excluded from Git; public demo contains derived aggregate statistics and score/target pairs with no original IDs. No claim of separate real-customer data permission is needed: these are fictional sample-company records, not live telecom customers. No reliable calendar/time span is provided.

Source URL: https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/d5371f5d83a446ad5673cbcca3b814b926491f8a/data/Telco-Customer-Churn.csv

SHA256: 16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91.
Raw and cleaned rows: 7,043; excluded: 0. Unique customer IDs required; duplicate IDs rejected. Eleven blank TotalCharges values become missing, not zero. Those records have zero tenure. Median imputation is fitted only on training records. Source target Yes/No is validated and mapped to 1/0. No oversampling is performed; original class proportions are preserved by stratification.

Schema: customerID is fictional identity (excluded from modeling); tenure is months; MonthlyCharges and TotalCharges are source charge amounts (no operational currency guarantee); contract/payment/service fields are categorical; Churn is the source binary outcome. gender and SeniorCitizen are aggregate audit-only fields. Partner/Dependents are excluded. See src/pipeline.py NUM/CAT for the exact feature allowlist and generated missingness report.

Regenerate: `python scripts/download_telco.py`, then `python -m projects.churniq.src.pipeline`. Seed 20261117; deterministic 60/20/20 stratified cross-sectional split. Source lacks feature/outcome collection timestamps, so even an ID-disjoint holdout cannot prove deployment-time availability or temporal generalization. TotalCharges is cumulative and correlated with tenure; post-outcome availability cannot be established. No original IDs are exposed in the public demo.
