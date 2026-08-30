"""Tiny JSON state file for tracking 'last successful run' timestamps.

Deliberately minimal — a single {key: iso_timestamp} file, not a database
table, since it only needs to survive between CLI invocations on one host.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_STATE_PATH = Path(".migration_state.json")


def read_last_success(state_path: Path, key: str) -> str | None:
    if not state_path.exists():
        return None
    try:
        data = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return data.get(key)


def write_last_success(state_path: Path, key: str, timestamp: str) -> None:
    data = {}
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}
    data[key] = timestamp
    state_path.write_text(json.dumps(data, indent=2))
