# MarketScope — retail warehouse and executive BI

Historical merchandise analytics reconciled from both sheets of UCI Online Retail II into SQLite, with executable SQL models, date/customer/product/location dimensions, RFM, cohorts and an interactive browser dashboard.

```sh
python scripts/download_retail.py
python -m projects.marketscope.src.warehouse
python -m pytest projects/marketscope/tests -q
python -m http.server 8780 --directory docs
```
Open http://localhost:8780/#marketscope. Country/date filters, empty states, product drill-down, cohort selection and CSV exports work. The public view uses precomputed SQL aggregates; raw SQL and the local database reproduce them. See [DATA_PROVENANCE.md](DATA_PROVENANCE.md), [CASE_STUDY.md](CASE_STUDY.md), [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md).

Architecture: official workbook → raw_classified with disposition → fact_lines and four dimensions → SQL views (CTEs/window functions/NTILE/cohort joins) → reconciled aggregate CSV/JSON → dashboard. `sql/models.sql` is executed, not decorative SQL. `src/warehouse.py` orchestrates it and checks independent pandas arithmetic.

Power BI Desktop was unavailable on this Mac. Import docs/data/marketscope/*.csv using Get Data > Text/CSV. Monthly has month/country grain; product and RFM exports are full-period aggregates and should not be joined as transaction facts. For a full star model, connect to the local SQLite warehouse through a suitable connector or export its fact/dimension tables; relate dimension unique keys one-to-many to fact keys, use single-direction filtering, and define Gross/Returns/Net from integer micro-GBP /1e6. No .pbix file or executed dbt run is claimed; these are equivalent transparent SQL transforms.
