"""Extractor for the Toggle Service's flag-change audit log.

Polls `GET /api/flags/audit?since=<ISO timestamp>` on config-toggle-service
and returns the raw audit entries as a DataFrame. Unlike flags_client.py
(the runtime decision gate, which fails open), this extractor fails loudly
on a bad fetch — a silently-skipped audit batch would mean the pipeline
reports success while quietly missing data, which the rest of this project
avoids on purpose (see "quarantine, don't crash" in the README).
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.extract.base import Extractor, ExtractionError

DEFAULT_TIMEOUT_SECONDS = 10


class FlagAuditExtractor(Extractor):
    """Reads flag-change audit entries from config-toggle-service.

    Expected API response shape (see GET /api/flags/audit):
        {"count": int, "entries": [
            {"key": str, "action": str, "previousState": dict | None,
             "newState": dict | None, "actor": str, "timestamp": str}, ...
        ]}
    """

    required_columns = (
        "flag_key",
        "action",
        "previous_state",
        "new_state",
        "changed_at",
    )

    def __init__(
        self,
        base_url: str,
        since: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        """
        Args:
            base_url: e.g. "http://localhost:3000" — no trailing slash.
            since: ISO 8601 timestamp; only entries at/after this time are
                fetched. None fetches the full audit log.
            timeout: request timeout in seconds — a hung toggle-service
                should not hang the whole migration run.
        """
        self.base_url = base_url.rstrip("/")
        self.since = since
        self.timeout = timeout

    def extract(self) -> pd.DataFrame:
        url = f"{self.base_url}/api/flags/audit"
        params = {"since": self.since} if self.since else None

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise ExtractionError(
                f"Timed out after {self.timeout}s fetching audit log from {url}"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ExtractionError(
                f"Could not reach toggle-service at {url}. Is it running?"
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise ExtractionError(
                f"Toggle service returned {response.status_code} for {url}: {response.text}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExtractionError(f"Non-JSON response from {url}: {response.text[:200]}") from exc

        entries: list[dict[str, Any]] = payload.get("entries")
        if entries is None:
            raise ExtractionError(f"Unexpected response shape from {url}: missing 'entries' key")

        df = self._to_dataframe(entries)
        self._validate_columns(df, source_name=url)
        return df

    @staticmethod
    def _to_dataframe(entries: list[dict[str, Any]]) -> pd.DataFrame:
        if not entries:
            return pd.DataFrame(columns=FlagAuditExtractor.required_columns)

        return pd.DataFrame(
            {
                "flag_key": [e.get("key") for e in entries],
                "action": [e.get("action") for e in entries],
                "previous_state": [e.get("previousState") for e in entries],
                "new_state": [e.get("newState") for e in entries],
                "changed_at": [e.get("timestamp") for e in entries],
            }
        )
