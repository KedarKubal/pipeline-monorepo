"""Pure, unit-testable cleaning functions.

Each function takes a DataFrame in and returns a new DataFrame out — no
side effects, no I/O. This is what makes them trivially unit-testable and
safely composable in the pipeline.
"""
from __future__ import annotations

import re

import pandas as pd

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_NON_DIGITS_RE = re.compile(r"\D")


def split_full_name(df: pd.DataFrame, source_col: str = "full_name") -> pd.DataFrame:
    """Splits 'Jane Doe' -> first_name='Jane', last_name='Doe'.

    Names with more than two tokens put everything after the first token
    into last_name (e.g. 'Mary Jane Watson' -> first='Mary', last='Jane Watson'),
    which is a safer default than silently dropping data.
    """
    df = df.copy()
    parts = df[source_col].fillna("").str.strip().str.split(n=1, expand=True)
    # When every value in source_col is empty, str.split(expand=True) returns
    # a DataFrame with zero columns rather than a column of empty strings —
    # guard both the "no column 0" and "no column 1" cases explicitly.
    df["first_name"] = parts[0].fillna("").str.strip() if 0 in parts.columns else ""
    df["last_name"] = parts[1].fillna("").str.strip() if 1 in parts.columns else ""
    return df


def normalize_email(df: pd.DataFrame, col: str = "email") -> pd.DataFrame:
    """Lowercases and strips emails; leaves genuinely missing values as NaN."""
    df = df.copy()
    df[col] = df[col].astype("string").str.strip().str.lower()
    return df


def normalize_phone(df: pd.DataFrame, col: str = "phone") -> pd.DataFrame:
    """Strips phone numbers to digits only (e.g. '(555) 123-4567' -> '5551234567').

    Keeps None/NaN as-is since phone is optional in the target schema.
    """
    df = df.copy()

    def _clean(value: object) -> str | None:
        if pd.isna(value):
            return None
        digits = _NON_DIGITS_RE.sub("", str(value))
        return digits or None

    df[col] = df[col].apply(_clean)
    return df


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerces columns to numeric, turning unparsable values into NaN
    (which the validator layer then catches) rather than raising mid-pipeline.
    """
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def coerce_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerces columns to ISO-8601 date strings; unparsable dates become NaT/NaN."""
    df = df.copy()
    for col in columns:
        parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
        df[col] = parsed.dt.strftime("%Y-%m-%d")
    return df


def strip_whitespace(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Trims leading/trailing whitespace on the given string columns."""
    df = df.copy()
    for col in columns:
        df[col] = df[col].astype("string").str.strip()
    return df


def is_valid_email(value: object) -> bool:
    return isinstance(value, str) and bool(_EMAIL_RE.match(value))


def coerce_timestamps(df, columns):
    """Coerces columns to full ISO-8601 timestamp strings (with time-of-day
    preserved); unparsable values become NaT/NaN.

    Distinct from coerce_dates, which truncates to a date-only string --
    correct for calendar dates like signup_date/order_date, but wrong for
    anything used as part of a uniqueness key at sub-day granularity (e.g.
    flag_change_audits' natural key is (flag_key, changed_at)).
    """
    df = df.copy()
    for col in columns:
        parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
        df[col] = parsed.dt.strftime("%Y-%m-%dT%H:%M:%S.%f").str[:-3] + "Z"
    return df
