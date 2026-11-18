# DemandCast — weekly sales forecasts and inventory scenarios

Compares seasonal naïve, four-week moving average and Holt trend forecasts using expanding-window validation and held-out evaluation. The simple baseline wins; complexity is not forced into the result.

```sh
# First reproduce MarketScope as documented in its README.
python -m projects.demandcast.src.forecast
python -m pytest projects/demandcast/tests -q
python -m http.server 8780 --directory docs
```
Open http://localhost:8780/#demandcast. Select a product, inspect dated held-out predictions, download future forecasts and change lead-time/service/holding-cost assumptions. No forecast training occurs in the public browser.

[Data provenance](DATA_PROVENANCE.md) · [Case study](CASE_STUDY.md) · [Interview guide](INTERVIEW_GUIDE.md). Exact metrics: ../../evidence/demandcast-metrics.json.

Architecture: curated positive invoice quantities → complete weekly series → training-only SKU selection → fixed validation origins → model choice → untouched later origins → future forecast export and assumption-only inventory scenario. Core source src/forecast.py. MAE/RMSE/WAPE independently rechecked through scalar arithmetic. MASE scales each error using that origin's training-only seasonal-naïve absolute differences; zero scale is undefined, not zero error.
