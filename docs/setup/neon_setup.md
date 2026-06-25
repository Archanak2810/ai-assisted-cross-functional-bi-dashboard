# Neon PostgreSQL Setup

1. Create or open your Neon project.
2. Create the `neondb` database, or use the database provided by Neon.
3. Load RetailMart schemas and tables into Neon.
4. Verify the upload with `sql/01_database_validation.sql`.
5. Copy the Neon **pooled connection** host, not a local PostgreSQL host.
6. Store credentials only in Streamlit Secrets or a local untracked `secrets.toml` file.

Do not place passwords in Python files, SQL files, screenshots, or GitHub commits.
