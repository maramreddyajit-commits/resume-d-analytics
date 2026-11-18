# Decision brief: investigate friction before promising savings

The customer-success stakeholder needs a tractable outreach shortlist, not an unexplained accuracy score. ChurnIQ uses IBM's fictional Telco sample to demonstrate that workflow.

Cleaning retained 7,043 accounts and treated 11 blank cumulative charges as missing. Training-only preprocessing and a stratified 60/20/20 split prevent test-set preprocessing leakage. Two fixed models were compared against a majority baseline; no hyperparameter search was performed. Validation average precision selected the random forest and validation F1 selected threshold 0.36. The test is used once for reporting, not model selection. Logistic regression's slightly higher test AP does not justify switching afterward.

Three outreach hypotheses follow from descriptive associations and should be tested, not presented as causal conclusions:

1. Month-to-month accounts have 1,655 churn labels among 3,875 accounts (42.71%), versus 166/1,473 (11.27%) on one-year and 48/1,695 (2.83%) on two-year contracts. Interview customers about commitment, pricing and flexibility before testing a contract offer; selection and tenure confound this comparison.
2. Investigate first-year onboarding friction using the tenure-band table. A prospective experiment could offer optional setup assistance; guard against contact burden and complaint increases.
3. Investigate service/support friction using TechSupport and InternetService segment counts and rates. Test useful support, not coercive retention. Customers self-select services, so segment differences alone cannot establish a treatment benefit.

The proposed operating policy ranks test scores within a budget. Default assumptions are 500 budget units, 10 per contact, 10% prevention among would-be churners and 300 value units per prevented churn. Expected value equals summed risk × assumed prevention × value minus contact costs. These are deliberately separate assumptions, not observed treatment effects or dollars saved. Risk prediction does not estimate uplift: high-risk accounts may be impossible to retain.

Before operational use: establish timestamped feature availability, validate/calibrate on a later real cohort with lawful access, estimate intervention effects through random assignment, and assess uncertainty and subgroup error. Gender/senior status audit tables describe stability only; excluded features can still have proxies. No fairness compliance claim is made.
