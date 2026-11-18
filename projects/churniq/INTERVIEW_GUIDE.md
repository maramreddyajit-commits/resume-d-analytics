# Explain ChurnIQ

The CSV is a table of fictional accounts. SQL-like grouping produces segment rates. A model turns permitted account attributes into a risk score. The dashboard separates that probability from a yes/no decision threshold and from assumed intervention value.

Learn five tradeoffs: cross-sectional vs chronological validation (timestamps absent); train-only imputation vs whole-data preprocessing; simple logistic vs nonlinear random forest; F1 threshold vs business-cost optimization; predicted risk vs causal uplift. The first is what the data permits, the last is what the data cannot answer.

Ten interview prompts and honest answers:
1. What is the dataset? IBM's fictional Telco sample, 7,043 records; not real customer activity.
2. What is the split? 4,225 train, 1,409 validation, 1,409 test, stratified and ID-disjoint.
3. How are missing values handled? Eleven blank TotalCharges values become NaN; medians learned from training data.
4. How is leakage reduced? Feature allowlist excludes IDs/target/demographics, preprocessing fits training only, selection uses validation only. Missing source timestamps remain a limitation.
5. Why random forest? It won validation AP among two fixed candidates; test results did not select it.
6. What is 0.858? Rounded test ROC-AUC, a ranking measure, not accuracy or achieved retention.
7. What is AP? Precision weighted by increments of recall at score thresholds; baseline is prevalence.
8. Why threshold 0.36? It maximized validation F1 on a prespecified grid. Test slider is exploration, not retuning.
9. What is the scenario? Assumed preventable fraction × summed risk × value minus outreach costs; not measured savings.
10. What next? Timestamped lawful data, later-cohort calibration, and a randomized intervention before business claims.

Three-minute demo: show sample label/counts (30 seconds); switch contract/tenure segments (45 seconds); explain validation/test model comparison (45 seconds); adjust threshold and budget while distinguishing observed outcomes from assumptions (45 seconds); finish with the main limitation (15 seconds).

Exercise: change only the scenario budget from 500 to 250; manually compute the maximum contacts at cost 10, then reproduce with src.pipeline.scenario. Never change the seed repeatedly to hunt for a better résumé score. Architecture code is src/pipeline.py; frontend controls are docs/churniq.js. Run the README commands to reproduce.
