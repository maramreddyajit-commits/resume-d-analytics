# CFO/operations briefing

Decision: use a reconciled merchandise view for historical trading review, but request costs and stock records before procurement or profitability recommendations.

Observed findings under the documented merchandise/deduplication definition:

1. 1,021,127 accepted lines produce £19,642,676.02 gross, £716,425.97 returns and £18,926,250.05 net sales. These are historical 2009–2011 GBP amounts, not current operating results. Removing returns would materially overstate revenue.
2. The top 10 products represent 8.0441% of gross sales. The leading product, code 22423, has £330,590.32 gross and £314,045.02 net. Inspect return reasons for high-value lines before assuming they deserve more inventory; no stock availability or costs are present.
3. 226,964 accepted lines lack customer identity. They contribute to financial totals but cannot support customer RFM or retention. Customer analysis is therefore a selected subset, not a census of all shoppers. Among identified purchasing customers, 925 are in the defined lapsed-high-value segment with £2,549,177.21 historical gross purchases; this is not forward-looking CLV.

Recommendations: (a) implement stable invoice/customer capture and reconciliation before publishing customer KPIs; (b) investigate returns by product using the drill-down, with reasons and fulfillment context collected next; (c) use complete-month cohort behavior to design a consent-aware repeat-purchase experiment, not to claim a CRM campaign already improved retention.

Sensitivity: exact duplicate lines may be legitimate repeated items. Including eligible duplicates yields £19,382,459.88 net. Including deduplicated positive-price non-merchandise transactions yields £19,014,209.838; fractional source prices explain the sub-penny total. Do not mix these definitions. December 2011 is partial, making an apparent monthly decline misleading. Wholesalers and bulk buyers are real parts of the source, not automatically outliers to remove.

Metrics unavailable: profit margins, advertising CAC/ROAS, visitor conversion, inventory levels and actual stockouts. No recommendation here claims measured cost savings. SQL/pandas reconciliation proves arithmetic consistency under the chosen rules; it does not validate original accounting completeness.
