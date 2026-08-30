"""add flag_change_audits table

Revision ID: cf2fcc07b199
Revises: 0001
Create Date: 2026-08-22 16:14:07.542817
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'cf2fcc07b199'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('flag_change_audits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('flag_key', sa.String(length=64), nullable=False),
    sa.Column('action', sa.String(length=32), nullable=False),
    sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('changed_at', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('flag_key', 'changed_at', name='uq_flag_key_changed_at')
    )
    op.create_index(op.f('ix_flag_change_audits_flag_key'), 'flag_change_audits', ['flag_key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_flag_change_audits_flag_key'), table_name='flag_change_audits')
    op.drop_table('flag_change_audits')
