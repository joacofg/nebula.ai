"""Add evidence governance policy and ledger markers.

Revision ID: 20260411_0010
Revises: 20260401_0009
Create Date: 2026-04-11 20:58:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260411_0010"
down_revision = "20260401_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tenant_policy_columns = {col["name"] for col in inspector.get_columns("tenant_policies")}
    usage_ledger_columns = {col["name"] for col in inspector.get_columns("usage_ledger")}

    if "evidence_retention_window" not in tenant_policy_columns:
        op.add_column(
            "tenant_policies",
            sa.Column(
                "evidence_retention_window",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'30d'"),
            ),
        )
    if "metadata_minimization_level" not in tenant_policy_columns:
        op.add_column(
            "tenant_policies",
            sa.Column(
                "metadata_minimization_level",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'standard'"),
            ),
        )

    if "message_type" not in usage_ledger_columns:
        op.add_column(
            "usage_ledger",
            sa.Column(
                "message_type",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'chat'"),
            ),
        )
    if "evidence_retention_window" not in usage_ledger_columns:
        op.add_column(
            "usage_ledger",
            sa.Column(
                "evidence_retention_window",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'30d'"),
            ),
        )
    if "evidence_expires_at" not in usage_ledger_columns:
        op.add_column(
            "usage_ledger",
            sa.Column("evidence_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "metadata_minimization_level" not in usage_ledger_columns:
        op.add_column(
            "usage_ledger",
            sa.Column(
                "metadata_minimization_level",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'standard'"),
            ),
        )
    if "metadata_fields_suppressed_json" not in usage_ledger_columns:
        op.add_column(
            "usage_ledger",
            sa.Column(
                "metadata_fields_suppressed_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            ),
        )
    if "governance_source" not in usage_ledger_columns:
        op.add_column(
            "usage_ledger",
            sa.Column(
                "governance_source",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'tenant_policy'"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tenant_policy_columns = {col["name"] for col in inspector.get_columns("tenant_policies")}
    usage_ledger_columns = {col["name"] for col in inspector.get_columns("usage_ledger")}

    if "governance_source" in usage_ledger_columns:
        op.drop_column("usage_ledger", "governance_source")
    if "metadata_fields_suppressed_json" in usage_ledger_columns:
        op.drop_column("usage_ledger", "metadata_fields_suppressed_json")
    if "metadata_minimization_level" in usage_ledger_columns:
        op.drop_column("usage_ledger", "metadata_minimization_level")
    if "evidence_expires_at" in usage_ledger_columns:
        op.drop_column("usage_ledger", "evidence_expires_at")
    if "evidence_retention_window" in usage_ledger_columns:
        op.drop_column("usage_ledger", "evidence_retention_window")
    if "message_type" in usage_ledger_columns:
        op.drop_column("usage_ledger", "message_type")

    if "metadata_minimization_level" in tenant_policy_columns:
        op.drop_column("tenant_policies", "metadata_minimization_level")
    if "evidence_retention_window" in tenant_policy_columns:
        op.drop_column("tenant_policies", "evidence_retention_window")
