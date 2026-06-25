# Python and Jupyter Workflow

The project contains three complementary Python artefacts:

1. `app.py` is the self-contained Streamlit deployment application.
2. `src/bi_pipeline.py` is a reusable analytical module for data validation, Sales Fact creation, KPI logic, RFM segmentation, and explainable rule-based insights.
3. `notebooks/01_retailmart_data_validation_and_eda.ipynb` documents exploratory analysis and validation for academic review.

## Local development setup

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Set database variables only in your local environment. Do not commit a real `.streamlit/secrets.toml`, `.env` file, password, connection string, or database export with credentials.

```bash
# Windows Git Bash example
export POSTGRES_HOST="your-host"
export POSTGRES_PORT="5432"
export POSTGRES_DATABASE="your-database"
export POSTGRES_USER="your-user"
export POSTGRES_PASSWORD="your-password"
export POSTGRES_SSLMODE="require"
```

## Validate database mapping

```bash
python -m scripts.neon_database_validation
```

The script writes safe CSV validation summaries into `reports/` and does not include credentials in its outputs.

## Open the notebook

```bash
jupyter lab
```

Open `notebooks/01_retailmart_data_validation_and_eda.ipynb` from the repository root.
