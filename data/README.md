# Data

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
