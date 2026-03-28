"""Add route_signals JSON column to usage_ledger.

Revision ID: 20260326_0006
Revises: 20260322_0005
Create Date: 2026-03-26 00:06:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260326_0006"
down_revision = "20260322_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("usage_ledger")}
    if "route_signals" not in columns:
        op.add_column("usage_ledger", sa.Column("route_signals", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("usage_ledger")}
    if "route_signals" in columns:
        op.drop_column("usage_ledger", "route_signals")
