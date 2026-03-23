"""Add last_seen_at and dependency_summary_json to deployments.

Revision ID: 20260322_0003
Revises: 20260321_0002
Create Date: 2026-03-22 00:03:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260322_0003"
down_revision = "20260321_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("deployments")}
    if "last_seen_at" not in cols:
        op.add_column(
            "deployments",
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "dependency_summary_json" not in cols:
        op.add_column(
            "deployments",
            sa.Column("dependency_summary_json", sa.JSON, nullable=True),
        )


def downgrade() -> None:
    op.drop_column("deployments", "dependency_summary_json")
    op.drop_column("deployments", "last_seen_at")
