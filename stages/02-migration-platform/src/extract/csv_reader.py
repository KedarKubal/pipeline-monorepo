"""Extractor for legacy customer data delivered as CSV."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.extract.base import Extractor, ExtractionError


class CustomerCsvExtractor(Extractor):
    """Reads the legacy `customers_legacy.csv` export.

    Expected legacy columns (deliberately messy, as real legacy exports are):
        customer_id, full_name, email, phone, addr_line, city, state, zip, signup_date
    """

    required_columns = (
        "customer_id",
        "full_name",
        "email",
        "phone",
        "addr_line",
        "city",
        "state",
        "zip",
        "signup_date",
    )

    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)

    def extract(self) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise ExtractionError(f"CSV source not found: {self.csv_path}")

        try:
            # dtype=str keeps legacy IDs (e.g. zero-padded) intact; we coerce
            # types explicitly and deliberately in the transform layer instead
            # of letting pandas guess.
            df = pd.read_csv(self.csv_path, dtype=str, keep_default_na=False, na_values=["", "NULL", "null", "N/A"])
        except pd.errors.ParserError as exc:
            raise ExtractionError(f"Failed to parse CSV {self.csv_path}: {exc}") from exc

        self._validate_columns(df, source_name=str(self.csv_path))
        return df
