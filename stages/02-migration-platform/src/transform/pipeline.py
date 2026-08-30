"""Orchestrates cleaning + validation into two named pipelines:
customers and order lines. Kept separate from load/ so transform logic can
be unit tested without touching a database.
"""
from __future__ import annotations

import pandas as pd

from src.transform.cleaners import (
    coerce_dates,
    coerce_numeric,
    coerce_timestamps,
    normalize_email,
    normalize_phone,
    split_full_name,
    strip_whitespace,
)
from src.transform.validators import (
    ValidationResult,
    validate_customers,
    validate_flag_audit,
    validate_order_lines,
    validate_analytics_events
)

def transform_customers(raw: pd.DataFrame, *, strict_email: bool = False) -> ValidationResult:
    df = raw.copy()
    df = split_full_name(df, source_col="full_name")
    df = normalize_email(df, col="email")
    df = normalize_phone(df, col="phone")
    df = strip_whitespace(df, columns=["addr_line", "city", "state", "zip"])
    df = coerce_dates(df, columns=["signup_date"])
    return validate_customers(df, strict_email=strict_email)


def transform_order_lines(raw: pd.DataFrame, known_customer_legacy_ids: set[str]) -> ValidationResult:
    df = raw.copy()
    df = coerce_numeric(df, columns=["qty", "unit_price"])
    df = coerce_dates(df, columns=["order_date"])
    df = strip_whitespace(df, columns=["product_sku", "product_name", "status"])
    return validate_order_lines(df, known_customer_legacy_ids=known_customer_legacy_ids)


def transform_flag_audit(raw: pd.DataFrame) -> ValidationResult:
    df = raw.copy()
    df = coerce_timestamps(df, columns=["changed_at"])
    df = strip_whitespace(df, columns=["flag_key", "action"])
    return validate_flag_audit(df)


def transform_analytics_events(raw: pd.DataFrame) -> ValidationResult:
    df = raw.copy()
    df = coerce_timestamps(df, columns=["timestamp"])
    df = strip_whitespace(df, columns=["event"])
    return validate_analytics_events(df)
