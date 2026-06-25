"""Reusable PostgreSQL and Pandas analytics pipeline for the RetailMart BI project.

The Streamlit dashboard in ``app.py`` is intentionally self-contained for simple
Streamlit Cloud deployment. This module provides the same core analytical pattern
in a reusable form for Jupyter-based exploration, SQL/Python validation, and
academic documentation. It contains no credentials and reads all connection
settings from the calling application or environment variables.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus
import json

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

VALID_ORDER_STATUSES = {"Delivered", "Shipped", "Out for Delivery", "Processing"}

# Table keys are mapped to the PostgreSQL schema/table names used by the project.
# Required tables are needed to build the central sales fact; optional tables extend
# analysis across customer, marketing, finance, HR, operations, and logistics domains.
TABLE_SPECS: dict[str, dict[str, Any]] = {
    "orders": {"pg": ("sales", "orders"), "required": True},
    "order_items": {"pg": ("sales", "order_items"), "required": True},
    "products": {"pg": ("products", "products"), "required": True},
    "brand": {"pg": ("core", "dim_brand"), "required": True},
    "category": {"pg": ("core", "dim_category"), "required": True},
    "stores": {"pg": ("stores", "stores"), "required": False},
    "region": {"pg": ("core", "dim_region"), "required": False},
    "customers": {"pg": ("customers", "customers"), "required": False},
    "sales_returns": {"pg": ("sales", "returns"), "required": False},
    "sales_shipments": {"pg": ("sales", "shipments"), "required": False},
    "ads_spend": {"pg": ("marketing", "ads_spend"), "required": False},
    "campaigns": {"pg": ("marketing", "campaigns"), "required": False},
    "email_clicks": {"pg": ("marketing", "email_clicks"), "required": False},
    "finance_expenses": {"pg": ("finance", "expenses"), "required": False},
    "finance_payments": {"pg": ("finance", "payments"), "required": False},
    "attendance": {"pg": ("hr", "attendance"), "required": False},
    "salary_history": {"pg": ("hr", "salary_history"), "required": False},
    "pay_slips": {"pg": ("payroll", "pay_slips"), "required": False},
    "inventory": {"pg": ("products", "inventory"), "required": False},
    "suppliers": {"pg": ("products", "suppliers"), "required": False},
    "warehouses": {"pg": ("supply_chain", "warehouses"), "required": False},
    "inventory_snapshots": {"pg": ("supply_chain", "inventory_snapshots"), "required": False},
    "inbound_shipments": {"pg": ("supply_chain", "shipments"), "required": False},
    "work_orders": {"pg": ("manufacture", "work_orders"), "required": False},
    "production_lines": {"pg": ("manufacture", "production_lines"), "required": False},
}

DATE_COLUMNS: dict[str, tuple[str, ...]] = {
    "orders": ("order_date",),
    "sales_returns": ("return_date",),
    "sales_shipments": ("shipped_date", "delivered_date"),
    "customers": ("registration_date",),
    "ads_spend": ("spend_date",),
    "campaigns": ("start_date", "end_date"),
    "email_clicks": ("sent_date",),
    "finance_expenses": ("expense_date",),
    "attendance": ("attendance_date", "check_in", "check_out"),
    "salary_history": ("payment_date",),
    "pay_slips": ("payment_date",),
    "inventory_snapshots": ("snapshot_date",),
    "inbound_shipments": ("shipped_date", "arrival_date"),
    "work_orders": ("start_timestamp", "end_timestamp"),
}


@dataclass(frozen=True)
class LoadMessage:
    """A safe table-load message suitable for a notebook or validation log."""

    table_key: str
    severity: str
    message: str


def create_postgres_engine(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    sslmode: str = "require",
) -> Engine:
    """Create a PostgreSQL SQLAlchemy engine without exposing credentials in code."""
    safe_user = quote_plus(str(user))
    safe_password = quote_plus(str(password))
    url = (
        f"postgresql+psycopg2://{safe_user}:{safe_password}@{host}:"
        f"{int(port)}/{database}?sslmode={sslmode}"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def test_database_connection(engine: Engine) -> dict[str, str]:
    """Return a minimal connection status record without printing connection secrets."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database(), current_user"))
        database, user = result.one()
    return {"status": "connected", "database": str(database), "user": str(user)}


