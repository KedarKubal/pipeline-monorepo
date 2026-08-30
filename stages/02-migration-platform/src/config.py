"""Centralized configuration loaded from environment variables.

Keeping DB URLs and tunables here (rather than scattered os.getenv calls)
gives one place to validate config at startup and fail fast with a clear
error instead of a cryptic connection failure three layers deep.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    target_db_url: str
    legacy_db_url: str
    load_batch_size: int

    @classmethod
    def from_env(cls) -> "Settings":
        target_db_url = os.getenv("TARGET_DB_URL")
        legacy_db_url = os.getenv("LEGACY_DB_URL")
        batch_size_raw = os.getenv("LOAD_BATCH_SIZE", "500")

        if not target_db_url:
            raise ConfigError("TARGET_DB_URL is not set. Copy .env.example to .env and fill it in.")
        if not legacy_db_url:
            raise ConfigError("LEGACY_DB_URL is not set. Copy .env.example to .env and fill it in.")
        try:
            batch_size = int(batch_size_raw)
        except ValueError as exc:
            raise ConfigError(f"LOAD_BATCH_SIZE must be an integer, got {batch_size_raw!r}") from exc
        if batch_size <= 0:
            raise ConfigError("LOAD_BATCH_SIZE must be a positive integer.")

        return cls(
            target_db_url=target_db_url,
            legacy_db_url=legacy_db_url,
            load_batch_size=batch_size,
        )


def get_settings() -> Settings:
    return Settings.from_env()
