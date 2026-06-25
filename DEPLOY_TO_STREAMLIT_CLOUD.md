# Deploy to Streamlit Cloud — Step-by-Step Guide

## Prerequisites
- GitHub account with this repository pushed
- Neon PostgreSQL project with RetailMart dataset loaded
- Streamlit Cloud account (free at streamlit.io)

## Step 1 — Push repository to GitHub
Upload all files from this folder to a new empty GitHub repository.  
Do NOT upload only `app.py` — all files must be present.

## Step 2 — Create Streamlit Cloud app
1. Go to https://share.streamlit.io
2. Click **New app**
3. Select your GitHub repository
4. Set **Main file path** to `app.py`
5. Click **Deploy**

## Step 3 — Add Neon credentials in Secrets
1. In Streamlit Cloud, open **App settings → Secrets**
2. Paste the following block with your real Neon values:

```toml
[postgres]
host     = "YOUR_NEON_POOLER_HOST"
port     = 5432
database = "neondb"
user     = "neondb_owner"
password = "YOUR_REAL_NEON_PASSWORD"
sslmode  = "require"
```

Use the **pooler host** from Neon (starts with `ep-...`), not a local IP.

## Step 4 — Deploy and verify
1. Click **Save** then **Clear cache and reboot**
2. Sidebar should show: **Live Neon connection verified**
3. Check all 9 tabs load without errors
4. Test filters, KPI cards, AI Insights, and Export Report downloads

## Troubleshooting
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` | Confirm `requirements.txt` is in repo root |
| `OperationalError` on connect | Check host is pooler URL, not local; verify sslmode = require |
| Blank charts | Run `sql/01_database_validation.sql` in Neon to confirm tables exist |
| `StreamlitDuplicateElementId` | This version uses unique chart keys — clear cache and reboot |

## Verification SQL
Run `database/00_verify_neon_connection.sql` in the Neon SQL Editor to confirm connectivity before deploying.
