"""add funnel metrics table

Revision ID: de8e39201ef1
Revises: cf2fcc07b199
Create Date: 2026-08-30 15:52:25.732766
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'de8e39201ef1'
down_revision: Union[str, None] = 'cf2fcc07b199'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "funnel_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("metric_name", sa.String(64), nullable=False),
        sa.Column("metric_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("window_start", sa.String(32), nullable=False),
        sa.Column("window_end", sa.String(32), nullable=False),
        sa.Column("computed_at", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("metric_name", "window_start", "window_end", name="uq_metric_window"),
    )
    op.create_index("ix_funnel_metrics_metric_name", "funnel_metrics", ["metric_name"])


def downgrade() -> None:
    op.drop_index("ix_funnel_metrics_metric_name", table_name="funnel_metrics")
    op.drop_table("funnel_metrics")
