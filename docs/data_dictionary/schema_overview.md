# RetailMart Schema Overview

The dashboard is built on a multi-schema retail dataset. Primary analytical domains include:

| Domain | Typical Tables | Dashboard Use |
|---|---|---|
| Sales | orders, order_items, payments, returns | Revenue, profit, AOV, product and regional performance |
| Customers | customers, addresses, reviews, wallets | RFM, customer value, retention and satisfaction proxies |
| Marketing | campaigns, ads_spend, email_clicks | Spend, email engagement, platform analysis, ROI proxy |
| Finance | expenses, accounts, revenue_summary, transfer_log | Expense, refunds, EBITDA, cost-to-revenue |
| HR & Payroll | employees, attendance, salary_history, pay_slips | Headcount, attendance, salary and payroll metrics |
| Operations | work_orders, production_lines | Output, rejection rate, manufacturing quality |
| Logistics & Supply Chain | warehouses, shipments, inventory_snapshots | Shipment status, warehouse exposure, inventory working capital |
| Products & Core | products, categories, brands, dimensions | Product, category, brand, region, and date enrichment |

The detailed business-question and KPI registry is in `docs/business_questions/domain_questions_and_kpis.md`.
