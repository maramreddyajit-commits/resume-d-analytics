# Interview evidence and honest answers

The ten project-specific questions/answers are in each project's INTERVIEW_GUIDE.md. Begin with stakeholder problem, implementation, measured result, limitation and next step.

## Headline denominators

- ChurnIQ: AUC compares positive-negative score pairs among 1,409 test accounts, not all 7,043 training-inclusive records. AP summarizes precision over recall increments. Threshold precision uses TP/(TP+FP); recall uses TP/(TP+FN). Model selection used only validation AP.
- ExperimentLab: 1,232 control events / 10,113 units versus 1,326 / 9,887 treatment units. Absolute difference 0.0122921; relative difference 0.100901. Confidence interval [0.00303315,0.02155951]. A p-value is not probability the treatment works. All outcomes are synthetic.
- MarketScope: 1,021,127 accepted lines from 1,067,371 raw rows. Invoice counts differ from line counts. Net is £19,642,676.02 minus £716,425.97. Customer analyses exclude unknown identity; sales totals do not.
- DemandCast: WAPE = 44,924.5 absolute unit error / 84,531 observed units over 144 test predictions. MAE = 44,924.5 / 144 = 311.9757. This is not 46.85% “accuracy.” Twelve products × three origins × four horizons = 144. MASE uses each origin's training-only seasonal scale.

## Questions across projects

**Why not a bigger stack?** Python and SQLite make the analyses inspectable and reproducible. Hosting static result views avoids pretending a portfolio demo is a production data platform.

**What did you fix?** Strict input validation, edge denominators, train-only preprocessing and source cache integrity have explicit tests. Browser QA caught a mobile overflow in currency totals; wrapping and responsive sizing fixed it.

**What would deployment require?** Monitoring, secure identity/data access, refreshed source pipelines, data contracts, prospective model validation and appropriate governance. Public demos are already accessible, but no production customer integration exists.

**What is a business recommendation versus a result?** A result is a reproduced dataset calculation. A recommendation interprets it under assumptions. A causal effect or cost saving requires separate evidence; none is fabricated here.

**How reproducible is it?** Pinned dependency versions, fixed seeds/splits, original-data checksums, saved predictions and independent arithmetic. Each project's metric JSON matched its second full pipeline run byte-for-byte on the audited environment.
