# Add Python and Jupyter Files to Your Existing Repository

This project now includes reusable Python and Jupyter artefacts to demonstrate the full technology stack: PostgreSQL/Neon, Python, Pandas, SQLAlchemy, Streamlit, and rule-based AI-assisted insights.

## New files and folders

- `src/bi_pipeline.py` — reusable PostgreSQL/Pandas data pipeline, Sales Fact creation, KPI calculation, RFM segmentation, and explainable rule-based insights.
- `scripts/neon_database_validation.py` — command-line validation of database connectivity, mapped table availability, and data-quality profile.
- `notebooks/01_retailmart_data_validation_and_eda.ipynb` — academic notebook documenting the end-to-end analytical workflow.
- `requirements-dev.txt` — Jupyter-only development dependencies. This does not affect Streamlit Cloud deployment.
- `docs/setup/python_and_notebook_workflow.md` — local run instructions.

## How to merge this package

1. Extract the **code additions ZIP** into the root of your existing repository.
2. Choose **Replace files** when Windows asks to merge updated `README.md`, `.gitignore`, or the GitHub workflow.
3. Do not create or copy a real `.streamlit/secrets.toml` file. Keep only `secrets.toml.example` in GitHub.
4. In Git Bash, check the new artefacts:

   ```bash
   git status
   ```

   You should see `src/`, `scripts/`, `notebooks/`, `requirements-dev.txt`, and documentation files as new or modified files.

5. Commit and push:

   ```bash
   git add .
   git commit -m "Add Python analytics pipeline and Jupyter validation notebook"
   git push -u origin main
   ```

## Important

`app.py` remains the Streamlit Cloud entry point. The new `src/` pipeline and notebook provide reusable development and academic evidence; they do not require changing the dashboard main file.
