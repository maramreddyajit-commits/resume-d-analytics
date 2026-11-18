# A 60-minute learning and demonstration plan

0–10 minutes: run `make demo` and read every provenance banner. Explain the difference between historical observations (UCI), a fictional educational sample (IBM), and a generated randomized simulation (ExperimentLab). None establishes actual business impact.

10–25: open ChurnIQ. Explain 7,043 rows → 4,225/1,409/1,409 split, training-only preprocessing, validation selection and unseen test evaluation. ROC-AUC 0.858 is ranking quality, not accuracy. Change the scenario budget and say which quantities are assumed.

25–35: open ExperimentLab. Compute 1,232/10,113 vs 1,326/9,887 and explain the 1.229 percentage-point difference. Read the uncertainty interval and why a latency guardrail rejects rollout despite a small p-value. Change the MDE and observe sample-size needs.

35–45: open MarketScope. Explain invoice-line grain, missing customer IDs, gross/returns/net, and why £18.926M historical net is not earned revenue by you. Change country/month and inspect a product. No margins or inventory exist in this source.

45–55: open DemandCast. Explain why choosing SKUs and models using future outcomes would leak information. Trace an origin's training-end date and four later predictions. Explain WAPE 53.15% honestly; the moving average beats the tested seasonal baseline but still has large errors.

55–60: give a three-minute demo of one project, then state its most important limitation without prompting. Use the per-project exercise to prove you can calculate a small result manually.

## Architecture in plain language

CSV/Excel/generator → validation → Python/SQL transformations → model/statistics → JSON/CSV evidence → static HTML/JavaScript dashboard. The public dashboard does not run Python. A random seed makes repeated draws consistent, not realistic. A test protects a specific behavior, not every possible failure.

Detailed guides, each with ten technical prompts, five tradeoffs, a demo script and an exercise:
- [ChurnIQ](../projects/churniq/INTERVIEW_GUIDE.md)
- [ExperimentLab](../projects/experimentlab/INTERVIEW_GUIDE.md)
- [MarketScope](../projects/marketscope/INTERVIEW_GUIDE.md)
- [DemandCast](../projects/demandcast/INTERVIEW_GUIDE.md)

Do not claim unaided authorship. Explain AI coding assistance honestly and demonstrate that you understand and can modify the implementation. Preserve the fixed validation/test protocol when experimenting; use a new held-out dataset for genuinely new model selection.
