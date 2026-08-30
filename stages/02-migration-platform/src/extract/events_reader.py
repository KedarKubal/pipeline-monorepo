"""Extractor for the pipeline's Stage 1 event stream.

Reads the append-only JSONL file the demo-site's collector server writes
to (see stages/01-adobe-analytics-demo/demo-site/server.js). Malformed
individual lines are skipped with a warning rather than failing the whole
extract — a single corrupted line (e.g. from a concurrent partial write)
shouldn't block every other event in the file.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from src.extract.base import Extractor, ExtractionError

logger = logging.getLogger(__name__)


class AnalyticsEventsExtractor(Extractor):
    """Reads events.jsonl produced by the adobe-analytics-demo collector.

    Each line is one JSON object with at minimum `event` and `timestamp`
    keys; other keys vary by event type (sku, price, orderId, total, ...)
    and are preserved as extra columns via pd.json_normalize.
    """

    required_columns = ("event", "timestamp")

    def __init__(self, events_path: str | Path):
        self.events_path = Path(events_path)

    def extract(self) -> pd.DataFrame:
        if not self.events_path.exists():
            raise ExtractionError(f"Events source not found: {self.events_path}")

        records: list[dict] = []
        with self.events_path.open("r") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Skipping unparsable line %d in %s: %s", line_no, self.events_path, exc
                    )

        if not records:
            return pd.DataFrame(columns=list(self.required_columns))

        df = pd.json_normalize(records)
        self._validate_columns(df, source_name=str(self.events_path))
        return df
