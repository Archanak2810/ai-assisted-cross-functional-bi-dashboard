# Jupyter Notebooks

This folder contains the notebook used to document exploratory analysis and data-quality validation for the academic project.

- `01_retailmart_data_validation_and_eda.ipynb` demonstrates PostgreSQL/Neon connectivity, mapped-table validation, data-quality profiling, Sales Fact construction, executive KPI calculation, monthly trends, RFM segmentation, and explainable rule-based insight generation.

## Run locally

1. Install the dashboard dependencies and the development dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. Set database variables in your local terminal. Do not store real credentials inside this notebook or in GitHub.

3. Start Jupyter Lab from the repository root:

   ```bash
   jupyter lab
   ```

The notebook is for analysis documentation only. The deployed Streamlit dashboard runs through `app.py`.
