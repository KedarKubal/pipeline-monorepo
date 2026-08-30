"""Unit tests for src/transform/validators.py."""
from __future__ import annotations

from src.transform.pipeline import transform_customers, transform_order_lines


class TestValidateCustomers:
    def test_valid_rows_pass_through(self, raw_customers_df):
        result = transform_customers(raw_customers_df.iloc[:2])
        assert len(result.valid) == 2
        assert len(result.quarantined) == 0

    def test_invalid_email_is_quarantined(self, raw_customers_df):
        result = transform_customers(raw_customers_df)
        reasons = result.quarantined["rejection_reason"].tolist()
        assert any("email" in r for r in reasons)

    def test_duplicate_email_keeps_most_recent(self):
        import pandas as pd
        df = pd.DataFrame(
            [
                {"customer_id": "C1", "full_name": "A A", "email": "same@example.com", "phone": None,
                 "addr_line": "x", "city": "x", "state": "IL", "zip": "1", "signup_date": "2023-01-01"},
                {"customer_id": "C2", "full_name": "B B", "email": "same@example.com", "phone": None,
                 "addr_line": "x", "city": "x", "state": "IL", "zip": "1", "signup_date": "2023-02-01"},
            ]
        )
        result = transform_customers(df)
        assert len(result.valid) == 1
        assert result.valid.iloc[0]["customer_id"] == "C2"  # most recent kept


class TestValidateOrderLines:
    def test_orphaned_customer_is_quarantined(self, raw_order_lines_df):
        result = transform_order_lines(raw_order_lines_df, known_customer_legacy_ids={"C001"})
        assert len(result.quarantined) == 1
        assert "referential integrity" in result.quarantined.iloc[0]["rejection_reason"]
        assert len(result.valid) == 1

    def test_all_known_customers_pass(self, raw_order_lines_df):
        result = transform_order_lines(raw_order_lines_df, known_customer_legacy_ids={"C001", "C999"})
        assert len(result.valid) == 2
