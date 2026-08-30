"""Aggregation logic for turning validated event rows into funnel metrics.

Kept separate from transform/pipeline.py (row-level clean+validate) since
this step aggregates many rows into one summary row — a different shape
of operation, still a pure function for the same testability reasons.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd


def compute_funnel_metrics(
    events: pd.DataFrame,
    *,
    window_hours: int = 24,
    now: datetime | None = None,
) -> pd.DataFrame:
    """Computes cart_abandonment_rate over the trailing `window_hours`.

    abandonment_rate = (add_to_cart_count - purchase_count) / add_to_cart_count
    Returns 0.0 (not an alert-worthy state) when there's no cart activity
    in the window at all, rather than dividing by zero.
    """
    now = now or datetime.now(timezone.utc)
    window_start = now - timedelta(hours=window_hours)

    ts = pd.to_datetime(events["timestamp"], errors="coerce", utc=True)
    in_window = events[(ts >= window_start) & (ts <= now)]

    add_to_cart_count = int((in_window["event"] == "add_to_cart").sum())
    purchase_count = int((in_window["event"] == "purchase").sum())

    if add_to_cart_count > 0:
        abandonment_rate = round((add_to_cart_count - purchase_count) / add_to_cart_count, 4)
    else:
        abandonment_rate = 0.0

    return pd.DataFrame([{
        "metric_name": "cart_abandonment_rate",
        "metric_value": abandonment_rate,
        "sample_size": add_to_cart_count,
        "window_start": window_start.isoformat(),
        "window_end": now.isoformat(),
        "computed_at": now.isoformat(),
    }])
