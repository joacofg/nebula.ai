"""Add credential_raw to local_hosted_identity for heartbeat auth.

Revision ID: 20260322_0004
Revises: 20260322_0003
Create Date: 2026-03-22 00:04:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260322_0004"
down_revision = "20260322_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("local_hosted_identity")}
    if "credential_raw" not in cols:
        op.add_column(
            "local_hosted_identity",
            sa.Column("credential_raw", sa.String(255), nullable=False, server_default=""),
        )


def downgrade() -> None:
    op.drop_column("local_hosted_identity", "credential_raw")
