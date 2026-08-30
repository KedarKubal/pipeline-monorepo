"""CLI entrypoint for running the migration pipeline.

Usage:
    python -m src.orchestration.cli run --customers-csv sample_data/customers_legacy.csv
    python -m src.orchestration.cli run --customers-csv <path> --legacy-orders-table orders_legacy
"""
from __future__ import annotations

import logging
import sys

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config import ConfigError, get_settings
from src.extract.csv_reader import CustomerCsvExtractor
from src.extract.legacy_db_reader import LegacyOrdersDbExtractor
from src.load.loader import LoadError, TargetLoader
from src.transform.pipeline import transform_customers, transform_order_lines

from datetime import datetime, timezone
from pathlib import Path

from src.flags_client import FlagsClient
from src.extract.flag_audit_reader import FlagAuditExtractor
from src.extract.events_reader import AnalyticsEventsExtractor
from src.orchestration.state import DEFAULT_STATE_PATH, read_last_success, write_last_success
from src.transform.pipeline import transform_flag_audit, transform_analytics_events
from src.transform.aggregations import compute_funnel_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")


@click.group()
def cli():
    """Migration platform CLI."""


@cli.command()
@click.option(
    "--toggle-service-url",
    default="http://localhost:3000",
    envvar="TOGGLE_SERVICE_URL",
    help="Base URL of config-toggle-service.",
)
@click.option("--customers-csv", required=True, type=click.Path(exists=True), help="Path to legacy customers CSV.")
@click.option("--legacy-orders-table", default="orders_legacy", help="Legacy DB table name for order lines.")
@click.option("--dry-run", is_flag=True, help="Run extract+transform and report stats without writing to the target DB.")
def run(customers_csv: str, legacy_orders_table: str, dry_run: bool, toggle_service_url: str):
    """Run the full extract -> transform -> load pipeline."""
    try:
        settings = get_settings()
    except ConfigError as exc:
        logger.error(str(exc))
        sys.exit(1)

    flags = FlagsClient(toggle_service_url)
    strict_email = flags.is_enabled("strict-email-validation", default=False)
    logger.info("strict-email-validation flag resolved to: %s", strict_email)

    # --- Extract ---
    logger.info("Extracting customers from %s", customers_csv)
    raw_customers = CustomerCsvExtractor(customers_csv).extract()

    logger.info("Extracting order lines from legacy table '%s'", legacy_orders_table)
    raw_orders = LegacyOrdersDbExtractor(settings.legacy_db_url, table_name=legacy_orders_table).extract()

    # --- Transform ---
    customer_result = transform_customers(raw_customers, strict_email=strict_email)
    logger.info("Customer transform: %s", customer_result.summary())

    known_ids = set(customer_result.valid["customer_id"].astype(str))
    order_result = transform_order_lines(raw_orders, known_customer_legacy_ids=known_ids)
    logger.info("Order line transform: %s", order_result.summary())

    if len(customer_result.quarantined) or len(order_result.quarantined):
        logger.warning(
            "Quarantined %d customer rows and %d order line rows — see logs above for reasons.",
            len(customer_result.quarantined),
            len(order_result.quarantined),
        )

    if dry_run:
        logger.info("Dry run complete. No data was written to the target database.")
        return

    # --- Load ---
    engine = create_engine(settings.target_db_url)
    loader = TargetLoader(engine, batch_size=settings.load_batch_size)

    try:
        with Session(engine) as session:
            n_customers = loader.load_customers(session, customer_result.valid)
            n_addresses = loader.load_addresses(session, customer_result.valid)
            n_products = loader.load_products(session, order_result.valid)
            n_orders, n_items = loader.load_orders_and_items(session, order_result.valid)
            session.commit()
    except LoadError as exc:
        logger.error("Load failed and was rolled back: %s", exc)
        sys.exit(1)

    logger.info(
        "Load complete: customers=%d addresses=%d products=%d orders=%d order_items=%d",
        n_customers, n_addresses, n_products, n_orders, n_items,
    )


