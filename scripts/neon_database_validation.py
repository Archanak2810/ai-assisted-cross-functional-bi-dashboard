"""Validate Neon PostgreSQL connectivity and mapped tables without exposing secrets.

Run from the repository root:
    python -m scripts.neon_database_validation

Set these environment variables before running:
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_USER,
POSTGRES_PASSWORD, and optionally POSTGRES_SSLMODE.
"""
from __future__ import annotations

import os
from pathlib import Path

from src.bi_pipeline import (
    TABLE_SPECS,
    create_postgres_engine,
    data_quality_profile,
    load_tables_from_postgres,
    test_database_connection,
    validate_required_tables,
)


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing {name}. Set database credentials as environment variables or use Streamlit Secrets for app deployment."
        )
    return value


def main() -> None:
    host = _required_setting("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = _required_setting("POSTGRES_DATABASE")
    user = _required_setting("POSTGRES_USER")
    password = _required_setting("POSTGRES_PASSWORD")
    sslmode = os.getenv("POSTGRES_SSLMODE", "require")

    engine = create_postgres_engine(host, port, database, user, password, sslmode)
    status = test_database_connection(engine)
    print(f"Connection status: {status['status']} | Database: {status['database']} | User: {status['user']}")

    data, messages = load_tables_from_postgres(engine, TABLE_SPECS.keys())
    for message in messages:
        print(f"{message.severity.upper()}: {message.message}")

    required = validate_required_tables(data)
    quality = data_quality_profile(data)
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    required.to_csv(reports_dir / "neon_required_table_validation.csv", index=False)
    quality.to_csv(reports_dir / "neon_data_quality_profile.csv", index=False)

    print("\nRequired table validation")
    print(required.to_string(index=False))
    print("\nValidation reports written to reports/")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(f"Validation not run: {exc}")
