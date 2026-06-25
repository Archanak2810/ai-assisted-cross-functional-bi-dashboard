# AI-Assisted Cross-Functional BI Dashboard

A cloud-connected, management-oriented Business Intelligence dashboard developed for a synthetic RetailMart environment.

The application integrates Sales & Customer, Marketing, Finance, HR, Operations & Logistics, Cross-Functional analytics, AI-Assisted Insights, and management report exports in one Streamlit interface.

## Live Dashboard

🚀 **[Open the Live Streamlit Dashboard](https://ai-assisted-cross-functional-bi-dashboard-g8wfha5zkccdlqnfum8n.streamlit.app/)**

---

## Project Overview

The dashboard is designed to help management users monitor business performance, investigate linked drivers, and export findings for review and action.

It provides:

* Executive KPI monitoring for revenue, profit, margin, and orders
* Sales, product, regional, customer, and RFM analysis
* Marketing spend, campaign pacing, and email engagement analysis
* Finance analysis including expenses, refunds, payment status, EBITDA proxy, and cost-to-revenue ratio
* HR analysis covering headcount, payroll, salary, attendance, and revenue per employee
* Operations and Logistics analysis for inventory, shipment status, supplier lead time, and production rejection
* Cross-functional analysis across revenue, cost, marketing, inventory, workforce, and profitability
* Explainable rule-based AI-assisted management insights
* Exportable Text, Excel, and HTML management reports

---

## Technology Stack

| Layer                 | Technology                              |
| --------------------- | --------------------------------------- |
| Data storage          | Neon PostgreSQL                         |
| Data processing       | Python 3.11, Pandas, NumPy              |
| Database connectivity | SQLAlchemy and PostgreSQL               |
| Visualisation         | Plotly Express and Plotly Graph Objects |
| Dashboard UI          | Streamlit                               |
| Export                | openpyxl, HTML, plain text              |
| Deployment            | Streamlit Cloud                         |
| Version control       | GitHub                                  |

---

## Repository Structure

```text
ai-assisted-cross-functional-bi-dashboard/
├── app.py                          # Streamlit entry point and deployment app
├── src/
│   ├── __init__.py                 # Python package marker
│   └── bi_pipeline.py              # Reusable KPI, validation, and insight functions
├── scripts/
│   └── neon_database_validation.py # PostgreSQL/Neon validation utility
├── notebooks/
│   └── 01_retailmart_data_validation_and_eda.ipynb
├── requirements.txt                # Streamlit deployment dependencies
├── requirements-dev.txt            # Jupyter development dependencies
├── .streamlit/
│   ├── config.toml                 # Streamlit theme configuration
│   └── secrets.toml.example        # Safe credential template
├── sql/
│   ├── 01_database_validation.sql  # Schema and table validation queries
│   └── 02_domain_analytics.sql     # Domain and cross-functional SQL queries
├── database/
│   └── 00_verify_neon_connection.sql
├── docs/
│   ├── architecture/
│   ├── business_questions/
│   ├── data_dictionary/
│   ├── setup/
│   └── report_assets/
├── assets/
│   ├── figures/
│   └── screenshots/
├── reports/
├── DEPLOY_TO_STREAMLIT_CLOUD.md
├── PROJECT_SUBMISSION_CHECKLIST.md
└── .github/workflows/
```

---

## Dashboard Tabs

| Tab                    | Key Analysis                                                                       |
| ---------------------- | ---------------------------------------------------------------------------------- |
| Executive Overview     | Revenue, profit, margin, orders, trends, and executive priorities                  |
| Sales & Customer       | Product contribution, regional performance, RFM segments, returns, and loyalty     |
| Marketing              | Platform spend, campaign pacing, email funnel, and spend-versus-revenue comparison |
| Finance                | Expenses, refund analysis, payment status, EBITDA proxy, and cost-to-revenue ratio |
| HR                     | Headcount, salary, payroll, attendance, and revenue per employee                   |
| Operations & Logistics | Inventory exposure, shipment status, supplier lead time, and rejection rate        |
| Cross-Functional       | Marketing, revenue, profit, inventory, workforce, and cost relationships           |
| AI Insights            | Explainable rule-based management recommendations                                  |
| Export Report          | Downloadable Text, Excel, and HTML management reports                              |

---

## Python and Jupyter Analysis Evidence

The project uses Python, Pandas, SQLAlchemy, PostgreSQL/Neon, Plotly, and Streamlit.

* `src/bi_pipeline.py` contains reusable data-cleaning, validation, Sales Fact construction, KPI calculation, RFM segmentation, and rule-based insight logic.
* `scripts/neon_database_validation.py` supports database connectivity checks, table validation, and data-quality profiling.
* `notebooks/01_retailmart_data_validation_and_eda.ipynb` documents exploratory data analysis, KPI validation, and academic evidence.
* `app.py` remains self-contained for reliable Streamlit Cloud deployment.

---

## Deployment Summary

1. Push the repository to GitHub.
2. Load the synthetic RetailMart dataset into Neon PostgreSQL.
3. Run `sql/01_database_validation.sql` in Neon SQL Editor.
4. Create a Streamlit Cloud application linked to this repository.
5. Select `app.py` as the main file.
6. Add database credentials in Streamlit Cloud **App Settings → Secrets**.
7. Deploy and verify all tabs, filters, KPI cards, AI Insights, and export options.

See [`DEPLOY_TO_STREAMLIT_CLOUD.md`](DEPLOY_TO_STREAMLIT_CLOUD.md) for detailed instructions.

---

## Data Scope

The dashboard uses a synthetic RetailMart dataset created for academic and demonstration purposes.

It does not contain real organisational, customer, employee, supplier, or financial data.

The dataset is stored separately from this repository because it contains multiple related PostgreSQL schemas and large source files.

For dataset access and loading instructions, see:

* [`data/README.md`](data/README.md)
* [`docs/setup/neon_setup.md`](docs/setup/neon_setup.md)
* [`docs/data_dictionary/schema_overview.md`](docs/data_dictionary/schema_overview.md)

---

## Dashboard Screenshots

<img width="1532" height="696" alt="Dashboard" src="https://github.com/user-attachments/assets/95474e48-cf08-446b-9c50-64021b26cc5c" />

Example files:

```text
01_executive_overview.png
02_sales_customer.png
03_marketing.png
04_finance.png
05_hr.png
06_operations_logistics.png
07_cross_functional.png
08_ai_insights.png
09_export_report.png
```

---

## Security and Credentials

> Never commit real database credentials, passwords, connection strings, or `.env` files to GitHub.

Use:

* `.streamlit/secrets.toml` only on your local machine
* Streamlit Cloud Secrets for deployment
* `.streamlit/secrets.toml.example` as the safe repository template

---

## Project Status

The current dashboard delivers:

* PostgreSQL/Neon-backed data access
* Cross-functional KPI analysis
* Interactive Streamlit dashboard tabs and filters
* Python and Pandas processing
* Plotly visualisations
* Rule-based AI-assisted insights
* Text, Excel, and HTML export reports
* SQL validation and Jupyter notebook evidence
* GitHub-ready documentation and deployment guidance

---

## Academic Note

This project is an MBA Business Analytics capstone submission. The dashboard demonstrates business intelligence, data preparation, KPI design, cross-functional analytics, explainable AI-assisted insights, and management reporting in a simulated RetailMart environment.
