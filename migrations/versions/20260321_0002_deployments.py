"""deployments and enrollment_tokens tables

Revision ID: 20260321_0002
Revises: 20260315_0001
Create Date: 2026-03-21 00:02:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260321_0002"
down_revision = "20260315_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "deployments" not in tables:
        op.create_table(
            "deployments",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("environment", sa.String(length=64), nullable=False),
            sa.Column(
                "enrollment_state",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'pending'"),
            ),
            sa.Column("nebula_version", sa.String(length=64), nullable=True),
            sa.Column(
                "capability_flags_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            ),
            sa.Column("credential_hash", sa.String(length=64), nullable=True, unique=True),
            sa.Column("credential_prefix", sa.String(length=32), nullable=True),
            sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "enrollment_tokens" not in tables:
        op.create_table(
            "enrollment_tokens",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column(
                "deployment_id",
                sa.String(length=255),
                sa.ForeignKey("deployments.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
            sa.Column("token_prefix", sa.String(length=16), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "local_hosted_identity" not in tables:
        op.create_table(
            "local_hosted_identity",
            sa.Column("deployment_id", sa.String(255), primary_key=True),
            sa.Column("display_name", sa.String(255), nullable=False),
            sa.Column("environment", sa.String(64), nullable=False),
            sa.Column("credential_hash", sa.String(64), nullable=False),
            sa.Column("credential_prefix", sa.String(16), nullable=False),
            sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("local_hosted_identity")
    op.drop_table("enrollment_tokens")
    op.drop_table("deployments")
