"""Minimal read-only HTTP API exposing the latest funnel metric.

Deliberately built on the stdlib http.server rather than adding a web
framework dependency — this is a single read-only endpoint, not a service,
mirroring the same "don't reach for more than the job needs" choice made
for the adobe-analytics-demo collector server.
"""
from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config import get_settings
from src.models.target import FunnelMetric

logger = logging.getLogger(__name__)


def _latest_metric_json(metric_name: str) -> dict | None:
    settings = get_settings()
    engine = create_engine(settings.target_db_url)
    with Session(engine) as session:
        latest = (
            session.query(FunnelMetric)
            .filter(FunnelMetric.metric_name == metric_name)
            .order_by(FunnelMetric.computed_at.desc())
            .first()
        )
    if latest is None:
        return None
    return {
        "metric_name": latest.metric_name,
        "metric_value": float(latest.metric_value),
        "sample_size": latest.sample_size,
        "window_start": latest.window_start,
        "window_end": latest.window_end,
        "computed_at": latest.computed_at,
    }


class MetricsRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (stdlib method name)
        parsed = urlparse(self.path)
        if parsed.path != "/api/metrics/latest":
            self._send_json(404, {"error": "not_found"})
            return

        query = parse_qs(parsed.query)
        metric_name = query.get("metric_name", ["cart_abandonment_rate"])[0]

        try:
            result = _latest_metric_json(metric_name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to read metric %r: %s", metric_name, exc)
            self._send_json(500, {"error": "internal_error"})
            return

        if result is None:
            self._send_json(404, {"error": "no_metric_computed_yet", "metric_name": metric_name})
            return

        self._send_json(200, result)

    def _send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 (stdlib signature)
        logger.info("%s - %s", self.address_string(), format % args)


def serve(port: int = 8001) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), MetricsRequestHandler)
    logger.info("Metrics API serving on http://0.0.0.0:%d/api/metrics/latest", port)
    server.serve_forever()