def _read_postgres_table(engine: Engine, schema: str, table_name: str) -> pd.DataFrame:
    """Read a mapped PostgreSQL table using quoted schema and table identifiers."""
    query = text(f'SELECT * FROM "{schema}"."{table_name}"')
    return pd.read_sql_query(query, engine)


def _is_hashable(value: Any) -> bool:
    try:
        hash(value)
        return True
    except TypeError:
        return False


def _duplicate_safe_value(value: Any) -> Any:
    """Create a temporary hashable duplicate key for JSON-like PostgreSQL values."""
    if _is_hashable(value):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, sort_keys=True, default=str)
        except TypeError:
            return repr(value)
    return repr(value)


def safe_drop_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate records while preserving JSONB/dictionary values in output."""
    if frame.empty:
        return frame.copy()
    try:
        return frame.drop_duplicates().copy()
    except TypeError:
        key_frame = frame.copy()
        for column in key_frame.columns:
            series = key_frame[column]
            if series.dtype == "object":
                sample = series.dropna().head(100)
                if not sample.empty and not sample.map(_is_hashable).all():
                    key_frame[column] = series.map(_duplicate_safe_value)
        return frame.loc[~key_frame.duplicated()].copy()


def clean_tables(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Standardise configured date fields and safely remove duplicate records."""
    cleaned: dict[str, pd.DataFrame] = {}
    for key, frame in data.items():
        out = frame.copy()
        for column in DATE_COLUMNS.get(key, ()):
            if column in out.columns:
                out[column] = pd.to_datetime(out[column], errors="coerce")
        cleaned[key] = safe_drop_duplicates(out)
    return cleaned


def load_tables_from_postgres(
    engine: Engine,
    table_keys: Iterable[str] | None = None,
) -> tuple[dict[str, pd.DataFrame], list[LoadMessage]]:
    """Load available mapped tables and return non-fatal messages for unavailable tables."""
    requested = list(table_keys) if table_keys is not None else list(TABLE_SPECS)
    data: dict[str, pd.DataFrame] = {}
    messages: list[LoadMessage] = []

    for key in requested:
        if key not in TABLE_SPECS:
            messages.append(LoadMessage(key, "warning", "Table key is not mapped in TABLE_SPECS."))
            continue
        spec = TABLE_SPECS[key]
        schema, table_name = spec["pg"]
        try:
            data[key] = _read_postgres_table(engine, schema, table_name)
        except Exception as exc:  # Project is designed to continue when optional domains are absent.
            severity = "error" if spec.get("required", False) else "warning"
            messages.append(LoadMessage(key, severity, f"Unable to load {schema}.{table_name}: {exc}"))
    return clean_tables(data), messages


