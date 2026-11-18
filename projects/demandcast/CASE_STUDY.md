# Operations decision: keep the baseline, expose uncertainty

Question: can a transparent forecast support a purchasing discussion for selected historical gift SKUs without claiming to observe true demand?

Twelve products were selected by sales units in the first 52 complete weeks only. Each has 104 observed weeks. Three validation origins and three later test origins forecast four weeks each. Holt parameters are optimized only on each training window. A more complex method must improve validation WAPE by at least 5% relative to the best baseline to be selected. This rule was set before test evaluation.

Four-week moving average won validation (WAPE 67.62%) against seasonal naïve (102.91%) and Holt (73.49%). On 144 held-out SKU-week predictions, moving average has MAE 311.98 units, RMSE 565.38, WAPE 53.15% and MASE 0.625. Seasonal naïve has MAE 637.86 and WAPE 108.66%. Holt's test RMSE is slightly better, but its validation result did not qualify it; do not switch after inspecting the test.

These errors are still substantial. High-volume irregular wholesale purchases and limited history make reliable seasonal estimation difficult. A 53% WAPE is not an operational accuracy guarantee. Aggregate WAPE weights high-volume products; per-product and horizon tables expose heterogeneity. The pooled validation absolute-error radius is 859 units, with 92.36% empirical test coverage for a nominal 90% band. It is heuristic, especially for low-volume SKUs and correlated horizons.

Recommendation: use a simple baseline for a first analyst review, collect inventory availability and lead-time history, and compare future forecasts against actual orders before operationalizing. The scenario can illustrate how assumed service level and lead time raise safety stock; it cannot tell a buyer how much to order without on-hand/on-order inventory. Holding costs are assumed, not measured. No savings, stockout reduction or real inventory intervention occurred.

A sensible next experiment is a shadow forecast: generate weekly predictions without changing orders, log stock availability and promotions, then assess performance by product volume and horizon on genuinely new data.
