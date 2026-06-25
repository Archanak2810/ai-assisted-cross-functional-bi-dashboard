# RetailMart Domain-Wise Questions, KPIs, and Cross-Functional Questions

This registry is the design foundation for the deployed Streamlit dashboard. Coverage labels are used consistently in the dashboard:

- **Direct** — computable from the current schema.
- **Workaround / Proxy** — derived logic is possible, but results should not be interpreted as causal attribution.
- **Gap** — additional fields are required.

## Sales & Customer

### Core business questions
1. What drives revenue across products, categories, regions, stores, and customer tiers?
2. Who are the most valuable customers, and what is their relative lifetime value?
3. What is the repeat-purchase pattern, and which customers show early churn risk?
4. Why do customers return products, and which products or categories generate the most returns?
5. How satisfied are customers based on reviews, support tickets, calls, and sentiment?
6. Is the loyalty programme associated with repeat purchases, point balances, and redemption behaviour?

### KPIs
- Total revenue, gross margin, profit margin, average order value, units per order
- Repeat-purchase rate, RFM segments, CLV proxy, new vs returning customer revenue
- Return rate, refund value, review rating, ticket resolution time, loyalty redemption rate

## Marketing

### Core business questions
1. Which campaigns and platforms coincide with revenue and order movement?
2. Are campaigns pacing to budget or over/under-spending?
3. What are email open rate, click-through rate, and click-to-open rate by campaign?
4. Which categories or brands deserve additional marketing investment?
5. Is blended customer acquisition cost improving over time?
6. How does web engagement convert into orders, and where may the funnel leak?

### KPIs
- Spend by platform, campaign pacing, email open rate, CTR, CTOR
- Blended CAC proxy, campaign-period revenue trend, promotion uplift proxy
- Web conversion proxy, pages per session, single-page-session share (optional web-event tables)

## Finance

### Core business questions
1. What are the revenue, expense, margin, and EBITDA proxy trends?
2. Which expense categories are the largest cost drivers?
3. How much is lost through refunds and failed refunds?
4. Are payments succeeding, and what are the failure or refund patterns?
5. Is the cost-to-revenue ratio improving or deteriorating?

### KPIs
- Gross revenue, total expenses, operating expense ratio, EBITDA proxy
- Refund value, refund rate, payment status mix, failed-refund count
- Cost-to-revenue ratio, expense-category concentration

## HR

### Core business questions
1. What are total payroll cost, labour cost as a share of revenue, and average salary by department and role?
2. Are employees attending consistently, and what are their average recorded work hours?
3. What are headcount, department distribution, role mix, and pay distribution?
4. Are salary payment records consistently processed?
5. What is attrition rate and average tenure? *(Gap: employee exit data is required.)*

### KPIs
- Headcount, average salary, gross payroll, net payroll, deduction rate
- Average recorded hours, missing-checkout rate, salary-payment status
- Revenue per employee, payroll-to-revenue proxy

## Operations & Logistics

### Core business questions
1. Do we hold the right inventory in the right locations, and where are below-reorder or high-capital positions?
2. Which suppliers have better inbound lead-time performance?
3. How fast and reliably do we deliver, and which courier performs best?
4. Which production lines or products drive rejection rates?
5. Is the platform healthy based on API errors, latency, and procedure failures?

### KPIs
- Below-reorder SKUs, inventory working capital, inventory value by category
- Inbound lead time, delivery cycle time, shipment-status mix, courier performance
- Production yield, rejection rate, supplier lead time, API error rate, p95 latency

## Cross-Functional

### Cross-functional business questions
1. Does marketing spend translate into revenue and profit movement?
2. Which high-value customer segments are at risk, and what is their revenue contribution?
3. Are high inventory working-capital categories also low-margin or slow-moving?
4. Do regions with stronger revenue have proportionate profit, staffing capacity, and store performance?
5. Could shipment delays, high rejection rates, or refund patterns indicate customer-experience risk?
6. Is payroll and operating expenditure increasing faster than revenue?
7. Which business area should management prioritise based on financial impact, customer risk, and operational risk?

### Cross-functional KPI combinations
- Marketing spend + revenue + profit
- Inventory value + category margin + sales velocity
- Region revenue + profit + employee headcount + salary
- Payroll + operating expenses + EBITDA proxy
- Shipment status + returns/refunds + customer reviews and support signals
- Production rejection + cost + inventory availability
