"""Unit tests for FlagAuditExtractor.

Mirrors the structure of test_flags_client.py, but exercises the fail-loud
path (see flag_audit_reader.py's module docstring) rather than fail-open —
this extractor should never silently swallow a bad fetch.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.extract.base import ExtractionError
from src.extract.flag_audit_reader import FlagAuditExtractor

BASE_URL = "http://localhost:3000"


def _mock_response(json_body: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.text = str(json_body)
    resp.raise_for_status.return_value = None
    return resp


class TestExtractHappyPath:
    @patch("src.extract.flag_audit_reader.requests.get")
    def test_maps_entries_to_expected_columns(self, mock_get):
        mock_get.return_value = _mock_response(
            {
                "count": 1,
                "entries": [
                    {
                        "key": "dark-mode",
                        "action": "toggle",
                        "previousState": {"enabled": False},
                        "newState": {"enabled": True},
                        "actor": "kedar",
                        "timestamp": "2026-08-20T10:00:00.000Z",
                    }
                ],
            }
        )

        df = FlagAuditExtractor(BASE_URL).extract()

        assert list(df.columns) == [
            "flag_key",
            "action",
            "previous_state",
            "new_state",
            "changed_at",
        ]
        assert df.iloc[0]["flag_key"] == "dark-mode"
        assert df.iloc[0]["action"] == "toggle"
        assert df.iloc[0]["changed_at"] == "2026-08-20T10:00:00.000Z"

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_empty_entries_returns_empty_dataframe_with_correct_columns(self, mock_get):
        mock_get.return_value = _mock_response({"count": 0, "entries": []})

        df = FlagAuditExtractor(BASE_URL).extract()

        assert df.empty
        assert list(df.columns) == list(FlagAuditExtractor.required_columns)

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_since_param_passed_when_provided(self, mock_get):
        mock_get.return_value = _mock_response({"count": 0, "entries": []})

        FlagAuditExtractor(BASE_URL, since="2026-08-01T00:00:00Z").extract()

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"since": "2026-08-01T00:00:00Z"}

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_since_omitted_sends_no_params(self, mock_get):
        mock_get.return_value = _mock_response({"count": 0, "entries": []})

        FlagAuditExtractor(BASE_URL).extract()

        _, kwargs = mock_get.call_args
        assert kwargs["params"] is None


class TestExtractFailsLoud:
    """Unlike FlagsClient (fail-open), every one of these must raise."""

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_timeout_raises_extraction_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(ExtractionError, match="Timed out"):
            FlagAuditExtractor(BASE_URL, timeout=5).extract()

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_connection_error_raises_extraction_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(ExtractionError, match="Could not reach toggle-service"):
            FlagAuditExtractor(BASE_URL).extract()

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_http_error_status_raises_extraction_error(self, mock_get):
        resp = _mock_response({"error": "boom"}, status_code=500)
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        mock_get.return_value = resp

        with pytest.raises(ExtractionError, match="500"):
            FlagAuditExtractor(BASE_URL).extract()

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_non_json_response_raises_extraction_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status.return_value = None
        resp.json.side_effect = ValueError("not json")
        resp.text = "<html>not json</html>"
        mock_get.return_value = resp

        with pytest.raises(ExtractionError, match="Non-JSON response"):
            FlagAuditExtractor(BASE_URL).extract()

    @patch("src.extract.flag_audit_reader.requests.get")
    def test_missing_entries_key_raises_extraction_error(self, mock_get):
        mock_get.return_value = _mock_response({"count": 0})  # no "entries"

        with pytest.raises(ExtractionError, match="missing 'entries' key"):
            FlagAuditExtractor(BASE_URL).extract()
