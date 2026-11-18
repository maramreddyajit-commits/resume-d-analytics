# Decision Atlas — Resume D analytics portfolio

Four executable analytics projects: customer churn, experiment inference, a retail SQL warehouse and time-series forecasting. Each includes a decision memo, reproducible metrics, tests and an interactive browser view. Built with AI coding assistance; no fabricated impact or company affiliation.

## Quick start

Tested with Python 3.14.7 on macOS; dependencies pinned. Python and Node tooling are not bundled.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
bash scripts/reproduce_all.sh
make demo
```

Open http://localhost:8780/. The committed dashboard results work immediately with `make demo`; raw data is required to rerun pipelines/tests. Full UCI workbook is ~44 MB; parsing and rebuilding the local SQLite warehouse needs several hundred MB of disk and may take a few minutes. No API credentials are required. Raw data/customer IDs and private résumé files are excluded from public Git.

| Project | Workflow and docs | Source class | Local command |
|---|---|---|---|
| ChurnIQ | [README](projects/churniq/README.md) | IBM fictional sample | `python -m projects.churniq.src.pipeline` |
| ExperimentLab | [README](projects/experimentlab/README.md) | Explicit synthetic randomized trial | `python -m projects.experimentlab.src.analysis` |
| MarketScope | [README](projects/marketscope/README.md) | Historical UCI transactions | `python -m projects.marketscope.src.warehouse` |
| DemandCast | [README](projects/demandcast/README.md) | Weekly observed UCI sales | `python -m projects.demandcast.src.forecast` |

`make test` runs all Python tests. `make qa` adds fatal-error lint checks. Browser QA scripts require optional Node/Playwright; instructions in scripts/browser/README.md. Public demo serves precomputed Python/SQL results with working filters, exports and scenario controls; it does not train models or run SQL remotely. This keeps the demo available without a database service or server credentials.

## Results and caveats

- ChurnIQ: 7,043 fictional accounts; validation-selected random forest on 1,409 test accounts, ROC-AUC 0.8580 / AP 0.6580. Cross-sectional, not chronological; no measured retention gains.
- ExperimentLab: 20,000 simulated units; observed difference +1.229 pp, p=0.00926; latency guardrail rejects rollout. Not a real product win.
- MarketScope: 1,067,371 historical raw lines → 1,021,127 accepted merchandise lines; £18,926,250.05 net under explicit cleaning rules. No inferred margins or stockouts.
- DemandCast: 12 SKUs, 104 weeks; moving-average baseline selected on validation; test WAPE 53.15%, MAE 311.98 over 144 predictions. Units sold, not unconstrained demand; inventory scenarios are assumptions.

[QA report](QA_REPORT.md) · [Status](PROJECT_STATUS.md) · [Provenance](DATA_PROVENANCE.md) · [Learning plan](learning/LEARN_THIS_NEXT.md). Per-project CASE_STUDY.md explains recommendations and uncertainty. Public data attribution/license links are in third-party/ATTRIBUTION.md.
