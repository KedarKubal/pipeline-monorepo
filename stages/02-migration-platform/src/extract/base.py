"""Common extractor contract.

Every extractor — regardless of source format — returns a plain pandas
DataFrame. This is the seam that lets transform/load stay source-agnostic:
add a new source format by writing one new Extractor subclass, nothing
downstream changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class ExtractionError(RuntimeError):
    """Raised when a source cannot be read or fails structural validation."""


class Extractor(ABC):
    """Base class for all source readers."""

    #: Columns the extracted DataFrame must contain. Subclasses set this.
    required_columns: tuple[str, ...] = ()

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Read the source and return a raw (untransformed) DataFrame."""
        raise NotImplementedError

    def _validate_columns(self, df: pd.DataFrame, source_name: str) -> None:
        missing = set(self.required_columns) - set(df.columns)
        if missing:
            raise ExtractionError(
                f"{source_name} is missing required columns: {sorted(missing)}. "
                f"Found columns: {list(df.columns)}"
            )
