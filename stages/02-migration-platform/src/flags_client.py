"""
Runtime feature-flag client for the Migration Platform.

Fetches flag state from the Config Toggle Service. Fails open (returns a
safe default) on any network error, timeout, or malformed response — a
missing/down flag service must never crash a migration run, consistent
with this project's "quarantine, don't crash" philosophy.
"""
from __future__ import annotations

import logging
from typing import Dict

import httpx

logger = logging.getLogger(__name__)


class FlagsClient:
    """Thin, cached client for reading feature flags at runtime.

    One instance is meant to live for the duration of a single migration
    run. Each key is fetched once and cached in-memory — a migration run
    is a batch job, not a long-lived server, so mid-run flag flips aren't
    a concern.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 2.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._cache: Dict[str, bool] = {}

    def is_enabled(self, key: str, *, default: bool = False) -> bool:
        """Return whether `key` is enabled, caching the result for this run.

        Never raises. Falls back to `default` on HTTP errors, connection
        errors, timeouts, or an unparseable body.
        """
        if key in self._cache:
            return self._cache[key]

        enabled = default
        try:
            response = httpx.get(
                f"{self._base_url}/api/flags/{key}",
                timeout=self._timeout,
            )
            response.raise_for_status()
            body = response.json()
            enabled = bool(body.get("enabled", default))
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Flag %r lookup returned HTTP %s; failing open to %s",
                key, exc.response.status_code, default,
            )
        except (httpx.RequestError, ValueError) as exc:
            logger.warning(
                "Flag %r lookup failed (%s); failing open to %s",
                key, exc, default,
            )

        self._cache[key] = enabled
        return enabled
