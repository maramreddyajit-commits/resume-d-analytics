# ExperimentLab — product experiment decisions

A complete synthetic randomized trial analysis with assignment QA, two-proportion inference, score-based confidence intervals, bootstrap verification, power/MDE planning and a latency guardrail.

```sh
python -m projects.experimentlab.src.analysis
python -m pytest projects/experimentlab/tests -q
python -m http.server 8780 --directory docs
```
Open http://localhost:8780/#experimentlab. Change population, baseline, MDE and available sample size; download the analysis. Public demo is precomputed inference plus browser design calculators; it does not execute arbitrary statistical uploads.

[Data provenance](DATA_PROVENANCE.md) · [Case study](CASE_STUDY.md) · [Interview guide](INTERVIEW_GUIDE.md). Exact metrics: ../../evidence/experimentlab-metrics.json.

Architecture: seeded assignment/outcome generator → uniqueness/label/exposure checks → pooled two-proportion z test, Newcombe/Wilson CI, empirical binomial bootstrap, Fisher exact cross-check → SRM and guardrail → dashboard. Zero-event cases return finite intervals and undefined relative lift as null. The normal approximation is flagged when expected-quality cell counts are small. Peeking simulation is separate from the primary trial. No real users participated.
