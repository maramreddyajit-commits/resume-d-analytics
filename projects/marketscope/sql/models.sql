-- Grain: one accepted, deduplicated source invoice line. Monetary fields are micro-GBP integers.
CREATE INDEX IF NOT EXISTS idx_fact_invoice ON fact_lines(invoice);
CREATE INDEX IF NOT EXISTS idx_fact_product_date ON fact_lines(product_key,date_key);
CREATE VIEW sales AS SELECT * FROM fact_lines WHERE quantity>0;
CREATE VIEW returns AS SELECT * FROM fact_lines WHERE quantity<0;
CREATE VIEW monthly AS
 SELECT substr(date_key,1,7) month, location_key country,
 SUM(CASE WHEN quantity>0 THEN amount_micro ELSE 0 END) gross_micro,
 -SUM(CASE WHEN quantity<0 THEN amount_micro ELSE 0 END) returns_micro,
 SUM(amount_micro) net_micro,
 COUNT(DISTINCT CASE WHEN quantity>0 THEN invoice END) orders,
 SUM(CASE WHEN quantity>0 THEN quantity ELSE 0 END) sold_units
 FROM fact_lines GROUP BY 1,2;
CREATE VIEW product_rank AS
 WITH totals AS (SELECT product_key, SUM(CASE WHEN quantity>0 THEN amount_micro ELSE 0 END) gross_micro,
 SUM(amount_micro) net_micro, SUM(CASE WHEN quantity>0 THEN quantity ELSE 0 END) units
 FROM fact_lines GROUP BY product_key), ranked AS (
 SELECT *,ROW_NUMBER() OVER(ORDER BY gross_micro DESC,product_key) rank,
 SUM(gross_micro) OVER() total_gross FROM totals)
 SELECT *,1.0*gross_micro/total_gross gross_share FROM ranked;
CREATE VIEW customer_rfm AS
 WITH base AS (SELECT customer_key, MAX(date_key) last_purchase,COUNT(DISTINCT invoice) frequency,
 SUM(amount_micro)/1000000.0 monetary FROM sales WHERE customer_key!='UNKNOWN' GROUP BY customer_key),
 scored AS (SELECT *,CAST(julianday('2011-12-10')-julianday(last_purchase) AS INTEGER) recency_days,
 NTILE(4) OVER(ORDER BY last_purchase,customer_key) r_score,
 NTILE(4) OVER(ORDER BY frequency,customer_key) f_score,
 NTILE(4) OVER(ORDER BY monetary,customer_key) m_score FROM base)
 SELECT *,CASE WHEN r_score>=3 AND f_score>=3 AND m_score>=3 THEN 'Recent high-value repeat'
 WHEN r_score<=2 AND m_score>=3 THEN 'Lapsed high-value'
 WHEN r_score>=3 THEN 'Other recent' ELSE 'Other lapsed' END segment FROM scored;
CREATE VIEW cohort_retention AS
 WITH activity AS (SELECT DISTINCT customer_key,substr(date_key,1,7) month FROM sales WHERE customer_key!='UNKNOWN'),
 firsts AS (SELECT customer_key,MIN(month) cohort FROM activity GROUP BY customer_key),
 cohorts AS (SELECT cohort,COUNT(*) cohort_size FROM firsts GROUP BY cohort)
 SELECT f.cohort,a.month,c.cohort_size,COUNT(*) returned,
 12*(CAST(substr(a.month,1,4) AS INT)-CAST(substr(f.cohort,1,4) AS INT))+CAST(substr(a.month,6,2) AS INT)-CAST(substr(f.cohort,6,2) AS INT) age_month,
 1.0*COUNT(*)/c.cohort_size rate
 FROM activity a JOIN firsts f USING(customer_key) JOIN cohorts c USING(cohort)
 WHERE a.month<'2011-12' GROUP BY f.cohort,a.month,c.cohort_size;