def validate_required_tables(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return a required-table validation table for governance and reporting evidence."""
    rows: list[dict[str, Any]] = []
    for key, spec in TABLE_SPECS.items():
        if not spec.get("required", False):
            continue
        schema, table_name = spec["pg"]
        frame = data.get(key)
        rows.append(
            {
                "table_key": key,
                "database_table": f"{schema}.{table_name}",
                "status": "Available" if frame is not None and not frame.empty else "Missing or empty",
                "row_count": int(len(frame)) if frame is not None else 0,
            }
        )
    return pd.DataFrame(rows)


def data_quality_profile(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Summarise table availability, row counts, duplicate removal, and missing-cell rates."""
    rows: list[dict[str, Any]] = []
    for key, frame in sorted(data.items()):
        cells = max(frame.shape[0] * frame.shape[1], 1)
        missing_rate = float(frame.isna().sum().sum() / cells * 100) if not frame.empty else 0.0
        rows.append(
            {
                "table_key": key,
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "missing_cell_rate_pct": round(missing_rate, 2),
                "duplicate_rows_after_cleaning": int(len(frame) - len(safe_drop_duplicates(frame))),
            }
        )
    return pd.DataFrame(rows)


def table(data: dict[str, pd.DataFrame], key: str) -> pd.DataFrame:
    """Return a safe copy of a table or an empty frame when it is unavailable."""
    frame = data.get(key)
    return frame.copy() if frame is not None else pd.DataFrame()


def safe_divide(numerator: pd.Series | float | int, denominator: pd.Series | float | int) -> Any:
    """Divide safely, replacing zero denominators with NaN rather than infinity."""
    if isinstance(denominator, pd.Series):
        return numerator / denominator.replace(0, np.nan)
    return np.nan if pd.isna(denominator) or denominator == 0 else numerator / denominator


def make_product_dimension(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build a product-category-brand dimension from mapped product tables."""
    products = table(data, "products")
    if products.empty:
        return products
    dimension = products.copy()
    brands = table(data, "brand")
    categories = table(data, "category")
    if not brands.empty and {"brand_id"}.issubset(dimension.columns) and "brand_id" in brands.columns:
        dimension = dimension.merge(brands, on="brand_id", how="left")
    if not categories.empty and "category_id" in dimension.columns and "category_id" in categories.columns:
        dimension = dimension.merge(categories, on="category_id", how="left")
    return dimension


def build_sales_fact(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build the central fact table used for sales, profitability, trend, and RFM analysis."""
    orders = table(data, "orders")
    items = table(data, "order_items")
    if orders.empty or items.empty:
        return pd.DataFrame()

    if "order_status" in orders.columns:
        orders = orders.loc[orders["order_status"].isin(VALID_ORDER_STATUSES)].copy()
    order_fields = [
        column
        for column in [
            "order_id", "cust_id", "store_id", "order_date", "order_status", "gross_total",
            "discount_amount", "net_total", "payment_mode_id",
        ]
        if column in orders.columns
    ]
    orders = orders[order_fields].rename(columns={"discount_amount": "order_discount_amount"})
    items = items.rename(columns={"discount_amount": "item_discount_amount"})
    fact = items.merge(orders, on="order_id", how="inner")

    product_dimension = make_product_dimension(data)
    if not product_dimension.empty and "prod_id" in fact.columns and "product_id" in product_dimension.columns:
        fact = fact.merge(product_dimension, left_on="prod_id", right_on="product_id", how="left")

    stores = table(data, "stores")
    regions = table(data, "region")
    if not stores.empty and "store_id" in fact.columns and "store_id" in stores.columns:
        fact = fact.merge(stores, on="store_id", how="left", suffixes=("", "_store"))
    if not regions.empty and "region_id" in fact.columns and "region_id" in regions.columns:
        fact = fact.merge(regions, on="region_id", how="left", suffixes=("", "_region"))

    for field in ("quantity", "net_amount", "cost_price", "gross_amount", "item_discount_amount"):
        if field in fact.columns:
            fact[field] = pd.to_numeric(fact[field], errors="coerce").fillna(0)
    fact["cost"] = fact.get("quantity", 0) * fact.get("cost_price", 0)
    fact["profit"] = fact.get("net_amount", 0) - fact["cost"]
    fact["profit_margin_pct"] = safe_divide(fact["profit"], fact.get("net_amount", pd.Series(np.nan, index=fact.index))) * 100
    if "order_date" in fact.columns:
        fact["order_date"] = pd.to_datetime(fact["order_date"], errors="coerce")
        fact["month"] = fact["order_date"].dt.to_period("M").dt.to_timestamp()
    return fact


def calculate_executive_kpis(fact: pd.DataFrame) -> dict[str, float]:
    """Calculate revenue, profit, margin, valid orders, and average order value."""
    if fact.empty:
        return {"revenue": 0.0, "profit": 0.0, "margin_pct": np.nan, "orders": 0, "aov": np.nan}
    revenue = float(fact["net_amount"].sum())
    profit = float(fact["profit"].sum())
    order_count = int(fact["order_id"].nunique()) if "order_id" in fact.columns else 0
    return {
        "revenue": revenue,
        "profit": profit,
        "margin_pct": float(safe_divide(profit, revenue) * 100),
        "orders": order_count,
        "aov": float(safe_divide(revenue, order_count)),
    }


def monthly_sales_summary(fact: pd.DataFrame) -> pd.DataFrame:
    """Return monthly revenue, profit, order count, and profit-margin trend."""
    if fact.empty or "month" not in fact.columns:
        return pd.DataFrame(columns=["month", "revenue", "profit", "orders", "margin_pct"])
    summary = (
        fact.groupby("month", as_index=False)
        .agg(revenue=("net_amount", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        .sort_values("month")
    )
    summary["margin_pct"] = safe_divide(summary["profit"], summary["revenue"]) * 100
    return summary


def rfm_segmentation(fact: pd.DataFrame) -> pd.DataFrame:
    """Create explainable RFM customer segments and a CLV proxy from observed transactions."""
    if fact.empty or not {"cust_id", "order_date", "order_id", "net_amount"}.issubset(fact.columns):
        return pd.DataFrame()
    max_date = pd.to_datetime(fact["order_date"], errors="coerce").max()
    customer = (
        fact.groupby("cust_id", as_index=False)
        .agg(last_order=("order_date", "max"), frequency=("order_id", "nunique"), monetary=("net_amount", "sum"))
    )
    customer["recency_days"] = (max_date - pd.to_datetime(customer["last_order"], errors="coerce")).dt.days
    customer["r_score"] = (1 - customer["recency_days"].rank(method="first", pct=True)) * 5
    customer["f_score"] = customer["frequency"].rank(method="first", pct=True) * 5
    customer["m_score"] = customer["monetary"].rank(method="first", pct=True) * 5
    customer[["r_score", "f_score", "m_score"]] = customer[["r_score", "f_score", "m_score"]].round().clip(1, 5).astype(int)
    customer["rfm_total"] = customer[["r_score", "f_score", "m_score"]].sum(axis=1)
    conditions = [
        (customer["r_score"] >= 4) & (customer["f_score"] >= 4) & (customer["m_score"] >= 4),
        (customer["r_score"] >= 3) & (customer["f_score"] >= 3),
        (customer["r_score"] <= 2) & (customer["m_score"] >= 4),
        (customer["r_score"] <= 2) & (customer["f_score"] <= 2),
    ]
    customer["segment"] = np.select(conditions, ["Champions", "Loyal", "At-Risk Valuable", "Needs Attention"], default="Others")
    max_frequency = max(float(customer["frequency"].max()), 1.0)
    customer["clv_proxy"] = customer["monetary"] * (1 + customer["frequency"] / max_frequency)
    return customer.sort_values("monetary", ascending=False).reset_index(drop=True)


def build_rule_based_insights(fact: pd.DataFrame) -> list[str]:
    """Generate transparent, advisory management prompts from sales and customer metrics.

    The function does not use machine learning or generative AI. It creates explainable
    recommendations based on threshold and comparative KPI conditions.
    """
    if fact.empty:
        return ["No valid sales fact records are available for AI-assisted insight generation."]

    insights: list[str] = []
    kpis = calculate_executive_kpis(fact)
    if pd.notna(kpis["margin_pct"]) and kpis["margin_pct"] < 20:
        insights.append("Profit margin is below the 20% review threshold; examine cost, discount, refund, and product-mix drivers.")
    else:
        insights.append("Revenue and profit metrics are available for management review; compare product and regional contribution before action planning.")

    if "category_name" in fact.columns:
        category = fact.groupby("category_name", as_index=False).agg(revenue=("net_amount", "sum"), profit=("profit", "sum"))
        category["margin_pct"] = safe_divide(category["profit"], category["revenue"]) * 100
        weakest = category.sort_values("margin_pct").head(1)
        if not weakest.empty:
            row = weakest.iloc[0]
            insights.append(f"Review category '{row['category_name']}' because it has the lowest observed profit margin in the selected context.")

    rfm = rfm_segmentation(fact)
    if not rfm.empty:
        at_risk = int((rfm["segment"] == "At-Risk Valuable").sum())
        if at_risk:
            insights.append(f"{at_risk} high-value customer(s) are classified as At-Risk Valuable; consider targeted retention or service-recovery review.")
    return insights
