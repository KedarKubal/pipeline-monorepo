"""Target (normalized) schema ORM models.

Normalization decisions, and why:
- `Customer` no longer stores a single free-text address or "full_name" —
  the legacy source mixed those together, which made dedup and search fragile.
- `Address` is split out 1:N per customer (a customer may have shipping vs
  billing addresses; the legacy system only ever captured one).
- `Product` is deduplicated by SKU. The legacy orders table repeated product
  name/price on every order row (a classic denormalized flat-file pattern).
- `Order` / `OrderItem` follow a standard header/line-item split so a single
  order can contain multiple products.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from src.models.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    legacy_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    addresses: Mapped[list["Address"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=True, nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="addresses")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    legacy_order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    order_date: Mapped[str] = mapped_column(String(32), nullable=False)  # ISO date string
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "product_id", name="uq_order_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price_at_order: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


class FlagChangeAudit(Base, TimestampMixin):
    """Audit trail of feature-flag changes, sourced from config-toggle-service's
    audit log. Not linked by FK to anything else in this schema — flags live
    in the toggle service, not in this database — so this table has no
    dependents in the load order (see load/loader.py).
    """
    __tablename__ = "flag_change_audits"
    __table_args__ = (UniqueConstraint("flag_key", "changed_at", name="uq_flag_key_changed_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    flag_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # create | update | toggle | delete
    previous_state: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )
    new_state: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )
    changed_at: Mapped[str] = mapped_column(String(32), nullable=False)  # ISO timestamp string


class FunnelMetric(Base, TimestampMixin):
    """A computed pipeline insight (e.g. cart_abandonment_rate), sourced
    from adobe-analytics-demo events via migration-platform's ETL. No FK
    dependency on anything else — a time-series metric table, natural key
    is (metric_name, window_start, window_end) so re-running the same
    window is an idempotent upsert, not a duplicate row.
    """
    __tablename__ = "funnel_metrics"
    __table_args__ = (
        UniqueConstraint("metric_name", "window_start", "window_end", name="uq_metric_window"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    sample_size: Mapped[int] = mapped_column(nullable=False, default=0)
    window_start: Mapped[str] = mapped_column(String(32), nullable=False)
    window_end: Mapped[str] = mapped_column(String(32), nullable=False)
    computed_at: Mapped[str] = mapped_column(String(32), nullable=False)
