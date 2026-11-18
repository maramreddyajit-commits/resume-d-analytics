# Forecast data lineage

Source: the completed MarketScope warehouse, derived from UCI Online Retail II, Chen (2012), DOI 10.24432/C5CG6D, CC BY 4.0. See ../marketscope/DATA_PROVENANCE.md for download, checksum, row treatment and historical provenance. M5's competition page was inspected but no authorized dataset download/session was established; no Kaggle access restriction was bypassed. The declared alternative is UCI observed sales, not M5 or simulated external observations.

Select only positive accepted merchandise quantities, excluding returns. Aggregate by product and week ending Sunday. Drop incomplete boundary weeks; use 104 complete weeks ending December 13, 2009 through December 4, 2011. Reindex absent weeks to zero recorded sales, not zero unconstrained demand. Choose the top 12 products by units in the first 52 weeks only; later outcomes never select SKUs.

Validation origins: 60,68,76 observed weeks, each predicting four subsequent weeks. Test origins: 88,92,96, also four-week horizons. This yields 144 validation and 144 test SKU-week predictions per model, with no overlap between validation and test target windows. Expanding windows legitimately use earlier observed test weeks at later origins. Each training-end and target date is saved. No random seed is needed; fixed origins and deterministic optimizers are used.

Production-style future forecasts use all 104 historical weeks only after model selection is frozen. Future CSV has 48 rows (12 products × four weeks). These forecasts have no subsequently observed actuals in this source and are not used to report test error. Pooled validation absolute residuals provide a heuristic uncertainty band, not a guaranteed calibrated predictive interval.

Reproduce: build MarketScope, then `python -m projects.demandcast.src.forecast`. Weekly aggregated series and all backtest predictions are saved locally in data/. Public outputs contain product aggregates, no customer IDs. No inventory, stockout, margin or actual lead-time data are available. Safety stock assumes independent normal errors, specified service level and holding cost, with validation RMSE as a rough weekly variability proxy.
