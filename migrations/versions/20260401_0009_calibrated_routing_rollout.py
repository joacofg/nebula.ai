"""Add calibrated routing rollout control to tenant_policies.

Revision ID: 20260401_0009
Revises: 20260328_0008
Create Date: 2026-04-01 23:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260401_0009"
down_revision = "20260328_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("tenant_policies")}

    if "calibrated_routing_enabled" not in columns:
        op.add_column(
            "tenant_policies",
            sa.Column(
                "calibrated_routing_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("tenant_policies")}

    if "calibrated_routing_enabled" in columns:
        op.drop_column("tenant_policies", "calibrated_routing_enabled")
