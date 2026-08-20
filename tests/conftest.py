"""Shared pytest fixtures."""
from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def raw_customers_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_id": "C001", "full_name": "Jane Doe", "email": "Jane.Doe@Example.com",
                "phone": "(555) 123-4567", "addr_line": "123 Main St", "city": "Springfield",
                "state": "IL", "zip": "62701", "signup_date": "2023-01-15",
            },
            {
                "customer_id": "C002", "full_name": "John Smith", "email": "john.smith@example.com",
                "phone": "555-234-5678", "addr_line": "456 Oak Ave", "city": "Chicago",
                "state": "IL", "zip": "60601", "signup_date": "2023-02-20",
            },
            {
                "customer_id": "C003", "full_name": "Bad Email", "email": "not-an-email",
                "phone": None, "addr_line": "789 Pine Rd", "city": "Peoria",
                "state": "IL", "zip": "61601", "signup_date": "2023-03-10",
            },
        ]
    )


@pytest.fixture
def raw_order_lines_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_id": "O1001", "cust_id": "C001", "product_sku": "SKU-100",
                "product_name": "Widget Large", "qty": 2, "unit_price": 19.99,
                "order_date": "2023-06-01", "status": "shipped",
            },
            {
                "order_id": "O1002", "cust_id": "C999", "product_sku": "SKU-200",
                "product_name": "Widget Small", "qty": 1, "unit_price": 9.99,
                "order_date": "2023-06-15", "status": "pending",
            },
        ]
    )
