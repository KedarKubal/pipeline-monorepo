"""Orchestrates cleaning + validation into two named pipelines:
customers and order lines. Kept separate from load/ so transform logic can
be unit tested without touching a database.
"""
from __future__ import annotations

import pandas as pd

from src.transform.cleaners import (
    coerce_dates,
    coerce_numeric,
    normalize_email,
    normalize_phone,
    split_full_name,
    strip_whitespace,
)
from src.transform.validators import ValidationResult, validate_customers, validate_order_lines


def transform_customers(raw: pd.DataFrame) -> ValidationResult:
    df = raw.copy()
    df = split_full_name(df, source_col="full_name")
    df = normalize_email(df, col="email")
    df = normalize_phone(df, col="phone")
    df = strip_whitespace(df, columns=["addr_line", "city", "state", "zip"])
    df = coerce_dates(df, columns=["signup_date"])
    return validate_customers(df)


def transform_order_lines(raw: pd.DataFrame, known_customer_legacy_ids: set[str]) -> ValidationResult:
    df = raw.copy()
    df = coerce_numeric(df, columns=["qty", "unit_price"])
    df = coerce_dates(df, columns=["order_date"])
    df = strip_whitespace(df, columns=["product_sku", "product_name", "status"])
    return validate_order_lines(df, known_customer_legacy_ids=known_customer_legacy_ids)
