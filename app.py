"""AI-Assisted Cross-Functional BI Dashboard — Neon PostgreSQL Only.

Standalone Streamlit deployment file.
Runtime data comes only from Neon PostgreSQL through SQLAlchemy and pandas.
No CSV reader, ZIP uploader, or import from an external local project module is used.
"""
from __future__ import annotations

from collections.abc import Iterable
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="AI-Assisted Cross-Functional BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

VALID_ORDER_STATUSES = {"Delivered", "Shipped", "Out for Delivery", "Processing"}

# Each entry maps an analytical table key to a Neon PostgreSQL schema and table.
# Optional tables make the dashboard resilient when the Neon project does not yet contain every domain.
TABLE_SPECS: dict[str, dict[str, Any]] = {
    # Core sales/customer/product tables
    "orders": {"pg": ("sales", "orders"), "required": True},
    "order_items": {"pg": ("sales", "order_items"), "required": True},
    "sales_payments": {"pg": ("sales", "payments"), "required": False},
    "sales_returns": {"pg": ("sales", "returns"), "required": False},
    "sales_shipments": {"pg": ("sales", "shipments"), "required": False},
    "products": {"pg": ("products", "products"), "required": True},
    "inventory": {"pg": ("products", "inventory"), "required": False},
    "suppliers": {"pg": ("products", "suppliers"), "required": False},
    "promotions": {"pg": ("products", "promotions"), "required": False},
    "brand": {"pg": ("core", "dim_brand"), "required": True},
    "category": {"pg": ("core", "dim_category"), "required": True},
    "region": {"pg": ("core", "dim_region"), "required": False},
    "department": {"pg": ("core", "dim_department"), "required": False},
    "expense_category": {"pg": ("core", "dim_expense_category"), "required": False},
    "stores": {"pg": ("stores", "stores"), "required": False},
    "store_employees": {"pg": ("stores", "employees"), "required": False},
    "store_expenses": {"pg": ("stores", "expenses"), "required": False},
    "customers": {"pg": ("customers", "customers"), "required": True},
    "reviews": {"pg": ("customers", "reviews"), "required": False},
    "loyalty_points": {"pg": ("customers", "loyalty_points"), "required": False},
    "wallets": {"pg": ("customers", "wallets"), "required": False},
    "loyalty_members": {"pg": ("loyalty", "members"), "required": False},
    "loyalty_tiers": {"pg": ("loyalty", "tiers"), "required": False},
    "loyalty_redemptions": {"pg": ("loyalty", "redemptions"), "required": False},
    "support_tickets": {"pg": ("support", "tickets"), "required": False},
    "calls": {"pg": ("call_center", "calls"), "required": False},
    "transcripts": {"pg": ("call_center", "transcripts"), "required": False},
    # Marketing
    "campaigns": {"pg": ("marketing", "campaigns"), "required": False},
    "ads_spend": {"pg": ("marketing", "ads_spend"), "required": False},
    "email_clicks": {"pg": ("marketing", "email_clicks"), "required": False},
    # Finance
    "finance_expenses": {"pg": ("finance", "expenses"), "required": False},
    "finance_payments": {"pg": ("finance", "payments"), "required": False},
    "finance_payment_modes": {"pg": ("finance", "payment_modes"), "required": False},
    "revenue_summary": {"pg": ("finance", "revenue_summary"), "required": False},
    "refund_log": {"pg": ("audit", "refund_log"), "required": False},
    "refund_failures": {"pg": ("audit", "refund_failures"), "required": False},
    # HR and payroll
    "attendance": {"pg": ("hr", "attendance"), "required": False},
    "salary_history": {"pg": ("hr", "salary_history"), "required": False},
    "pay_slips": {"pg": ("payroll", "pay_slips"), "required": False},
    # Operations and logistics
    "warehouses": {"pg": ("supply_chain", "warehouses"), "required": False},
    "inbound_shipments": {"pg": ("supply_chain", "shipments"), "required": False},
    "inventory_snapshots": {"pg": ("supply_chain", "inventory_snapshots"), "required": False},
    "work_orders": {"pg": ("manufacture", "work_orders"), "required": False},
    "production_lines": {"pg": ("manufacture", "production_lines"), "required": False},
    # Optional website/technical operations data (large tables; loaded only when requested)
    "page_views": {"pg": ("web_events", "page_views"), "required": False, "optional_large": True},
    "web_events": {"pg": ("web_events", "events"), "required": False, "optional_large": True},
    "api_requests": {"pg": ("audit", "api_requests"), "required": False},
    "application_logs": {"pg": ("audit", "application_logs"), "required": False},
    "procedure_calls": {"pg": ("audit", "procedure_calls"), "required": False},
}

DATE_COLUMNS: dict[str, list[str]] = {
    "orders": ["order_date"],
    "sales_payments": ["payment_date"],
    "sales_returns": ["return_date"],
    "sales_shipments": ["shipped_date", "delivered_date"],
    "customers": ["registration_date", "tier_updated_at"],
    "reviews": ["review_date"],
    "loyalty_points": ["date_earned"],
    "wallets": ["last_updated"],
    "loyalty_members": ["join_date"],
    "loyalty_redemptions": ["redemption_date"],
    "support_tickets": ["created_date", "resolved_date"],
    "calls": ["call_start_time"],
    "campaigns": ["start_date", "end_date"],
    "ads_spend": ["spend_date"],
    "email_clicks": ["sent_date"],
    "promotions": ["start_date", "end_date"],
    "finance_expenses": ["expense_date"],
    "finance_payments": ["refunded_at"],
    "revenue_summary": ["summary_date"],
    "refund_log": ["refunded_at"],
    "refund_failures": ["failed_at"],
    "attendance": ["attendance_date", "check_in", "check_out"],
    "salary_history": ["payment_date"],
    "pay_slips": ["payment_date"],
    "inbound_shipments": ["shipped_date", "arrival_date"],
    "inventory_snapshots": ["snapshot_date"],
    "work_orders": ["start_timestamp", "end_timestamp"],
    "page_views": ["view_timestamp"],
    "web_events": ["event_timestamp"],
    "api_requests": ["timestamp"],
    "application_logs": ["timestamp"],
    "procedure_calls": ["called_at"],
}


def create_postgres_engine(host: str, port: int, database: str, user: str, password: str, sslmode: str = "require"):
    """Create a SQLAlchemy PostgreSQL connection engine."""
    safe_user = quote_plus(str(user))
    safe_password = quote_plus(str(password))
    url = f"postgresql+psycopg2://{safe_user}:{safe_password}@{host}:{int(port)}/{database}?sslmode={sslmode}"
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def _read_postgres_table(engine, schema: str, table: str) -> pd.DataFrame:
    query = text(f'SELECT * FROM "{schema}"."{table}"')
    return pd.read_sql_query(query, engine)



def _selected_specs(include_web_events: bool) -> dict[str, dict[str, Any]]:
    return {
        key: spec
        for key, spec in TABLE_SPECS.items()
        if include_web_events or not spec.get("optional_large", False)
    }


def _is_hashable(value: Any) -> bool:
    """Return whether a value can be used in pandas duplicate detection."""
    try:
        hash(value)
        return True
    except TypeError:
        return False


def _duplicate_safe_value(value: Any) -> Any:
    """Convert nested JSON-like values to a stable representation for duplicate checks only."""
    if _is_hashable(value):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, sort_keys=True, default=str)
        except TypeError:
            return repr(value)
    return repr(value)


def _safe_drop_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows without changing JSONB/dict values returned by PostgreSQL.

    PostgreSQL JSON/JSONB columns are read by psycopg2 as Python dictionaries.
    Pandas cannot hash dictionaries when calling ``drop_duplicates`` directly.
    A temporary copy is therefore used only to create hashable duplicate keys,
    while the original dataframe values are retained in the output.
    """
    if frame.empty:
        return frame.copy()
    try:
        return frame.drop_duplicates()
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
    """Standardise date fields and remove duplicate rows safely."""
    cleaned = {name: frame.copy() for name, frame in data.items()}
    for table_name, columns in DATE_COLUMNS.items():
        frame = cleaned.get(table_name)
        if frame is None:
            continue
        for column in columns:
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
        cleaned[table_name] = _safe_drop_duplicates(frame)
    return cleaned



def load_tables_from_postgres(engine, include_web_events: bool = False) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Load all available mapped tables from PostgreSQL."""
    data: dict[str, pd.DataFrame] = {}
    messages: list[str] = []
    for key, spec in _selected_specs(include_web_events).items():
        schema, table = spec["pg"]
        try:
            data[key] = _read_postgres_table(engine, schema, table)
        except Exception as exc:  # lets the UI work with the available domains
            prefix = "Required" if spec.get("required", False) else "Optional"
            messages.append(f"{prefix} table unavailable — {schema}.{table}: {exc}")
    return clean_tables(data), messages


