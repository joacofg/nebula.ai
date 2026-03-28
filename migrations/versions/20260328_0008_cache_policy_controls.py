"""Add semantic cache tuning columns to tenant_policies.

Revision ID: 20260328_0008
Revises: 20260328_0007
Create Date: 2026-03-28 23:20:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260328_0008"
down_revision = "20260328_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("tenant_policies")}

    if "semantic_cache_similarity_threshold" not in columns:
        op.add_column(
            "tenant_policies",
            sa.Column(
                "semantic_cache_similarity_threshold",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0.9"),
            ),
        )
    if "semantic_cache_max_entry_age_hours" not in columns:
        op.add_column(
            "tenant_policies",
            sa.Column(
                "semantic_cache_max_entry_age_hours",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("168"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("tenant_policies")}

    if "semantic_cache_max_entry_age_hours" in columns:
        op.drop_column("tenant_policies", "semantic_cache_max_entry_age_hours")
    if "semantic_cache_similarity_threshold" in columns:
        op.drop_column("tenant_policies", "semantic_cache_similarity_threshold")
