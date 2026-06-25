"""Reusable data-processing components for the RetailMart BI project."""

from .bi_pipeline import (
    TABLE_SPECS,
    build_rule_based_insights,
    build_sales_fact,
    calculate_executive_kpis,
    create_postgres_engine,
    data_quality_profile,
    load_tables_from_postgres,
    monthly_sales_summary,
    rfm_segmentation,
    validate_required_tables,
)

__all__ = [
    "TABLE_SPECS",
    "build_rule_based_insights",
    "build_sales_fact",
    "calculate_executive_kpis",
    "create_postgres_engine",
    "data_quality_profile",
    "load_tables_from_postgres",
    "monthly_sales_summary",
    "rfm_segmentation",
    "validate_required_tables",
]