@cli.command("sync-flags-audit")
@click.option(
    "--toggle-service-url",
    default="http://localhost:3000",
    envvar="TOGGLE_SERVICE_URL",
    help="Base URL of config-toggle-service.",
)
@click.option(
    "--flags-audit-since",
    default=None,
    help="ISO 8601 timestamp. Defaults to the last successful sync recorded in the state file.",
)
@click.option(
    "--state-file",
    default=str(DEFAULT_STATE_PATH),
    type=click.Path(),
    help="Path to the JSON file tracking last-successful-run timestamps.",
)
@click.option("--dry-run", is_flag=True, help="Extract+transform and report stats without writing to the target DB.")
def sync_flags_audit(toggle_service_url: str, flags_audit_since: str | None, state_file: str, dry_run: bool):
    """Sync the toggle-service flag-change audit log into the target DB.

    Independent of the customers/orders pipeline — flag audit rows have no
    FK dependency on anything else in the target schema, so this can run
    on its own schedule (e.g. a more frequent cron than the main migration).
    """
    try:
        settings = get_settings()
    except ConfigError as exc:
        logger.error(str(exc))
        sys.exit(1)

    state_path = Path(state_file)
    since = flags_audit_since or read_last_success(state_path, key="flags_audit")
    if since:
        logger.info("Syncing flag audit entries since %s", since)
    else:
        logger.info("No prior sync recorded — fetching full flag audit log")

    # --- Extract ---
    raw_audit = FlagAuditExtractor(toggle_service_url, since=since).extract()

    # --- Transform ---
    audit_result = transform_flag_audit(raw_audit)
    logger.info("Flag audit transform: %s", audit_result.summary())
    if len(audit_result.quarantined):
        logger.warning(
            "Quarantined %d flag audit rows — see logs above for reasons.",
            len(audit_result.quarantined),
        )

    if dry_run:
        logger.info("Dry run complete. No data was written to the target database.")
        return

    sync_completed_at = datetime.now(timezone.utc).isoformat()

    # --- Load ---
    engine = create_engine(settings.target_db_url)
    loader = TargetLoader(engine, batch_size=settings.load_batch_size)
    try:
        with Session(engine) as session:
            n_audit = loader.load_flag_audit(session, audit_result.valid)
            session.commit()
    except LoadError as exc:
        logger.error("Load failed and was rolled back: %s", exc)
        sys.exit(1)

    write_last_success(state_path, key="flags_audit", timestamp=sync_completed_at)
    logger.info("Flag audit sync complete: flag_audits=%d (watermark updated to %s)", n_audit, sync_completed_at)


