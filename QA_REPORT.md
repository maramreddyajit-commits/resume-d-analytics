# Execution and QA report — November 17, 2026

## Environment and setup

Python 3.14.7, macOS arm64. Exact analytical dependencies in requirements.lock.txt; run-manifest.json records versions and metric checksums. Official IBM CSV/license and UCI workbook downloaded through committed scripts. Raw inputs remain local. A clean virtual-environment installation is recorded in evidence/fresh-install.txt. No API key is required.

## Executed commands

From repository root, using the audited virtual environment's Python:

```
python scripts/download_telco.py
python -m projects.churniq.src.pipeline
python -m pytest projects/churniq/tests -q
python -m projects.experimentlab.src.analysis
python -m pytest projects/experimentlab/tests -q
python scripts/download_retail.py
python -m projects.marketscope.src.warehouse
python -m pytest projects/marketscope/tests -q
python -m projects.demandcast.src.forecast
python -m pytest projects/demandcast/tests -q
python -m pytest projects -q --junitxml=evidence/tests.xml
python -m ruff check projects scripts --select E9,F63,F7,F82
python -m ruff format projects scripts
python -m pip check
```

Every project's analysis was run a second time and its docs/data JSON compared byte-for-byte using `cmp`; all matched. MarketScope's second run used the checksum-keyed local workbook cache, then rebuilt and reconciled the SQLite warehouse. Delete raw.pkl to force source Excel parsing. Copies of output and test logs are in evidence/. Formatting does not change analytical results.

## Results

| Project | Automated Python tests | Additional executed verification |
|---|---:|---|
| ChurnIQ | 13 | Manual tie-aware ROC/AP/Brier parity, training-only preprocessing, split isolation, browser controls |
| ExperimentLab | 15 | Independent Pearson chi-square vs z p-value, tiny Fisher fixture, seeded bootstrap, calculator parity |
| MarketScope | 11 | 10 executed SQL/financial/referential assertions, independent pandas totals, browser/SQL amount parity |
| DemandCast | 12 | Scalar MAE/RMSE/WAPE parity, chronology and training-only selection fixtures, browser scenario parity |
| Total | **51 passed** | Do not add overlapping SQL/browser assertions to inflate pytest count |

Combined run: 51 passed in 1.61s (evidence/all-tests.txt). No coverage percentage or mypy pass is claimed. Fatal-error Ruff checks passed; Python files formatted. Baseline pipelines are fixed, not tuned until scores look impressive.

Browser QA: ChurnIQ filters/threshold/scenario validation/download and mobile; ExperimentLab five checks; MarketScope seven checks; DemandCast seven checks. Screenshots are genuine running app captures. Scripts live in scripts/browser with portable environment overrides. Python training remains local; public controls work on precomputed evidence. No uncaught JavaScript errors in recorded checks.

## Failures, fixes and limitations

- Web text fetch could not download the 43.5 MB UCI archive; the explicit official-source acquisition script downloaded it normally. No dataset substitution occurred.
- openpyxl was initially absent; installed and pinned before workbook parsing.
- Invalid-date fixture initially emitted a pandas inference warning; explicit mixed-format parsing resolved it.
- MarketScope's first mobile check failed horizontal overflow on long GBP totals. Responsive typography, wrapping and minimum-width fixes passed the rerun.
- Model comparison did not force a complex winner. ChurnIQ retained its validation-selected random forest even though logistic test AP was higher. DemandCast retained moving average; high 53.15% WAPE is plainly reported.
- ChurnIQ lacks reliable source timestamps, so prospective feature availability remains unverified. Its economic assumptions are not estimated treatment effects.
- ExperimentLab uses a simulated RCT; no real experiment was deployed. Bootstrap degenerates for boundary probabilities; Wilson/Newcombe and exact checks expose edge behavior.
- Retail exact-duplicate and merchandise definitions affect totals; sensitivity is reported. Missing customer identity limits customer analysis. Source timezone is unknown, and December 2011 is incomplete.
- Forecasts model units sold, not unobserved demand. Pooled residual bands and inventory formulas are assumptions, not calibrated guarantees or actual savings.
- No Power BI Desktop/.pbix or dbt execution is claimed; working SQL and BI-ready aggregate exports are delivered.

Public deployment and final résumé checks are recorded in PUBLICATION.md after verification. Existing résumé experience is user-supplied historical material, not authenticated by this technical audit; the new project bullets are independently evidenced in the private résumé ledger.
