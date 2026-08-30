"""Load layer: batched, transactional upserts into the target schema.

Key design decisions:
- Each entity type (customers, addresses, products, orders, order_items) is
  loaded in its own transaction-scoped batch loop, in dependency order, so
  a failure never leaves a half-written child row pointing at a missing parent.
- Upserts use Postgres `INSERT ... ON CONFLICT DO UPDATE` (via SQLAlchemy's
  postgresql dialect) keyed on the natural/business key (legacy_id, sku,
  email, etc.), making the whole pipeline safely re-runnable.
- Batching (LOAD_BATCH_SIZE) bounds transaction size and memory even though
  our current volumes are small — it's cheap now and saves a rewrite later.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.models.target import Address, Customer, FlagChangeAudit, Order, OrderItem, Product

logger = logging.getLogger(__name__)


@dataclass
class LoadStats:
    customers_upserted: int = 0
    addresses_upserted: int = 0
    products_upserted: int = 0
    orders_upserted: int = 0
    order_items_upserted: int = 0
    flag_audits_upserted: int = 0


class LoadError(RuntimeError):
    """Raised when a batch fails to commit; caller decides whether to retry/abort."""


def _chunk(records: list[dict], size: int):
    for i in range(0, len(records), size):
        yield records[i : i + size]


def _upsert_batch(
    session: Session,
    model,
    records: list[dict],
    conflict_col: str | list[str],
    update_cols: list[str],
) -> int:
    """Runs one ON CONFLICT DO UPDATE statement for a batch of records.

    `conflict_col` accepts either a single column name or a list, so it
    covers both single-column natural keys (e.g. Product.sku) and composite
    unique constraints (e.g. OrderItem's (order_id, product_id)).
    """
    if not records:
        return 0
    index_elements = [conflict_col] if isinstance(conflict_col, str) else conflict_col
    stmt = pg_insert(model).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_={col: getattr(stmt.excluded, col) for col in update_cols},
    )
    session.execute(stmt)
    return len(records)


class TargetLoader:
    def __init__(self, engine: Engine, batch_size: int = 500):
        self.engine = engine
        self.batch_size = batch_size

    def load_customers(self, session: Session, customers: pd.DataFrame) -> int:
        records = customers[["customer_id", "first_name", "last_name", "email", "phone"]].rename(
            columns={"customer_id": "legacy_id"}
        ).to_dict("records")

        total = 0
        for batch in _chunk(records, self.batch_size):
            try:
                total += _upsert_batch(
                    session, Customer, batch,
                    conflict_col="legacy_id",
                    update_cols=["first_name", "last_name", "email", "phone"],
                )
                session.flush()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                raise LoadError(f"Failed to load customer batch: {exc}") from exc
        return total

    def load_addresses(self, session: Session, customers: pd.DataFrame) -> int:
        # Map legacy customer id -> target Customer.id (needed for the FK).
        legacy_to_id = dict(session.query(Customer.legacy_id, Customer.id).all())

        records = []
        for row in customers.itertuples(index=False):
            customer_id = legacy_to_id.get(row.customer_id)
            if customer_id is None:
                continue  # customer was quarantined upstream; skip its address too
            records.append(
                {
                    "customer_id": customer_id,
                    "line1": row.addr_line,
                    "city": row.city,
                    "state": row.state,
                    "postal_code": row.zip,
                    "is_primary": True,
                }
            )

        total = 0
        for batch in _chunk(records, self.batch_size):
            try:
                session.bulk_insert_mappings(Address, batch)
                session.flush()
                total += len(batch)
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                raise LoadError(f"Failed to load address batch: {exc}") from exc
        return total

    def load_products(self, session: Session, order_lines: pd.DataFrame) -> int:
        # Dedup by SKU — legacy orders repeat product info on every line.
        products = order_lines.drop_duplicates(subset=["product_sku"])[
            ["product_sku", "product_name", "unit_price"]
        ].rename(columns={"product_sku": "sku", "product_name": "name"}).to_dict("records")

        total = 0
        for batch in _chunk(products, self.batch_size):
            try:
                total += _upsert_batch(
                    session, Product, batch,
                    conflict_col="sku",
                    update_cols=["name", "unit_price"],
                )
                session.flush()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                raise LoadError(f"Failed to load product batch: {exc}") from exc
        return total

    def load_orders_and_items(self, session: Session, order_lines: pd.DataFrame) -> tuple[int, int]:
        legacy_cust_to_id = dict(session.query(Customer.legacy_id, Customer.id).all())
        sku_to_id = dict(session.query(Product.sku, Product.id).all())

        # One order per (order_id) header row; items are the line-level rows.
        order_headers = (
            order_lines.drop_duplicates(subset=["order_id"])[["order_id", "cust_id", "order_date", "status"]]
        )
        order_records = []
        for row in order_headers.itertuples(index=False):
            customer_id = legacy_cust_to_id.get(str(row.cust_id))
            if customer_id is None:
                continue
            order_records.append(
                {
                    "legacy_order_id": str(row.order_id),
                    "customer_id": customer_id,
                    "order_date": row.order_date,
                    "status": row.status,
                }
            )

        orders_loaded = 0
        for batch in _chunk(order_records, self.batch_size):
            try:
                orders_loaded += _upsert_batch(
                    session, Order, batch,
                    conflict_col="legacy_order_id",
                    update_cols=["customer_id", "order_date", "status"],
                )
                session.flush()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                raise LoadError(f"Failed to load order batch: {exc}") from exc

        legacy_order_to_id = dict(session.query(Order.legacy_order_id, Order.id).all())
        item_records = []
        for row in order_lines.itertuples(index=False):
            order_id = legacy_order_to_id.get(str(row.order_id))
            product_id = sku_to_id.get(row.product_sku)
            if order_id is None or product_id is None:
                continue
            item_records.append(
                {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": int(row.qty),
                    "unit_price_at_order": float(row.unit_price),
                }
            )

        items_loaded = 0
        for batch in _chunk(item_records, self.batch_size):
            try:
                items_loaded += _upsert_batch(
                    session, OrderItem, batch,
                    conflict_col=["order_id", "product_id"],  # matches uq_order_product constraint
                    update_cols=["quantity", "unit_price_at_order"],
                )
                session.flush()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                raise LoadError(f"Failed to load order_item batch: {exc}") from exc

        return orders_loaded, items_loaded

    def load_flag_audit(self, session: Session, flag_audit: pd.DataFrame) -> int:
        """No FK dependency — flags live in the toggle service, not this
        database — so this can run anywhere in the load sequence, including
        in parallel with the customer/order chain if that's ever useful.
        Natural key is (flag_key, changed_at); only the non-key columns are
        updated on conflict, since a duplicate natural key means this is a
        re-fetch of the same audit entry, not a new one.
        """
        records = flag_audit[["flag_key", "action", "previous_state", "new_state", "changed_at"]].to_dict(
            "records"
        )
        total = 0
        for batch in _chunk(records, self.batch_size):
            try:
                total += _upsert_batch(
                    session, FlagChangeAudit, batch,
                    conflict_col=["flag_key", "changed_at"],
                    update_cols=["action", "previous_state", "new_state"],
                )
                session.flush()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                raise LoadError(f"Failed to load flag_audit batch: {exc}") from exc
        return total
