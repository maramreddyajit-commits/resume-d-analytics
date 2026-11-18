# Synthetic experiment provenance

Generated locally on 2026-11-17; seed 20261117. No external experimental observations are used or redistributed. A public educational experiment with sufficiently documented licensing and instrumentation was not established for this build; use a controlled simulation instead. All 20,000 rows are explicitly labeled SYNTHETIC EXPERIMENT.

Generator: src/analysis.py generate. Each unique fictional unit is independently assigned with treatment probability 0.5, exposed once during October 1–28, 2026 UTC, and given a complete binary outcome. Control conversion probability is 0.12, treatment 0.135. Platform assignment is independent. Latency is lognormal with median 180 ms, log-scale SD 0.3; treatment adds 15 ms. No records excluded. No missing fields, duplicate units or negative latencies are allowed. IDs are generated, not real identities. Exposure times are illustrative simulated times; outcomes are complete, not real observation windows.

Regenerate: `python -m projects.experimentlab.src.analysis`. It saves data/synthetic-rct.csv (not committed) and public aggregate JSON. Bootstrap uses seed 20261117 and 10,000 independent resamples of each arm's empirical Bernoulli distribution. The peeking study uses seed 20261118 and 1,000 null trials, 20 looks, 500 added observations per arm per look. Truth is zero effect there; it is a separate simulation.
