"""Unit tests for pure transform functions in src/transform/cleaners.py."""
from __future__ import annotations

import pandas as pd

from src.transform.cleaners import (
    coerce_dates,
    coerce_numeric,
    is_valid_email,
    normalize_email,
    normalize_phone,
    split_full_name,
)


class TestSplitFullName:
    def test_splits_two_word_name(self):
        df = pd.DataFrame({"full_name": ["Jane Doe"]})
        result = split_full_name(df)
        assert result.loc[0, "first_name"] == "Jane"
        assert result.loc[0, "last_name"] == "Doe"

    def test_splits_three_word_name_keeps_remainder_in_last(self):
        df = pd.DataFrame({"full_name": ["Mary Jane Watson"]})
        result = split_full_name(df)
        assert result.loc[0, "first_name"] == "Mary"
        assert result.loc[0, "last_name"] == "Jane Watson"

    def test_handles_missing_name(self):
        df = pd.DataFrame({"full_name": [None]})
        result = split_full_name(df)
        assert result.loc[0, "first_name"] == ""
        assert result.loc[0, "last_name"] == ""

    def test_handles_single_word_name(self):
        df = pd.DataFrame({"full_name": ["Madonna"]})
        result = split_full_name(df)
        assert result.loc[0, "first_name"] == "Madonna"
        assert result.loc[0, "last_name"] == ""


class TestNormalizeEmail:
    def test_lowercases_and_strips(self):
        df = pd.DataFrame({"email": ["  Jane.Doe@Example.COM  "]})
        result = normalize_email(df)
        assert result.loc[0, "email"] == "jane.doe@example.com"


class TestNormalizePhone:
    def test_strips_formatting_to_digits(self):
        df = pd.DataFrame({"phone": ["(555) 123-4567"]})
        result = normalize_phone(df)
        assert result.loc[0, "phone"] == "5551234567"

    def test_none_stays_none(self):
        df = pd.DataFrame({"phone": [None]})
        result = normalize_phone(df)
        assert result.loc[0, "phone"] is None


class TestCoerceNumeric:
    def test_unparsable_becomes_nan(self):
        df = pd.DataFrame({"qty": ["3", "not-a-number", "5"]})
        result = coerce_numeric(df, columns=["qty"])
        assert result["qty"].tolist()[0] == 3
        assert pd.isna(result["qty"].tolist()[1])
        assert result["qty"].tolist()[2] == 5


class TestCoerceDates:
    def test_valid_date_normalized_to_iso(self):
        df = pd.DataFrame({"order_date": ["06/01/2023"]})
        result = coerce_dates(df, columns=["order_date"])
        assert result.loc[0, "order_date"] == "2023-06-01"

    def test_invalid_date_becomes_nan(self):
        df = pd.DataFrame({"order_date": ["not-a-date"]})
        result = coerce_dates(df, columns=["order_date"])
        assert pd.isna(result.loc[0, "order_date"])


class TestIsValidEmail:
    def test_valid_email(self):
        assert is_valid_email("user@example.com") is True

    def test_missing_at_sign(self):
        assert is_valid_email("userexample.com") is False

    def test_none_is_invalid(self):
        assert is_valid_email(None) is False
