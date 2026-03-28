"""Add hard budget guardrail columns to tenant_policies.

Revision ID: 20260328_0007
Revises: 20260326_0006
Create Date: 2026-03-28 00:07:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260328_0007"
down_revision = "20260326_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("tenant_policies")}

    if "hard_budget_limit_usd" not in columns:
        op.add_column("tenant_policies", sa.Column("hard_budget_limit_usd", sa.Float(), nullable=True))
    if "hard_budget_enforcement" not in columns:
        op.add_column(
            "tenant_policies",
            sa.Column("hard_budget_enforcement", sa.String(length=32), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("tenant_policies")}

    if "hard_budget_enforcement" in columns:
        op.drop_column("tenant_policies", "hard_budget_enforcement")
    if "hard_budget_limit_usd" in columns:
        op.drop_column("tenant_policies", "hard_budget_limit_usd")
