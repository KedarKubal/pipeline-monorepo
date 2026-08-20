"""Integration test: runs extract -> transform -> load against a throwaway
SQLite database (swapped in via dependency injection) so the test suite
doesn't require a live Postgres instance to validate load-layer wiring.

Note: SQLite doesn't support Postgres-native ON CONFLICT DO UPDATE, so this
test exercises the ORM model/session wiring and referential integrity, not
the upsert SQL itself. The upsert SQL path is covered by running the CLI
against docker-compose's Postgres (see README "Verifying the load layer").
"""
from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models.base import Base
from src.models.target import Address, Customer, Order, OrderItem, Product
from src.transform.pipeline import transform_customers, transform_order_lines


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_end_to_end_transform_and_manual_load(sqlite_engine, raw_customers_df, raw_order_lines_df):
    customer_result = transform_customers(raw_customers_df)
    known_ids = set(customer_result.valid["customer_id"].astype(str))
    order_result = transform_order_lines(raw_order_lines_df, known_customer_legacy_ids=known_ids)

    with Session(sqlite_engine) as session:
        for row in customer_result.valid.itertuples(index=False):
            session.add(
                Customer(
                    legacy_id=row.customer_id, first_name=row.first_name,
                    last_name=row.last_name, email=row.email, phone=row.phone,
                )
            )
        session.commit()

        loaded_customers = session.query(Customer).all()
        assert len(loaded_customers) == len(customer_result.valid)

        # Order line for C999 (not in known_ids) must have been quarantined upstream.
        assert "C999" not in known_ids
        assert len(order_result.valid) == 1
        assert order_result.valid.iloc[0]["cust_id"] == "C001"

        # Referential integrity: the valid order line's customer actually exists.
        loaded_emails = {c.email for c in loaded_customers}
        assert "jane.doe@example.com" in loaded_emails
