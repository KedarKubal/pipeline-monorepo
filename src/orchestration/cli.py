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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")


@click.group()
def cli():
    """Migration platform CLI."""


@cli.command()
@click.option("--customers-csv", required=True, type=click.Path(exists=True), help="Path to legacy customers CSV.")
@click.option("--legacy-orders-table", default="orders_legacy", help="Legacy DB table name for order lines.")
@click.option("--dry-run", is_flag=True, help="Run extract+transform and report stats without writing to the target DB.")
def run(customers_csv: str, legacy_orders_table: str, dry_run: bool):
    """Run the full extract -> transform -> load pipeline."""
    try:
        settings = get_settings()
    except ConfigError as exc:
        logger.error(str(exc))
        sys.exit(1)

    # --- Extract ---
    logger.info("Extracting customers from %s", customers_csv)
    raw_customers = CustomerCsvExtractor(customers_csv).extract()

    logger.info("Extracting order lines from legacy table '%s'", legacy_orders_table)
    raw_orders = LegacyOrdersDbExtractor(settings.legacy_db_url, table_name=legacy_orders_table).extract()

    # --- Transform ---
    customer_result = transform_customers(raw_customers)
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


if __name__ == "__main__":
    cli()
