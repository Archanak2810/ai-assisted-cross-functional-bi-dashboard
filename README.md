# AI-Assisted Cross-Functional BI Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://newproject-mcepvojsuiwumvmqx8aw2f.streamlit.app/)

A cloud-connected, management-ready intelligence platform built with Streamlit and Neon PostgreSQL.  
Covers Sales & Customer, Marketing, Finance, HR, Operations & Logistics, Cross-Functional analytics, AI-Assisted Insights, and management report export.

## Live Dashboard
**Streamlit URL:** https://newproject-mcepvojsuiwumvmqx8aw2f.streamlit.app/

## Technology Stack
| Layer | Technology |
|---|---|
| Data storage | Neon PostgreSQL (cloud, serverless) |
| Data processing | Python 3.11, Pandas, NumPy |
| Visualisation | Plotly Express & Graph Objects |
| Dashboard UI | Streamlit ≥ 1.36 |
| Export | openpyxl (Excel), HTML, plain text |
| Deployment | Streamlit Cloud (GitHub-connected) |

## Repository Structure
```
ai-assisted-cross-functional-bi-dashboard/
├── app.py                          # Streamlit entry point — self-contained deployment app
├── src/
│   ├── __init__.py                  # Python package marker
│   └── bi_pipeline.py               # Reusable PostgreSQL/Pandas KPI and validation pipeline
├── scripts/
│   └── neon_database_validation.py  # Command-line Neon table and data-quality validation
├── notebooks/
│   └── 01_retailmart_data_validation_and_eda.ipynb  # Jupyter EDA and validation evidence
├── requirements.txt                # Streamlit deployment dependencies
├── requirements-dev.txt            # Jupyter development dependencies
├── .streamlit/
│   ├── config.toml                 # Theme settings
│   └── secrets.toml.example        # Credential template (never commit real secrets)
├── sql/
│   ├── 01_database_validation.sql  # Row-count and schema checks (Step 3)
│   └── 02_domain_analytics.sql     # Representative domain and cross-functional queries
├── database/
│   └── 00_verify_neon_connection.sql  # Quick Neon connectivity check
├── docs/
│   ├── architecture/               # Solution architecture and development methodology
│   ├── business_questions/         # Domain KPIs and cross-functional question registry
│   ├── data_dictionary/            # Schema overview and data quality notes
│   ├── setup/                      # Local, Neon, and GitHub/Streamlit setup guides
│   └── report_assets/              # Figure placement guide for the academic report
├── assets/
│   ├── figures/                    # Architecture and methodology PNG figures
│   └── screenshots/                # Dashboard screenshots (add after deployment)
├── reports/                        # Sample exported report outputs
├── DEPLOY_TO_STREAMLIT_CLOUD.md    # Step-by-step deployment guide
├── PROJECT_SUBMISSION_CHECKLIST.md # Academic submission tracking
└── .github/workflows/              # GitHub Actions syntax check
```

## Python and Jupyter Analysis Evidence

The dashboard is built with Python, Pandas, SQLAlchemy, PostgreSQL/Neon, Plotly, and Streamlit.

- `src/bi_pipeline.py` documents reusable data cleaning, required-table validation, Sales Fact construction, KPI calculation, RFM segmentation, and explainable rule-based insight logic.
- `scripts/neon_database_validation.py` provides a safe command-line check for PostgreSQL connectivity, table availability, and a data-quality profile.
- `notebooks/01_retailmart_data_validation_and_eda.ipynb` documents the exploratory analysis and validation workflow for academic review.

The deployment app remains self-contained in `app.py` to keep Streamlit Cloud setup simple. No real credentials are stored in the repository.

## Deployment Steps (Summary)
1. Push all repository contents to GitHub.
2. Load RetailMart dataset into Neon PostgreSQL.
3. Run `sql/01_database_validation.sql` in Neon SQL Editor to verify tables.
4. Create a Streamlit Cloud app linked to this repository; set `app.py` as the entry point.
5. Add Neon credentials under **App Settings → Secrets** (use `secrets.toml.example` as the template).
6. Deploy and verify all tabs, filters, KPI cards, AI Insights, and Export Report.

See `DEPLOY_TO_STREAMLIT_CLOUD.md` for the full step-by-step guide.

## Dashboard Tabs
| Tab | Content |
|---|---|
| Executive | Revenue, profit, margin, orders, monthly trend, executive insights |
| Sales & Customer | Product revenue, regional performance, RFM segments, return reasons |
| Marketing | Platform spend, email funnel, campaign pacing, spend vs revenue trend |
| Finance | EBITDA proxy, expense categories, payment status, refund analysis |
| HR | Headcount, salary, payroll trend, attendance hours |
| Ops & Logistics | Inventory exposure, shipment status, production rejection, supplier lead time |
| Cross-Functional | Marketing-revenue-profit, regional capacity, inventory-margin scatter |
| AI Insights | Rule-based management recommendations across all domains |
| Export | Download Text, Excel, and HTML management reports |

## Data Scope
The dashboard uses a synthetic RetailMart dataset for academic and demonstration purposes.  
It does not represent actual organisational data.

## Important — Credentials
Never commit real Neon credentials to GitHub.  
Use `.streamlit/secrets.toml` locally and Streamlit Cloud Secrets for deployment.