def table(data: dict[str, pd.DataFrame], name: str) -> pd.DataFrame:
    """Return a table or an empty DataFrame when not available."""
    return data.get(name, pd.DataFrame()).copy()


def safe_divide(numerator: pd.Series | float | int, denominator: pd.Series | float | int):
    if isinstance(denominator, pd.Series):
        return numerator / denominator.replace(0, np.nan)
    return np.nan if pd.isna(denominator) or denominator == 0 else numerator / denominator


def filter_by_year(frame: pd.DataFrame, date_columns: Iterable[str], years: list[int] | None) -> pd.DataFrame:
    if frame.empty or not years:
        return frame.copy()
    for date_col in date_columns:
        if date_col in frame.columns:
            parsed = pd.to_datetime(frame[date_col], errors="coerce")
            return frame.loc[parsed.dt.year.isin(years)].copy()
    return frame.copy()


def make_product_dimension(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    products = table(data, "products")
    if products.empty:
        return products
    brands = table(data, "brand")
    categories = table(data, "category")
    dim = products.copy()
    if not brands.empty and "brand_id" in dim.columns and "brand_id" in brands.columns:
        dim = dim.merge(brands, on="brand_id", how="left")
    if not categories.empty and "category_id" in dim.columns and "category_id" in categories.columns:
        dim = dim.merge(categories, on="category_id", how="left")
    return dim


def make_sales_fact(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build the central Sales Fact table from valid orders, items, product, store and region dimensions."""
    orders = table(data, "orders")
    items = table(data, "order_items")
    if orders.empty or items.empty:
        return pd.DataFrame()

    product_dim = make_product_dimension(data)
    orders = orders.copy()
    items = items.copy()
    if "order_status" in orders.columns:
        orders = orders.loc[orders["order_status"].isin(VALID_ORDER_STATUSES)].copy()

    order_fields = [column for column in ["order_id", "cust_id", "store_id", "order_date", "order_status", "gross_total", "discount_amount", "net_total", "payment_mode_id"] if column in orders.columns]
    orders = orders[order_fields].rename(columns={"discount_amount": "order_discount_amount"})
    items = items.rename(columns={"discount_amount": "item_discount_amount"})
    fact = items.merge(orders, on="order_id", how="inner")

    if not product_dim.empty and "prod_id" in fact.columns and "product_id" in product_dim.columns:
        fact = fact.merge(product_dim, left_on="prod_id", right_on="product_id", how="left")

    stores = table(data, "stores")
    regions = table(data, "region")
    if not stores.empty and "store_id" in fact.columns and "store_id" in stores.columns:
        fact = fact.merge(stores, on="store_id", how="left", suffixes=("", "_store"))
    if not regions.empty and "region_id" in fact.columns and "region_id" in regions.columns:
        fact = fact.merge(regions, on="region_id", how="left", suffixes=("", "_region"))

    for field in ["quantity", "net_amount", "cost_price", "gross_amount", "item_discount_amount"]:
        if field in fact.columns:
            fact[field] = pd.to_numeric(fact[field], errors="coerce").fillna(0)
    fact["cost"] = fact.get("quantity", 0) * fact.get("cost_price", 0)
    fact["profit"] = fact.get("net_amount", 0) - fact["cost"]
    fact["profit_margin_pct"] = safe_divide(fact["profit"], fact.get("net_amount", pd.Series(np.nan, index=fact.index))) * 100
    if "order_date" in fact.columns:
        fact["month"] = pd.to_datetime(fact["order_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    return fact


def apply_sales_filters(
    fact: pd.DataFrame,
    years: list[int] | None = None,
    categories: list[str] | None = None,
    products: list[str] | None = None,
    regions: list[str] | None = None,
    states: list[str] | None = None,
    stores: list[str] | None = None,
) -> pd.DataFrame:
    filtered = fact.copy()
    if filtered.empty:
        return filtered
    if years and "order_date" in filtered.columns:
        filtered = filtered.loc[pd.to_datetime(filtered["order_date"], errors="coerce").dt.year.isin(years)]
    mappings = [
        ("category_name", categories),
        ("product_name", products),
        ("region_name", regions),
        ("state", states),
        ("store_name", stores),
    ]
    for column, selected in mappings:
        if selected and column in filtered.columns:
            filtered = filtered.loc[filtered[column].isin(selected)]
    return filtered.copy()


def executive_kpis(fact: pd.DataFrame) -> dict[str, float]:
    if fact.empty:
        return {"revenue": 0.0, "profit": 0.0, "margin": np.nan, "orders": 0, "aov": np.nan}
    revenue = float(fact["net_amount"].sum())
    profit = float(fact["profit"].sum())
    orders = int(fact["order_id"].nunique())
    return {
        "revenue": revenue,
        "profit": profit,
        "margin": safe_divide(profit, revenue) * 100,
        "orders": orders,
        "aov": safe_divide(revenue, orders),
    }


def monthly_sales_summary(fact: pd.DataFrame) -> pd.DataFrame:
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
    if fact.empty or "cust_id" not in fact.columns:
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
    labels = ["Champions", "Loyal", "At-Risk Valuable", "Needs Attention"]
    customer["segment"] = np.select(conditions, labels, default="Others")
    max_frequency = max(float(customer["frequency"].max()), 1.0)
    customer["clv_proxy"] = customer["monetary"] * (1 + customer["frequency"] / max_frequency)
    return customer


def sales_customer_outputs(data: dict[str, pd.DataFrame], fact: pd.DataFrame) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {"monthly": monthly_sales_summary(fact), "rfm": rfm_segmentation(fact)}
    if fact.empty:
        return outputs
    outputs["products"] = (
        fact.groupby("product_name", as_index=False)
        .agg(revenue=("net_amount", "sum"), profit=("profit", "sum"), units=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
    )
    if "category_name" in fact.columns:
        category = fact.groupby("category_name", as_index=False).agg(revenue=("net_amount", "sum"), profit=("profit", "sum"))
        category["margin_pct"] = safe_divide(category["profit"], category["revenue"]) * 100
        outputs["categories"] = category.sort_values("revenue", ascending=False)
    if "region_name" in fact.columns:
        regional = fact.groupby("region_name", as_index=False).agg(revenue=("net_amount", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        regional["margin_pct"] = safe_divide(regional["profit"], regional["revenue"]) * 100
        outputs["regions"] = regional.sort_values("revenue", ascending=False)
    # Returns by reason and category
    returns = table(data, "sales_returns")
    if not returns.empty:
        enriched = returns.merge(fact[["order_id", "prod_id", "category_name", "product_name"]].drop_duplicates(), on=["order_id", "prod_id"], how="left")
        outputs["return_reasons"] = enriched.groupby("reason", as_index=False).agg(refund_value=("refund_amount", "sum"), return_count=("return_id", "nunique")).sort_values("refund_value", ascending=False)
    reviews = table(data, "reviews")
    if not reviews.empty:
        outputs["reviews"] = reviews.groupby("rating", as_index=False).size().rename(columns={"size": "review_count"}).sort_values("rating")
    loyalty = table(data, "loyalty_members")
    tiers = table(data, "loyalty_tiers")
    if not loyalty.empty:
        if not tiers.empty:
            loyalty = loyalty.merge(tiers[["tier_id", "tier_name"]], on="tier_id", how="left")
        outputs["loyalty"] = loyalty.groupby(loyalty.get("tier_name", loyalty.get("tier_id")), as_index=False).agg(members=("customer_id", "nunique"), points_balance=("points_balance", "sum"))
        outputs["loyalty"].columns = ["tier", "members", "points_balance"]
    tickets = table(data, "support_tickets")
    if not tickets.empty:
        tickets["resolution_hours"] = (pd.to_datetime(tickets.get("resolved_date"), errors="coerce") - pd.to_datetime(tickets.get("created_date"), errors="coerce")).dt.total_seconds() / 3600
        outputs["tickets"] = tickets.groupby("category", as_index=False).agg(ticket_count=("ticket_id", "nunique"), avg_resolution_hours=("resolution_hours", "mean")).sort_values("ticket_count", ascending=False)
    return outputs


def marketing_outputs(data: dict[str, pd.DataFrame], fact: pd.DataFrame, years: list[int] | None = None, platforms: list[str] | None = None) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    spend = filter_by_year(table(data, "ads_spend"), ["spend_date"], years)
    campaigns = table(data, "campaigns")
    emails = filter_by_year(table(data, "email_clicks"), ["sent_date"], years)
    if platforms and "platform" in spend.columns:
        spend = spend.loc[spend["platform"].isin(platforms)].copy()
    if not spend.empty:
        outputs["platform_spend"] = spend.groupby("platform", as_index=False).agg(spend=("amount", "sum")).sort_values("spend", ascending=False)
        spend["month"] = pd.to_datetime(spend["spend_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
        outputs["monthly_spend"] = spend.groupby("month", as_index=False).agg(marketing_spend=("amount", "sum"))
        campaign_spend = spend.groupby("campaign_id", as_index=False).agg(actual_spend=("amount", "sum"))
        if not campaigns.empty:
            campaign_spend = campaign_spend.merge(campaigns[[c for c in ["campaign_id", "campaign_name", "budget", "start_date", "end_date"] if c in campaigns.columns]], on="campaign_id", how="left")
            campaign_spend["budget_variance"] = campaign_spend.get("budget", 0) - campaign_spend["actual_spend"]
            campaign_spend["spend_to_budget_pct"] = safe_divide(campaign_spend["actual_spend"], campaign_spend.get("budget", pd.Series(np.nan, index=campaign_spend.index))) * 100
        outputs["campaign_pacing"] = campaign_spend.sort_values("actual_spend", ascending=False)
    if not emails.empty:
        email = emails.copy()
        for col in ["emails_sent", "emails_opened", "emails_clicked"]:
            email[col] = pd.to_numeric(email[col], errors="coerce").fillna(0)
        if not campaigns.empty:
            email = email.merge(campaigns[[c for c in ["campaign_id", "campaign_name"] if c in campaigns.columns]], on="campaign_id", how="left")
        outputs["email_performance"] = email.groupby("campaign_name" if "campaign_name" in email.columns else "campaign_id", as_index=False).agg(sent=("emails_sent", "sum"), opened=("emails_opened", "sum"), clicked=("emails_clicked", "sum"))
        outputs["email_performance"]["open_rate_pct"] = safe_divide(outputs["email_performance"]["opened"], outputs["email_performance"]["sent"]) * 100
        outputs["email_performance"]["ctr_pct"] = safe_divide(outputs["email_performance"]["clicked"], outputs["email_performance"]["sent"]) * 100
        outputs["email_performance"]["ctor_pct"] = safe_divide(outputs["email_performance"]["clicked"], outputs["email_performance"]["opened"]) * 100
    monthly_sales = monthly_sales_summary(fact)
    monthly_spend = outputs.get("monthly_spend", pd.DataFrame(columns=["month", "marketing_spend"]))
    if not monthly_sales.empty:
        outputs["spend_sales_trend"] = monthly_sales.merge(monthly_spend, on="month", how="left").fillna({"marketing_spend": 0})
        outputs["spend_sales_trend"]["revenue_per_spend"] = safe_divide(outputs["spend_sales_trend"]["revenue"], outputs["spend_sales_trend"]["marketing_spend"])
    page_views = filter_by_year(table(data, "page_views"), ["view_timestamp"], years)
    if not page_views.empty:
        session = page_views.groupby("session_id", as_index=False).agg(pages=("view_id", "nunique"), customer_id=("customer_id", "first"))
        outputs["web_engagement"] = pd.DataFrame({
            "identified_sessions": [int(session["customer_id"].notna().sum())],
            "anonymous_sessions": [int(session["customer_id"].isna().sum())],
            "avg_pages_per_session": [float(session["pages"].mean())],
            "single_page_share_pct": [float((session["pages"] == 1).mean() * 100)],
        })
    return outputs


def finance_outputs(data: dict[str, pd.DataFrame], fact: pd.DataFrame, years: list[int] | None = None) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    expenses = filter_by_year(table(data, "finance_expenses"), ["expense_date"], years)
    expense_categories = table(data, "expense_category")
    if not expenses.empty:
        expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0)
        if not expense_categories.empty and "exp_cat_id" in expenses.columns:
            expenses = expenses.merge(expense_categories, on="exp_cat_id", how="left")
        category_col = "category_name" if "category_name" in expenses.columns else "exp_cat_id"
        outputs["expense_categories"] = expenses.groupby(category_col, as_index=False).agg(expense=("amount", "sum")).sort_values("expense", ascending=False)
        expenses["month"] = pd.to_datetime(expenses["expense_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
        outputs["monthly_expenses"] = expenses.groupby("month", as_index=False).agg(opex=("amount", "sum"))
    revenue = monthly_sales_summary(fact)
    if not revenue.empty:
        pl = revenue.merge(outputs.get("monthly_expenses", pd.DataFrame(columns=["month", "opex"])), on="month", how="left").fillna({"opex": 0})
        pl["ebitda_proxy"] = pl["profit"] - pl["opex"]
        pl["cost_to_revenue_pct"] = safe_divide(pl["opex"], pl["revenue"]) * 100
        outputs["pnl"] = pl
    payments = table(data, "finance_payments")
    if not payments.empty:
        status_col = "status" if "status" in payments.columns else payments.columns[-1]
        outputs["payment_status"] = payments.groupby(status_col, as_index=False).agg(payment_count=("payment_id", "nunique"), amount=("amount", "sum"))
        refunds = payments.loc[payments.get("refunded_at").notna()] if "refunded_at" in payments.columns else pd.DataFrame()
        if not refunds.empty:
            reason_col = "refund_reason" if "refund_reason" in refunds.columns else status_col
            outputs["refund_reasons"] = refunds.groupby(reason_col, as_index=False).agg(refund_count=("payment_id", "nunique"), refund_value=("amount", "sum")).sort_values("refund_value", ascending=False)
    refund_log = filter_by_year(table(data, "refund_log"), ["refunded_at"], years)
    if not refund_log.empty:
        outputs["refund_log"] = refund_log.groupby("reason", as_index=False).agg(refund_count=("refund_id", "nunique"), refund_value=("amount", "sum")).sort_values("refund_value", ascending=False)
    return outputs


def hr_outputs(data: dict[str, pd.DataFrame], revenue_total: float, years: list[int] | None = None) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    employees = table(data, "store_employees")
    departments = table(data, "department")
    if not employees.empty:
        if not departments.empty and "dept_id" in employees.columns:
            employees = employees.merge(departments, on="dept_id", how="left")
        dept_col = "dept_name" if "dept_name" in employees.columns else "dept_id"
        outputs["headcount"] = employees.groupby(dept_col, as_index=False).agg(headcount=("employee_id", "nunique"), avg_salary=("salary", "mean")).sort_values("headcount", ascending=False)
        role_col = "role" if "role" in employees.columns else dept_col
        outputs["role_salary"] = employees.groupby(role_col, as_index=False).agg(headcount=("employee_id", "nunique"), avg_salary=("salary", "mean")).sort_values("avg_salary", ascending=False)
        outputs["revenue_per_employee"] = pd.DataFrame({"revenue_per_employee": [safe_divide(revenue_total, employees["employee_id"].nunique())]})
    pay_slips = filter_by_year(table(data, "pay_slips"), ["payment_date"], years)
    if not pay_slips.empty:
        for col in ["gross_salary", "net_salary", "pf", "professional_tax", "income_tax"]:
            if col in pay_slips.columns:
                pay_slips[col] = pd.to_numeric(pay_slips[col], errors="coerce").fillna(0)
        pay_slips["month"] = pd.to_datetime(pay_slips["payment_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
        outputs["payroll_monthly"] = pay_slips.groupby("month", as_index=False).agg(gross_payroll=("gross_salary", "sum"), net_payroll=("net_salary", "sum"), deductions=("pf", "sum"))
        if "professional_tax" in pay_slips.columns:
            outputs["payroll_monthly"]["deductions"] += pay_slips.groupby("month")["professional_tax"].sum().values
        if "income_tax" in pay_slips.columns:
            outputs["payroll_monthly"]["deductions"] += pay_slips.groupby("month")["income_tax"].sum().values
        outputs["payroll_monthly"]["deduction_rate_pct"] = safe_divide(outputs["payroll_monthly"]["deductions"], outputs["payroll_monthly"]["gross_payroll"]) * 100
    attendance = filter_by_year(table(data, "attendance"), ["attendance_date"], years)
    if not attendance.empty:
        check_in = pd.to_datetime(attendance.get("check_in"), errors="coerce")
        check_out = pd.to_datetime(attendance.get("check_out"), errors="coerce")
        attendance["worked_hours"] = (check_out - check_in).dt.total_seconds() / 3600
        attendance["missing_checkout"] = check_out.isna()
        attendance_enriched = attendance.merge(employees[[c for c in ["employee_id", "dept_name", "dept_id"] if c in employees.columns]], on="employee_id", how="left") if not employees.empty else attendance
        group_col = "dept_name" if "dept_name" in attendance_enriched.columns else "dept_id" if "dept_id" in attendance_enriched.columns else "employee_id"
        outputs["attendance"] = attendance_enriched.groupby(group_col, as_index=False).agg(attendance_days=("attendance_id", "nunique"), avg_worked_hours=("worked_hours", "mean"), missing_checkout_rate=("missing_checkout", "mean"))
        outputs["attendance"]["missing_checkout_rate_pct"] = outputs["attendance"].pop("missing_checkout_rate") * 100
    salary_history = filter_by_year(table(data, "salary_history"), ["payment_date"], years)
    if not salary_history.empty:
        outputs["salary_payment_status"] = salary_history.groupby("status", as_index=False).agg(payment_count=("payment_id", "nunique"), amount=("amount", "sum"))
    return outputs


def operations_logistics_outputs(data: dict[str, pd.DataFrame], years: list[int] | None = None, shipment_statuses: list[str] | None = None, warehouse_regions: list[str] | None = None) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    products = make_product_dimension(data)
    inventory = table(data, "inventory")
    if not inventory.empty:
        inv = inventory.merge(products[[c for c in ["product_id", "product_name", "category_name", "cost_price"] if c in products.columns]], on="product_id", how="left") if not products.empty else inventory
        inv["quantity_on_hand"] = pd.to_numeric(inv["quantity_on_hand"], errors="coerce").fillna(0)
        inv["reorder_level"] = pd.to_numeric(inv["reorder_level"], errors="coerce").fillna(0)
        inv["below_reorder"] = inv["quantity_on_hand"] < inv["reorder_level"]
        inv["inventory_value"] = inv["quantity_on_hand"] * pd.to_numeric(inv.get("cost_price", 0), errors="coerce").fillna(0)
        outputs["inventory_risk"] = inv.sort_values("inventory_value", ascending=False)
        if "category_name" in inv.columns:
            outputs["inventory_by_category"] = inv.groupby("category_name", as_index=False).agg(inventory_units=("quantity_on_hand", "sum"), inventory_value=("inventory_value", "sum"), below_reorder_skus=("below_reorder", "sum"))
    outbound = filter_by_year(table(data, "sales_shipments"), ["shipped_date", "delivered_date"], years)
    if shipment_statuses and not outbound.empty and "status" in outbound.columns:
        outbound = outbound.loc[outbound["status"].isin(shipment_statuses)].copy()
    if not outbound.empty:
        outbound["delivery_days"] = (pd.to_datetime(outbound.get("delivered_date"), errors="coerce") - pd.to_datetime(outbound.get("shipped_date"), errors="coerce")).dt.total_seconds() / 86400
        outputs["outbound_status"] = outbound.groupby("status", as_index=False).agg(shipments=("shipment_id", "nunique"), avg_delivery_days=("delivery_days", "mean"))
        outputs["courier"] = outbound.groupby("courier_name", as_index=False).agg(shipments=("shipment_id", "nunique"), avg_delivery_days=("delivery_days", "mean")).sort_values("shipments", ascending=False)
    inbound = filter_by_year(table(data, "inbound_shipments"), ["shipped_date", "arrival_date"], years)
    warehouses = table(data, "warehouses")
    if not inbound.empty:
        if not warehouses.empty:
            inbound = inbound.merge(warehouses[[c for c in ["warehouse_id", "name", "region", "capacity_sqft"] if c in warehouses.columns]], on="warehouse_id", how="left")
        if warehouse_regions and "region" in inbound.columns:
            inbound = inbound.loc[inbound["region"].isin(warehouse_regions)].copy()
        suppliers = table(data, "suppliers")
        if not suppliers.empty:
            inbound = inbound.merge(suppliers[[c for c in ["supplier_id", "supplier_name"] if c in suppliers.columns]], on="supplier_id", how="left")
        inbound["lead_days"] = (pd.to_datetime(inbound.get("arrival_date"), errors="coerce") - pd.to_datetime(inbound.get("shipped_date"), errors="coerce")).dt.total_seconds() / 86400
        supplier_col = "supplier_name" if "supplier_name" in inbound.columns else "supplier_id"
        outputs["supplier_lead"] = inbound.groupby(supplier_col, as_index=False).agg(inbound_units=("quantity", "sum"), avg_lead_days=("lead_days", "mean"), shipments=("shipment_id", "nunique")).sort_values("avg_lead_days")
        if "region" in inbound.columns:
            outputs["warehouse_flow"] = inbound.groupby("region", as_index=False).agg(inbound_units=("quantity", "sum"), avg_lead_days=("lead_days", "mean"))
    work_orders = filter_by_year(table(data, "work_orders"), ["start_timestamp"], years)
    if not work_orders.empty:
        lines = table(data, "production_lines")
        if not lines.empty:
            work_orders = work_orders.merge(lines[[c for c in ["line_id", "line_name", "capacity_per_hour"] if c in lines.columns]], on="line_id", how="left")
        work_orders["yield_pct"] = safe_divide(work_orders["quantity_produced"] - work_orders["rejected_quantity"], work_orders["quantity_produced"]) * 100
        work_orders["rejection_rate_pct"] = safe_divide(work_orders["rejected_quantity"], work_orders["quantity_produced"]) * 100
        line_col = "line_name" if "line_name" in work_orders.columns else "line_id"
        outputs["production"] = work_orders.groupby(line_col, as_index=False).agg(produced=("quantity_produced", "sum"), rejected=("rejected_quantity", "sum"), rejection_rate_pct=("rejection_rate_pct", "mean"), yield_pct=("yield_pct", "mean")).sort_values("produced", ascending=False)
    api = filter_by_year(table(data, "api_requests"), ["timestamp"], years)
    if not api.empty:
        api["is_error"] = pd.to_numeric(api.get("status_code"), errors="coerce") >= 400
        outputs["api_health"] = api.groupby("endpoint", as_index=False).agg(requests=("request_id", "nunique"), error_rate_pct=("is_error", "mean"), p95_latency_ms=("response_time_ms", lambda x: np.nanpercentile(pd.to_numeric(x, errors="coerce").dropna(), 95) if pd.to_numeric(x, errors="coerce").notna().any() else np.nan))
        outputs["api_health"]["error_rate_pct"] *= 100
    return outputs


def cross_functional_outputs(data: dict[str, pd.DataFrame], fact: pd.DataFrame, years: list[int] | None = None, platforms: list[str] | None = None) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    marketing = marketing_outputs(data, fact, years, platforms)
    finance = finance_outputs(data, fact, years)
    hr = hr_outputs(data, executive_kpis(fact)["revenue"], years)
    operations = operations_logistics_outputs(data, years)
    if "spend_sales_trend" in marketing:
        outputs["marketing_sales_profit"] = marketing["spend_sales_trend"]
    if "pnl" in finance:
        outputs["profit_cost"] = finance["pnl"]
    # Link regional sales with staffing through stores and employees.
    regions = sales_customer_outputs(data, fact).get("regions", pd.DataFrame())
    employees = table(data, "store_employees")
    stores = table(data, "stores")
    region_table = table(data, "region")
    if not regions.empty and not employees.empty and not stores.empty:
        staff = employees.merge(stores[[c for c in ["store_id", "region_id"] if c in stores.columns]], on="store_id", how="left")
        if not region_table.empty:
            staff = staff.merge(region_table[[c for c in ["region_id", "region_name"] if c in region_table.columns]], on="region_id", how="left")
        if "region_name" in staff.columns:
            staff = staff.groupby("region_name", as_index=False).agg(headcount=("employee_id", "nunique"), avg_salary=("salary", "mean"))
            outputs["region_sales_staff"] = regions.merge(staff, on="region_name", how="left")
    # Link category margin with inventory capital.
    sc = sales_customer_outputs(data, fact)
    cat = sc.get("categories", pd.DataFrame())
    invcat = operations.get("inventory_by_category", pd.DataFrame())
    if not cat.empty and not invcat.empty:
        outputs["category_margin_inventory"] = cat.merge(invcat, on="category_name", how="left")
    # Cross-functional narrative input table.
    question_rows = [
        ("Marketing efficiency", "Does marketing spend move with revenue and profit?", "Compare monthly marketing spend with revenue and profit trend."),
        ("Inventory profitability", "Is capital held in inventory supported by product/category margin?", "Compare inventory working capital with category revenue and margin."),
        ("Regional productivity", "Do high-revenue regions have proportionate staff capacity?", "Compare region revenue, profit, headcount, and average salary."),
        ("Finance and workforce", "Is payroll growing faster than revenue?", "Compare monthly payroll cost with revenue and EBITDA proxy."),
        ("Operations and customer impact", "Could fulfilment delays or quality issues contribute to refunds?", "Review shipment status, rejection rate, refund reasons, and customer feedback."),
    ]
    outputs["question_framework"] = pd.DataFrame(question_rows, columns=["theme", "cross_functional_question", "dashboard_evidence"])
    return outputs


def build_ai_insights(data: dict[str, pd.DataFrame], fact: pd.DataFrame, years: list[int] | None = None, platforms: list[str] | None = None) -> dict[str, list[str]]:
    insights: dict[str, list[str]] = {"Executive": [], "Sales & Customer": [], "Marketing": [], "Finance": [], "HR": [], "Operations & Logistics": [], "Cross-Functional": []}
    metrics = executive_kpis(fact)
    insights["Executive"].append(f"Selected filters show revenue of ₹{metrics['revenue']:,.0f}, profit of ₹{metrics['profit']:,.0f}, and a profit margin of {metrics['margin']:.1f}%.")
    sales = sales_customer_outputs(data, fact)
    if not sales.get("products", pd.DataFrame()).empty:
        top = sales["products"].iloc[0]
        insights["Sales & Customer"].append(f"{top['product_name']} is the highest-revenue product in the selected view and should be monitored for margin protection and availability.")
    if not sales.get("rfm", pd.DataFrame()).empty:
        at_risk = int((sales["rfm"]["segment"] == "At-Risk Valuable").sum())
        insights["Sales & Customer"].append(f"{at_risk:,} customers are classified as At-Risk Valuable based on RFM logic; targeted re-engagement can be prioritised.")
    marketing = marketing_outputs(data, fact, years, platforms)
    if not marketing.get("platform_spend", pd.DataFrame()).empty:
        platform = marketing["platform_spend"].iloc[0]
        insights["Marketing"].append(f"{platform['platform']} has the highest marketing spend in the selected period. Review it alongside revenue-per-spend before reallocating budget.")
    finance = finance_outputs(data, fact, years)
    if not finance.get("expense_categories", pd.DataFrame()).empty:
        exp = finance["expense_categories"].iloc[0]
        label_col = finance["expense_categories"].columns[0]
        insights["Finance"].append(f"The largest expense category is {exp[label_col]}; it should be reviewed when the cost-to-revenue ratio increases.")
    hr = hr_outputs(data, metrics["revenue"], years)
    if not hr.get("headcount", pd.DataFrame()).empty:
        hr_top = hr["headcount"].iloc[0]
        dept_col = hr["headcount"].columns[0]
        insights["HR"].append(f"{hr_top[dept_col]} has the highest headcount. Compare staffing level, average salary, and revenue contribution during workforce planning.")
    ops = operations_logistics_outputs(data, years)
    if not ops.get("production", pd.DataFrame()).empty:
        worst = ops["production"].sort_values("rejection_rate_pct", ascending=False).iloc[0]
        line_col = ops["production"].columns[0]
        insights["Operations & Logistics"].append(f"{worst[line_col]} has the highest production rejection rate. Quality checks and root-cause review should be prioritised.")
    cross = cross_functional_outputs(data, fact, years, platforms)
    if not cross.get("marketing_sales_profit", pd.DataFrame()).empty:
        insights["Cross-Functional"].append("Review marketing spend together with revenue and profit because higher spend does not automatically indicate efficient growth.")
    if not cross.get("category_margin_inventory", pd.DataFrame()).empty:
        insights["Cross-Functional"].append("Review categories with high inventory working capital and lower margins to reduce capital blockage and margin pressure.")
    return insights


def domain_question_library() -> dict[str, list[dict[str, str]]]:
    """Question registry based on the supplied RetailMart Analytics Questions & KPI set."""
    return {
        "Sales & Customer": [
            {"question": "What drives revenue across products, categories, regions, stores, and customer tiers?", "status": "Direct"},
            {"question": "Who are the most valuable customers, and which segments require retention action?", "status": "Direct"},
            {"question": "What is the repeat-purchase pattern and early sign of churn?", "status": "Direct / Proxy"},
            {"question": "Why do customers return products and which products generate the most refunds?", "status": "Direct"},
            {"question": "How satisfied are customers based on reviews, support tickets, and call sentiment?", "status": "Direct"},
            {"question": "Is the loyalty programme associated with member activity and redemption behaviour?", "status": "Direct"},
        ],
        "Marketing": [
            {"question": "Which campaigns and platforms coincide with stronger revenue and order movement?", "status": "Workaround / Correlational"},
            {"question": "Are campaigns pacing to budget or overspending?", "status": "Direct"},
            {"question": "How does the email funnel perform across campaigns?", "status": "Direct"},
            {"question": "Which brands and categories should receive more marketing attention?", "status": "Workaround"},
            {"question": "What is blended customer acquisition cost and is it improving?", "status": "Workaround"},
            {"question": "How does web engagement convert into orders and where does the funnel leak?", "status": "Optional Web Events / Workaround"},
        ],
        "Finance": [
            {"question": "What are the revenue, expense, net margin, and EBITDA proxy trends?", "status": "Direct"},
            {"question": "How much value is affected by refunds and failed refunds?", "status": "Direct"},
            {"question": "Are payments successful and what are refund patterns by payment mode?", "status": "Direct"},
            {"question": "Which expense categories are the largest cost drivers?", "status": "Direct"},
            {"question": "How does the cost-to-revenue ratio change over time?", "status": "Direct"},
        ],
        "HR": [
            {"question": "What are total payroll cost, labour cost as a share of revenue, and average salary by department?", "status": "Direct"},
            {"question": "Are employees attending consistently and what are the average worked hours?", "status": "Direct"},
            {"question": "What are headcount, role distribution, and compensation patterns across the organisation?", "status": "Direct"},
            {"question": "What is the attrition rate and average tenure?", "status": "Gap: termination data is not available"},
            {"question": "Are salary payment records consistent and are any payments unprocessed?", "status": "Direct"},
        ],
        "Operations & Logistics": [
            {"question": "Do we hold the right inventory in the right locations, and where are stockouts or overstock risks?", "status": "Direct / Proxy"},
            {"question": "Which suppliers are reliable based on inbound lead time and shipment status?", "status": "Direct"},
            {"question": "How fast and reliably do we deliver, and which courier performs best?", "status": "Direct"},
            {"question": "Which production lines or products drive rejection rates?", "status": "Direct"},
            {"question": "Is the platform healthy based on API error rate and latency?", "status": "Direct"},
        ],
        "Cross-Functional": [
            {"question": "Does marketing spend translate into revenue and profit movement?", "status": "Workaround / Correlational"},
            {"question": "Which high-value customer segments are at risk and which revenue/product categories do they influence?", "status": "Direct / Proxy"},
            {"question": "Are high inventory working-capital categories also low-margin or slow-moving?", "status": "Direct / Proxy"},
            {"question": "Do regions with strong revenue have proportionate profit, staffing capacity, and store performance?", "status": "Direct / Proxy"},
            {"question": "Do shipment delays, production rejections, or refund patterns indicate a customer-experience risk?", "status": "Workaround"},
            {"question": "Is payroll and operating expenditure increasing faster than revenue?", "status": "Direct / Proxy"},
            {"question": "Which business area should management prioritise based on financial impact, customer risk, and operational risk?", "status": "Prescriptive"},
        ],
    }

# =============================================================================
# Streamlit UI — Premium top-tabs + left filters
# =============================================================================

PREMIUM_CSS = """
<style>
:root { --navy:#14263b; --navy2:#1f3a5c; --gold:#b9985b; --paper:#f5f6f9; --card:#ffffff; --ink:#16202d; --muted:#667085; --line:#dfe5ec; }
.stApp { background: var(--paper); color: var(--ink); }
[data-testid="stHeader"] { height:3.35rem; background:rgba(255,255,255,.96); border-bottom:1px solid #eef1f4; }
.block-container { max-width: 1500px; padding-top: 4.35rem !important; padding-bottom: 2.5rem; }
[data-testid="stSidebar"] { background:var(--navy); }
[data-testid="stSidebar"] * { color:#e6edf5; }
[data-testid="stSidebar"] .stCaption { color:#adbac9 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background:#20384f; border:1px solid #456079; }
[data-testid="stSidebar"] [data-baseweb="tag"] { background:var(--gold); }
.hero { padding:1.15rem 1.35rem; margin:0 0 1rem 0; background:linear-gradient(110deg,#162c44,#244c71); border-radius:12px; box-shadow:0 5px 18px rgba(16,38,61,.14); color:white; }
.hero .kicker { color:#e4c88e; font-size:.72rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }
.hero h1 { margin:.22rem 0 .35rem 0; color:white; font-size:2.05rem; }
.hero p { margin:0; color:#d6e1ed; font-size:.94rem; }
.metric-card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; box-shadow:0 2px 7px rgba(16,24,40,.04); min-height:108px; }
.metric-label { color:var(--muted); font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { color:var(--ink); font-size:1.65rem; font-weight:700; margin-top:.38rem; }
.metric-note { color:#7b8794; font-size:.78rem; margin-top:.2rem; }
.section-title { font-size:1.45rem; font-weight:750; margin:1rem 0 .15rem 0; color:var(--ink); }
.section-sub { color:var(--muted); font-size:.9rem; margin-bottom:.8rem; }
.chart-caption { color:var(--muted); font-size:.78rem; padding:.45rem .2rem 0 .2rem; }
.insight { background:#fffdf7; border:1px solid #eadfc3; border-left:4px solid var(--gold); border-radius:8px; padding:.75rem 1rem; margin:.4rem 0; }
.insight b { color:#6f531c; }
.connection-ok { background:#e7f6ec; border:1px solid #bfe3cb; color:#166534; border-radius:8px; padding:.65rem .75rem; font-size:.85rem; }
.stTabs [data-baseweb="tab-list"] { gap:.28rem; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { border-radius:7px 7px 0 0; padding:.7rem .85rem; font-weight:650; color:#475467; }
.stTabs [aria-selected="true"] { color:var(--navy2) !important; background:#edf4fb; border-bottom:3px solid var(--navy2); }
[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid var(--line) !important; border-radius:10px !important; background:#fff; }
.stDownloadButton button, .stButton button { background:var(--navy2); color:#fff; border:1px solid var(--navy2); border-radius:7px; font-weight:650; }
.stDownloadButton button:hover, .stButton button:hover { background:#14263b; border-color:#14263b; }
</style>
"""
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def fmt_currency(value: float | int | None) -> str:
    if value is None or not np.isfinite(float(value)):
        return "N/A"
    value = float(value)
    if abs(value) >= 1e7:
        return f"₹{value/1e7:,.2f} Cr"
    if abs(value) >= 1e5:
        return f"₹{value/1e5:,.2f} L"
    if abs(value) >= 1e3:
        return f"₹{value/1e3:,.1f} K"
    return f"₹{value:,.0f}"


def fmt_percent(value: float | int | None) -> str:
    if value is None or not np.isfinite(float(value)):
        return "N/A"
    return f"{float(value):.2f}%"


def metric(label: str, value: str, note: str) -> None:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{escape(label)}</div><div class='metric-value'>{escape(value)}</div><div class='metric-note'>{escape(note)}</div></div>", unsafe_allow_html=True)


def title_block(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='section-title'>{escape(title)}</div><div class='section-sub'>{escape(subtitle)}</div>", unsafe_allow_html=True)


def chart(fig: go.Figure, caption: str, chart_key: str) -> None:
    fig.update_layout(
        template='plotly_white', paper_bgcolor='white', plot_bgcolor='white',
        font=dict(family='Inter, Segoe UI, Arial', color='#16202d'),
        colorway=['#1f3a5c','#4c8fb6','#b9985b','#708090','#7b9e87','#b25e5e'],
        margin=dict(l=55,r=24,t=60,b=58), height=360,
        legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'),
    )
    fig.update_xaxes(showgrid=False, linecolor='#dfe5ec')
    fig.update_yaxes(gridcolor='#edf0f3', linecolor='#dfe5ec')
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False}, key=chart_key)
        st.markdown(f"<div class='chart-caption'>{escape(caption)}</div>", unsafe_allow_html=True)


def get_neon_config() -> tuple[str,int,str,str,str,str] | None:
    if 'postgres' not in st.secrets:
        return None
    cfg = st.secrets['postgres']
    required = ['host','database','user','password']
    if not all(key in cfg and str(cfg[key]).strip() for key in required):
        return None
    return (str(cfg['host']), int(cfg.get('port',5432)), str(cfg['database']), str(cfg['user']), str(cfg['password']), str(cfg.get('sslmode','require')))


@st.cache_resource(show_spinner=False)
def get_engine(config: tuple[str,int,str,str,str,str]):
    return create_postgres_engine(*config)


@st.cache_data(show_spinner='Connecting to Neon PostgreSQL and loading dashboard tables…')
def load_neon_data(config: tuple[str,int,str,str,str,str], include_web: bool):
    engine = get_engine(config)
    return load_tables_from_postgres(engine, include_web)


def connection_info(engine) -> dict[str,str]:
    with engine.connect() as conn:
        row = conn.execute(text('SELECT current_database() AS database, current_user AS db_user, CURRENT_TIMESTAMP AS server_time')).mappings().one()
    return {'database':str(row['database']), 'user':str(row['db_user']), 'server_time':str(row['server_time'])}


def available_values(df: pd.DataFrame, col: str) -> list:
    if df.empty or col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())


def build_filter_options(fact: pd.DataFrame) -> dict[str,list]:
    years=[]
    if 'order_date' in fact.columns:
        years=sorted(pd.to_datetime(fact['order_date'],errors='coerce').dt.year.dropna().astype(int).unique().tolist())
    return {'years':years,'categories':available_values(fact,'category_name'),'products':available_values(fact,'product_name'),'regions':available_values(fact,'region_name'),'states':available_values(fact,'state'),'stores':available_values(fact,'store_name')}


def fact_filter(fact: pd.DataFrame, filters: dict[str,list]) -> pd.DataFrame:
    return apply_sales_filters(fact, filters['years'], filters['categories'], filters['products'], filters['regions'], filters['states'], filters['stores'])


def page_overview(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('Executive Overview','Enterprise-level performance across commercial growth, financial efficiency, workforce, inventory, and operational delivery.')
    k = executive_kpis(fact)
    finance = finance_outputs(data, fact, filters['years'])
    hr = hr_outputs(data, k['revenue'], filters['years'])
    ops = operations_logistics_outputs(data, filters['years'], filters['shipment_status'], filters['warehouse_regions'])
    opex = float(finance.get('monthly_expenses',pd.DataFrame()).get('opex',pd.Series(dtype=float)).sum())
    payroll = float(hr.get('payroll_monthly',pd.DataFrame()).get('gross_payroll',pd.Series(dtype=float)).sum())
    low_stock = int(ops.get('inventory_risk',pd.DataFrame()).get('below_reorder',pd.Series(dtype=bool)).sum())
    employee_count = data.get('store_employees', pd.DataFrame()).get('employee_id', pd.Series(dtype=int)).nunique()
    revenue_per_employee = safe_divide(k['revenue'], max(1, employee_count))
    a,b,c,d = st.columns(4)
    with a: metric('Operating Expenses',fmt_currency(opex),'Finance expense records')
    with b: metric('Gross Payroll',fmt_currency(payroll),'Workforce cost')
    with c: metric('Below Reorder SKUs',f'{low_stock:,}','Inventory attention indicator')
    with d: metric('Revenue per Employee',fmt_currency(revenue_per_employee),'Revenue ÷ headcount')
    monthly = monthly_sales_summary(fact)
    c1,c2 = st.columns(2)
    with c1:
        if not monthly.empty: chart(px.line(monthly,x='month',y=['revenue','profit'],markers=True,title='Monthly Revenue and Profit'),'Tracks commercial performance by month for the current filter selection.','overview_monthly_revenue_profit')
    with c2:
        if not monthly.empty: chart(px.line(monthly,x='month',y='margin_pct',markers=True,title='Monthly Profit Margin'),'A falling margin may indicate rising costs or discount pressure.','overview_monthly_margin')
    insights = build_ai_insights(data, fact, filters['years'], filters['platforms'])
    st.subheader('Management Priorities')
    for group in ['Executive','Finance','Operations & Logistics','Cross-Functional']:
        for item in insights.get(group,[]):
            st.markdown(f"<div class='insight'><b>{escape(group)}:</b> {escape(item)}</div>",unsafe_allow_html=True)


def page_sales(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('Sales & Customer','Product, category, regional profitability, RFM segmentation, customer experience, returns, and loyalty indicators.')
    out=sales_customer_outputs(data,fact); k=executive_kpis(fact); rfm=out.get('rfm',pd.DataFrame())
    repeat=(rfm['frequency']>1).mean()*100 if not rfm.empty and 'frequency' in rfm.columns else np.nan
    a,b,c,d=st.columns(4)
    with a: metric('Revenue',fmt_currency(k['revenue']),'Selected sales view')
    with b: metric('Average Order Value',fmt_currency(k['aov']),'Revenue ÷ orders')
    with c: metric('Repeat Purchase Rate',fmt_percent(repeat),'Customers with more than one order')
    with d: metric('Total Orders',f"{k['orders']:,}",'Valid orders in scope')
    c1,c2=st.columns(2)
    products=out.get('products',pd.DataFrame()).head(12)
    regions=out.get('regions',pd.DataFrame())
    with c1:
        if not products.empty: chart(px.bar(products.sort_values('revenue'),x='revenue',y='product_name',orientation='h',title='Top Products by Revenue'),'Ranks the products contributing the greatest revenue.','sales_top_products')
    with c2:
        if not regions.empty: chart(px.bar(regions,x='region_name',y=['revenue','profit'],barmode='group',title='Revenue and Profit by Region'),'Compares commercial value and profitability across regions.','sales_region_revenue_profit')
    c1,c2=st.columns(2)
    with c1:
        if not rfm.empty:
            summary=rfm.groupby('segment',as_index=False).agg(customers=('cust_id','nunique'))
            chart(px.bar(summary,x='segment',y='customers',title='Customer Segments (RFM)'),'Shows customer groups for retention and reactivation planning.','sales_rfm_segments')
    with c2:
        returns=out.get('return_reasons',pd.DataFrame()).head(10)
        if not returns.empty: chart(px.bar(returns,x='refund_value',y='reason',orientation='h',title='Refund Value by Return Reason'),'Highlights return reasons with the greatest financial impact.','sales_refund_reasons')


def page_marketing(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('Marketing','Campaign spend, platform allocation, email engagement, budget pacing, and correlation with revenue and profit.')
    out=marketing_outputs(data,fact,filters['years'],filters['platforms'])
    spend=out.get('platform_spend',pd.DataFrame()); email=out.get('email_performance',pd.DataFrame()); trend=out.get('spend_sales_trend',pd.DataFrame())
    a,b,c,d=st.columns(4)
    with a: metric('Marketing Spend',fmt_currency(float(spend.get('spend',pd.Series(dtype=float)).sum())),'Selected platforms and period')
    with b: metric('Average Open Rate',fmt_percent(email.get('open_rate_pct',pd.Series(dtype=float)).mean() if not email.empty else np.nan),'Campaign engagement')
    with c: metric('Average CTR',fmt_percent(email.get('ctr_pct',pd.Series(dtype=float)).mean() if not email.empty else np.nan),'Clicks ÷ sent')
    rev_per=trend.get('revenue_per_spend',pd.Series(dtype=float)).replace([np.inf,-np.inf],np.nan).mean() if not trend.empty else np.nan
    with d: metric('Revenue per ₹ Spent',f'{rev_per:.2f}x' if np.isfinite(rev_per) else 'N/A','Correlation proxy, not attribution')
    c1,c2=st.columns(2)
    with c1:
        if not spend.empty: chart(px.bar(spend.sort_values('spend'),x='spend',y='platform',orientation='h',title='Ad Spend by Platform'),'Ranks marketing spend by platform.','marketing_spend_by_platform')
    with c2:
        if not trend.empty: chart(px.line(trend,x='month',y=['marketing_spend','revenue','profit'],markers=True,title='Marketing Spend, Revenue and Profit'),'Compares marketing investment with commercial outcomes; it is correlational.','marketing_spend_revenue_profit')
    if not email.empty:
        x='campaign_name' if 'campaign_name' in email.columns else email.columns[0]
        chart(px.line(email.head(15),x=x,y=['open_rate_pct','ctr_pct'],markers=True,title='Email Funnel Rates by Campaign'),'Compares email engagement performance across campaigns.','marketing_email_funnel')


def page_finance(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('Finance','Operating expenses, EBITDA proxy, payment patterns, refund exposure, and cost-to-revenue monitoring.')
    out=finance_outputs(data,fact,filters['years']); pnl=out.get('pnl',pd.DataFrame()); k=executive_kpis(fact)
    opex=float(out.get('monthly_expenses',pd.DataFrame()).get('opex',pd.Series(dtype=float)).sum()); ebitda=float(pnl.get('ebitda_proxy',pd.Series(dtype=float)).sum()) if not pnl.empty else np.nan
    refunds=float(out.get('refund_log',pd.DataFrame()).get('refund_value',pd.Series(dtype=float)).sum())
    a,b,c,d=st.columns(4)
    with a: metric('Operating Expenses',fmt_currency(opex),'Selected finance records')
    with b: metric('EBITDA Proxy',fmt_currency(ebitda),'Profit less operating expense')
    with c: metric('Cost-to-Revenue',fmt_percent(safe_divide(opex,k['revenue'])*100),'Operating expense ÷ revenue')
    with d: metric('Refund Value',fmt_currency(refunds),'Refund audit log')
    c1,c2=st.columns(2)
    with c1:
        if not pnl.empty: chart(px.line(pnl,x='month',y=['revenue','opex','ebitda_proxy'],markers=True,title='Revenue, Opex and EBITDA Proxy'),'Shows the relationship between revenue, operating cost, and estimated operating earnings.','finance_revenue_opex_ebitda')
    with c2:
        exp=out.get('expense_categories',pd.DataFrame()).head(12)
        if not exp.empty: chart(px.bar(exp.sort_values('expense'),x='expense',y=exp.columns[0],orientation='h',title='Largest Expense Categories'),'Highlights major cost drivers requiring review.','finance_expense_categories')


def page_hr(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('HR','Headcount, payroll, compensation, attendance, and workforce productivity indicators.')
    k=executive_kpis(fact); out=hr_outputs(data,k['revenue'],filters['years']); head=out.get('headcount',pd.DataFrame()); pay=out.get('payroll_monthly',pd.DataFrame()); att=out.get('attendance',pd.DataFrame())
    employees=data.get('store_employees',pd.DataFrame()); total_pay=float(pay.get('gross_payroll',pd.Series(dtype=float)).sum())
    a,b,c,d=st.columns(4)
    with a: metric('Headcount',f"{employees.get('employee_id',pd.Series(dtype=int)).nunique():,}" if not employees.empty else 'N/A','Employee master')
    with b: metric('Gross Payroll',fmt_currency(total_pay),'Pay-slip records')
    with c: metric('Average Salary',fmt_currency(head.get('avg_salary',pd.Series(dtype=float)).mean() if not head.empty else np.nan),'Department average')
    rev_emp=out.get('revenue_per_employee',pd.DataFrame()).get('revenue_per_employee',pd.Series(dtype=float))
    with d: metric('Revenue per Employee',fmt_currency(rev_emp.iloc[0] if len(rev_emp) else np.nan),'Revenue ÷ headcount')
    c1,c2=st.columns(2)
    with c1:
        if not head.empty: chart(px.bar(head,x=head.columns[0],y='headcount',title='Headcount by Department'),'Shows workforce distribution across departments.','hr_headcount_by_department')
    with c2:
        if not head.empty: chart(px.bar(head,x=head.columns[0],y='avg_salary',title='Average Salary by Department'),'Compares average salary by department.','hr_avg_salary_by_department')
    if not pay.empty: chart(px.line(pay,x='month',y=['gross_payroll','net_payroll'],markers=True,title='Gross and Net Payroll Trend'),'Tracks workforce cost over time.','hr_payroll_trend')
    st.info('Attrition is not calculated because the supplied schema does not include an employee exit or termination date.')


def page_operations(data: dict[str,pd.DataFrame], filters: dict[str,list]) -> None:
    title_block('Operations & Logistics','Inventory working capital, shipment status, supplier lead time, production quality, and operational reliability.')
    out=operations_logistics_outputs(data,filters['years'],filters['shipment_status'],filters['warehouse_regions']); inv=out.get('inventory_risk',pd.DataFrame()); prod=out.get('production',pd.DataFrame()); courier=out.get('courier',pd.DataFrame()); supplier=out.get('supplier_lead',pd.DataFrame())
    a,b,c,d=st.columns(4)
    with a: metric('Below Reorder SKUs',f"{int(inv.get('below_reorder',pd.Series(dtype=bool)).sum()):,}",'Inventory alert')
    with b: metric('Average Delivery Days',f"{courier.get('avg_delivery_days',pd.Series(dtype=float)).mean():.1f}" if not courier.empty else 'N/A','Delivered shipments')
    with c: metric('Average Rejection Rate',fmt_percent(prod.get('rejection_rate_pct',pd.Series(dtype=float)).mean() if not prod.empty else np.nan),'Production-line average')
    with d: metric('Supplier Lead Days',f"{supplier.get('avg_lead_days',pd.Series(dtype=float)).mean():.1f}" if not supplier.empty else 'N/A','Inbound shipment average')
    c1,c2=st.columns(2)
    cat=out.get('inventory_by_category',pd.DataFrame()); status=out.get('outbound_status',pd.DataFrame())
    with c1:
        if not cat.empty: chart(px.bar(cat.sort_values('inventory_value'),x='inventory_value',y='category_name',orientation='h',title='Inventory Working Capital by Category'),'Shows the value of stock tied up by product category.','ops_inventory_working_capital')
    with c2:
        if not status.empty: chart(px.bar(status,x='status',y='shipments',title='Outbound Shipment Status'),'Shows delivery status distribution for operational review.','ops_outbound_shipment_status')
    c1,c2=st.columns(2)
    with c1:
        if not prod.empty: chart(px.bar(prod,x=prod.columns[0],y='rejection_rate_pct',title='Rejection Rate by Production Line'),'Highlights lines requiring quality review.','ops_rejection_rate')
    with c2:
        if not supplier.empty: chart(px.bar(supplier.head(12),x=supplier.columns[0],y='avg_lead_days',title='Average Inbound Lead Time by Supplier'),'Compares supplier inbound delivery lead times.','ops_supplier_lead_time')


def page_cross(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('Cross-Functional View','Integrated analysis connecting marketing investment, sales, profit, workforce capacity, inventory exposure, and operating costs.')
    out=cross_functional_outputs(data,fact,filters['years'],filters['platforms'])
    c1,c2=st.columns(2)
    with c1:
        trend=out.get('marketing_sales_profit',pd.DataFrame())
        if not trend.empty: chart(px.line(trend,x='month',y=['marketing_spend','revenue','profit'],markers=True,title='Marketing Spend, Revenue and Profit'),'Connects commercial investment with revenue and profit movement.','cross_marketing_sales_profit')
    with c2:
        regional=out.get('region_sales_staff',pd.DataFrame())
        if not regional.empty: chart(px.scatter(regional,x='headcount',y='revenue',size='profit',hover_name='region_name',title='Regional Revenue, Profit and Headcount'),'Compares commercial productivity and staffing capacity.','cross_region_revenue_profit_headcount')
    c1,c2=st.columns(2)
    with c1:
        cat=out.get('category_margin_inventory',pd.DataFrame())
        if not cat.empty: chart(px.scatter(cat,x='inventory_value',y='margin_pct',size='revenue',hover_name='category_name',title='Inventory Working Capital vs Category Margin'),'Identifies capital concentration alongside category profitability.','cross_inventory_margin')
    with c2:
        pnl=out.get('profit_cost',pd.DataFrame())
        if not pnl.empty: chart(px.line(pnl,x='month',y=['profit','opex','ebitda_proxy'],markers=True,title='Profit, Opex and EBITDA Proxy'),'Shows how operating cost affects profit and estimated operating earnings.','cross_profit_opex_ebitda')
    st.dataframe(out.get('question_framework',pd.DataFrame()),use_container_width=True,hide_index=True)


def page_ai(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('AI-Assisted Insights','Rule-based, transparent management observations grounded in dashboard KPIs and analytical outputs.')
    insights=build_ai_insights(data,fact,filters['years'],filters['platforms'])
    for group,items in insights.items():
        with st.expander(f'{group} insights',expanded=(group=='Executive')):
            if items:
                for item in items: st.markdown(f"<div class='insight'><b>{escape(group)}:</b> {escape(item)}</div>",unsafe_allow_html=True)
            else: st.caption('No insight available for the current filter selection.')


def report_content(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> tuple[str,dict[str,pd.DataFrame]]:
    k=executive_kpis(fact); insights=build_ai_insights(data,fact,filters['years'],filters['platforms'])
    frames={
        'Executive_Monthly_KPI':monthly_sales_summary(fact),
        'Sales_Product':sales_customer_outputs(data,fact).get('products',pd.DataFrame()),
        'Marketing_Platform':marketing_outputs(data,fact,filters['years'],filters['platforms']).get('platform_spend',pd.DataFrame()),
        'Finance_PnL':finance_outputs(data,fact,filters['years']).get('pnl',pd.DataFrame()),
        'HR_Headcount':hr_outputs(data,k['revenue'],filters['years']).get('headcount',pd.DataFrame()),
        'Ops_Inventory':operations_logistics_outputs(data,filters['years'],filters['shipment_status'],filters['warehouse_regions']).get('inventory_risk',pd.DataFrame()),
        'Cross_Functional':cross_functional_outputs(data,fact,filters['years'],filters['platforms']).get('question_framework',pd.DataFrame()),
    }
    lines=['AI-Assisted Cross-Functional BI Dashboard — Management Report','='*65,f"Revenue: {fmt_currency(k['revenue'])}",f"Profit: {fmt_currency(k['profit'])}",f"Profit Margin: {fmt_percent(k['margin'])}",f"Orders: {k['orders']:,}",'','Management Insights']
    for group,items in insights.items():
        lines.append(f'\n{group}')
        lines.extend(f'- {x}' for x in items)
    return '\n'.join(lines),frames


def excel_bytes(frames: dict[str,pd.DataFrame])->bytes:
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine='openpyxl') as writer:
        for sheet,frame in frames.items(): frame.to_excel(writer,sheet_name=sheet[:31],index=False)
    return buf.getvalue()


def page_export(data: dict[str,pd.DataFrame], fact: pd.DataFrame, filters: dict[str,list]) -> None:
    title_block('Generate / Export Report','Download management-ready KPI summaries, insight statements, and domain-wise analytical tables.')
    report,frames=report_content(data,fact,filters)
    a,b,c=st.columns(3)
    with a: st.download_button('Download Text Report',report,'management_report.txt','text/plain',use_container_width=True)
    with b: st.download_button('Download Excel Workbook',excel_bytes(frames),'management_report.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
    with c: st.download_button('Download HTML Report',f'<html><body><pre>{escape(report)}</pre></body></html>','management_report.html','text/html',use_container_width=True)
    st.text_area('Report preview',report,height=340)


def main() -> None:
    config=get_neon_config()
    if config is None:
        st.error('Neon PostgreSQL credentials are not configured in Streamlit Secrets.')
        st.code('[postgres]\nhost = "YOUR_NEON_POOLER_HOST"\nport = 5432\ndatabase = "neondb"\nuser = "neondb_owner"\npassword = "YOUR_ACTUAL_NEON_PASSWORD"\nsslmode = "require"',language='toml')
        return
    try:
        engine=get_engine(config)
        conn=connection_info(engine)
    except Exception as exc:
        st.error(f'Neon connection failed: {exc}')
        st.info('Verify host, port, database, user, actual password, sslmode, and Streamlit Secrets formatting.')
        return
    with st.sidebar:
        st.markdown('## BI Control Center')
        st.caption('Neon-only runtime • PostgreSQL live source')
        st.markdown(f"<div class='connection-ok'>● Live Neon connection verified<br><small>{escape(conn['database'])} • {escape(conn['user'])}</small></div>",unsafe_allow_html=True)
        st.divider()
        load_web=st.toggle('Load optional web-event tables',value=False)
    try:
        data,messages=load_neon_data(config,load_web)
    except Exception as exc:
        st.error(f'Unable to load Neon tables: {exc}')
        return
    if 'orders' not in data or 'order_items' not in data or 'products' not in data:
        st.error('Required tables are missing from Neon. Required: sales.orders, sales.order_items, products.products, core.dim_brand, core.dim_category.')
        if messages:
            with st.expander('Neon load notes'):
                st.write('\n'.join(f'• {m}' for m in messages))
        return
    fact=make_sales_fact(data)
    if fact.empty:
        st.error('The Sales Fact table could not be created. Confirm primary and foreign key columns in the Neon tables.')
        return
    options=build_filter_options(fact)
    with st.sidebar:
        st.divider(); st.markdown('### Global Filters')
        years=st.multiselect('Year',options['years'],default=options['years'])
        categories=st.multiselect('Product category',options['categories'])
        products=st.multiselect('Product',options['products'])
        regions=st.multiselect('Sales region',options['regions'])
        states=st.multiselect('State',options['states'])
        stores=st.multiselect('Store',options['stores'])
        platforms=st.multiselect('Marketing platform',available_values(data.get('ads_spend',pd.DataFrame()),'platform'))
        shipment_status=st.multiselect('Shipment status',available_values(data.get('sales_shipments',pd.DataFrame()),'status'))
        warehouse_regions=st.multiselect('Warehouse region',available_values(data.get('warehouses',pd.DataFrame()),'region'))
        st.caption(f'Loaded {len(data)} Neon tables.')
    filters={'years':years,'categories':categories,'products':products,'regions':regions,'states':states,'stores':stores,'platforms':platforms,'shipment_status':shipment_status,'warehouse_regions':warehouse_regions}
    fact=fact_filter(fact,filters)
    st.markdown("<div class='hero'><div class='kicker'>RetailMart • Neon PostgreSQL • Live Dashboard</div><h1>AI-Assisted Cross-Functional BI Dashboard</h1><p>Management analytics across Sales & Customer, Marketing, Finance, HR, Operations & Logistics, and Cross-Functional performance.</p></div>",unsafe_allow_html=True)
    if fact.empty:
        st.warning('No sales records match the selected filter combination. Remove one or more filters.')
        return
    k=executive_kpis(fact); c1,c2,c3,c4=st.columns(4)
    with c1: metric('Total Revenue',fmt_currency(k['revenue']),'Net order value')
    with c2: metric('Total Profit',fmt_currency(k['profit']),'Revenue less estimated cost')
    with c3: metric('Profit Margin',fmt_percent(k['margin']),'Profit efficiency')
    with c4: metric('Total Orders',f"{k['orders']:,}",'Valid orders analysed')
    tabs=st.tabs(['Executive Overview','Sales & Customer','Marketing','Finance','HR','Operations & Logistics','Cross-Functional','AI Insights','Export Report'])
    with tabs[0]: page_overview(data,fact,filters)
    with tabs[1]: page_sales(data,fact,filters)
    with tabs[2]: page_marketing(data,fact,filters)
    with tabs[3]: page_finance(data,fact,filters)
    with tabs[4]: page_hr(data,fact,filters)
    with tabs[5]: page_operations(data,filters)
    with tabs[6]: page_cross(data,fact,filters)
    with tabs[7]: page_ai(data,fact,filters)
    with tabs[8]: page_export(data,fact,filters)
    if messages:
        with st.expander(f'Optional / unavailable Neon tables ({len(messages)})'):
            for message in messages: st.write('• '+message)


if __name__=='__main__':
    main()