@cli.command("run-funnel-metrics")
@click.option(
    "--events-file",
    default="../01-adobe-analytics-demo/demo-site/data/events.jsonl",
    type=click.Path(),
    help="Path to the events.jsonl file produced by adobe-analytics-demo's collector server.",
)
@click.option("--window-hours", default=24, help="Trailing window (in hours) to compute the funnel metric over.")
@click.option("--dry-run", is_flag=True, help="Extract+transform+aggregate and report stats without writing to the target DB.")
def run_funnel_metrics(events_file: str, window_hours: int, dry_run: bool):
    """Pipeline Stage 2: extract raw analytics events, validate, and
    aggregate into a funnel metric (cart_abandonment_rate) in the target DB.

    This is Stage 1 -> Stage 2 of the linear pipeline: adobe-analytics-demo
    emits events, this command turns them into a queryable insight.
    """
    try:
        settings = get_settings()
    except ConfigError as exc:
        logger.error(str(exc))
        sys.exit(1)

    events_path = Path(events_file)
    if not events_path.exists():
        logger.error(
            "Events file not found: %s. Has the demo site recorded any events yet?", events_path
        )
        sys.exit(1)

    # --- Extract ---
    logger.info("Extracting events from %s", events_path)
    raw_events = AnalyticsEventsExtractor(events_path).extract()

    # --- Transform (row-level validation) ---
    events_result = transform_analytics_events(raw_events)
    logger.info("Analytics events transform: %s", events_result.summary())
    if len(events_result.quarantined):
        logger.warning(
            "Quarantined %d event rows — see logs above for reasons.",
            len(events_result.quarantined),
        )

    # --- Aggregate ---
    metrics_df = compute_funnel_metrics(events_result.valid, window_hours=window_hours)
    metric_row = metrics_df.iloc[0]
    logger.info(
        "Computed %s = %.4f (sample_size=%d, window=%s..%s)",
        metric_row["metric_name"], metric_row["metric_value"], metric_row["sample_size"],
        metric_row["window_start"], metric_row["window_end"],
    )

    if dry_run:
        logger.info("Dry run complete. No data was written to the target database.")
        return

    # --- Load ---
    engine = create_engine(settings.target_db_url)
    loader = TargetLoader(engine, batch_size=settings.load_batch_size)
    try:
        with Session(engine) as session:
            n_metrics = loader.load_funnel_metrics(session, metrics_df)
            session.commit()
    except LoadError as exc:
        logger.error("Load failed and was rolled back: %s", exc)
        sys.exit(1)

    logger.info("Funnel metrics load complete: funnel_metrics=%d", n_metrics)


@cli.command("sync-alert-flag")
@click.option(
    "--toggle-service-url",
    default="http://localhost:3000",
    envvar="TOGGLE_SERVICE_URL",
    help="Base URL of config-toggle-service.",
)
@click.option(
    "--metric-name",
    default="cart_abandonment_rate",
    help="Which funnel_metrics row (by metric_name) to evaluate.",
)
def sync_alert_flag(toggle_service_url: str, metric_name: str):
    """Pipeline Stage 3: read the latest funnel metric and write the
    high-cart-abandonment-alert flag on config-toggle-service accordingly.

    This is Stage 2 -> Stage 3 of the linear pipeline: the computed metric
    becomes a decision, expressed as a flag flip. Fails loudly (does not
    fail open) if the write itself fails — see FlagsClient.set_enabled.
    """
    try:
        settings = get_settings()
    except ConfigError as exc:
        logger.error(str(exc))
        sys.exit(1)

    if not settings.toggle_service_api_key:
        logger.error(
            "TOGGLE_SERVICE_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
        sys.exit(1)

    # --- Read latest metric from the target DB ---
    from src.models.target import FunnelMetric  # local import avoids a cycle at module load time

    engine = create_engine(settings.target_db_url)
    with Session(engine) as session:
        latest = (
            session.query(FunnelMetric)
            .filter(FunnelMetric.metric_name == metric_name)
            .order_by(FunnelMetric.computed_at.desc())
            .first()
        )

    if latest is None:
        logger.error(
            "No %s metric found in the target DB yet. Run 'run-funnel-metrics' first.", metric_name
        )
        sys.exit(1)

    threshold = settings.cart_abandonment_alert_threshold
    should_alert = float(latest.metric_value) >= threshold
    logger.info(
        "Latest %s = %.4f (threshold=%.4f) -> alert=%s",
        metric_name, float(latest.metric_value), threshold, should_alert,
    )

    # --- Write the decision as a flag flip ---
    flags = FlagsClient(toggle_service_url)
    try:
        flags.set_enabled(
            "high-cart-abandonment-alert",
            enabled=should_alert,
            api_key=settings.toggle_service_api_key,
            description="Auto-managed by migration-platform: flips on when cart_abandonment_rate crosses threshold.",
        )
    except RuntimeError as exc:
        logger.error("Failed to sync alert flag: %s", exc)
        sys.exit(1)

    logger.info("high-cart-abandonment-alert set to %s", should_alert)


if __name__ == "__main__":
    cli()
