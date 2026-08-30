"""Extractor for legacy orders stored in a legacy relational database."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.extract.base import Extractor, ExtractionError


class LegacyOrdersDbExtractor(Extractor):
    """Reads the legacy `orders_legacy` table.

    Expected legacy columns (denormalized — one row per order line, with
    product info repeated on every row):
        order_id, cust_id, product_sku, product_name, qty, unit_price, order_date, status
    """

    required_columns = (
        "order_id",
        "cust_id",
        "product_sku",
        "product_name",
        "qty",
        "unit_price",
        "order_date",
        "status",
    )

    def __init__(self, db_url: str, table_name: str = "orders_legacy", engine: Engine | None = None):
        self.db_url = db_url
        self.table_name = table_name
        # Allow engine injection for testing (e.g. sqlite in-memory).
        self._engine = engine or create_engine(db_url)

    def extract(self) -> pd.DataFrame:
        try:
            with self._engine.connect() as conn:
                df = pd.read_sql(text(f"SELECT * FROM {self.table_name}"), conn)
        except Exception as exc:  # noqa: BLE001 - surfaced as a domain-specific error
            raise ExtractionError(f"Failed to read legacy table '{self.table_name}': {exc}") from exc

        self._validate_columns(df, source_name=self.table_name)
        return df
