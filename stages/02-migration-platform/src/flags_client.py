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
    
    def set_enabled(self, key: str, *, enabled: bool, api_key: str, description: str = "") -> None:
        """Sets a flag's enabled state, creating it first if it doesn't exist.

        Unlike is_enabled(), this does NOT fail open — a flag write is a
        decision this pipeline is making (e.g. "raise the cart-abandonment
        alert"), and there's no safe default for "did that decision get
        recorded or not." Raises RuntimeError on any failure so the caller
        (the CLI) can surface it loudly rather than silently no-op.
        """
        headers = {"X-API-Key": api_key}
        patch_url = f"{self._base_url}/api/flags/{key}"

        try:
            response = httpx.patch(patch_url, json={"enabled": enabled}, headers=headers, timeout=self._timeout)
            if response.status_code == 404:
                # Flag doesn't exist yet — create it, already in the desired state.
                create_response = httpx.post(
                    f"{self._base_url}/api/flags",
                    json={
                        "key": key,
                        "description": description or f"Auto-managed by migration-platform pipeline.",
                        "enabled": enabled,
                        "environments": ["development", "staging", "production"],
                    },
                    headers=headers,
                    timeout=self._timeout,
                )
                create_response.raise_for_status()
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Failed to set flag {key!r} to enabled={enabled}: HTTP {exc.response.status_code} — {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Failed to set flag {key!r} to enabled={enabled}: {exc}") from exc

        self._cache[key] = enabled
