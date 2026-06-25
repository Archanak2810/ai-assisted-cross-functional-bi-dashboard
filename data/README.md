# Data

The RetailMart dataset is a synthetic, multi-schema PostgreSQL dataset used for this academic dashboard project. It is stored separately in OneDrive and is not included in this repository because of its size and relational structure.

# Dataset access

Open the RetailMart Synthetic Dataset on OneDrive https://1drv.ms/f/c/33440d1b4aec2fdf/IgC_yDWqam60Tq84Tmt6l802ARDfFFRanGkz6WfIoJTIVXI?e=ZRtmju 

The dataset is intended only for academic evaluation and project demonstration. It does not contain real customer, employee, supplier, or organisational data.

# Why the dataset is stored separately
- The dataset contains 45+ related tables across multiple PostgreSQL schemas and is too large for efficient GitHub storage.
- The repository contains only the source code, SQL scripts, documentation, dashboard assets, and setup guidance.
- Database passwords, connection strings, and other credentials are never included in the repository.

# How to load the data

Follow the instructions in docs/setup/neon_setup.md to load the dataset into PostgreSQL or Neon before running the Streamlit dashboard.

# Dataset structure

The dataset covers the following PostgreSQL schemas:

sales, products, core, stores, customers, marketing, finance, hr, payroll, supply_chain, manufacture, audit, loyalty, support, and call_center.

For the complete table inventory and schema relationships, see docs/data_dictionary/schema_overview.md.# Data

The RetailMart dataset is a synthetic dataset loaded into Neon PostgreSQL.

It is NOT stored in this repository for two reasons:
1. The dataset is too large for GitHub (45+ tables, multi-schema structure).
2. Database credentials must never be committed to version control.

## How to load data
Follow the instructions in `docs/setup/neon_setup.md`.

## Dataset structure
The dataset covers 15 PostgreSQL schemas:
`sales`, `products`, `core`, `stores`, `customers`, `marketing`, `finance`,
`hr`, `payroll`, `supply_chain`, `manufacture`, `audit`, `loyalty`, `support`, `call_center`

See `docs/data_dictionary/schema_overview.md` for the full table inventory.
