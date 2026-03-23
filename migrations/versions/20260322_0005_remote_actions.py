"""Add hosted remote action queue table and live-action uniqueness guard.

Revision ID: 20260322_0005
Revises: 20260322_0004
Create Date: 2026-03-22 00:05:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260322_0005"
down_revision = "20260322_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "deployment_remote_actions" not in tables:
        op.create_table(
            "deployment_remote_actions",
            sa.Column("id", sa.String(length=255), primary_key=True, nullable=False),
            sa.Column(
                "deployment_id",
                sa.String(length=255),
                sa.ForeignKey("deployments.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("action_type", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("note", sa.String(length=280), nullable=False),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failure_reason", sa.String(length=64), nullable=True),
            sa.Column("failure_detail", sa.String(length=255), nullable=True),
            sa.Column("result_credential_prefix", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    indexes = {index["name"] for index in inspector.get_indexes("deployment_remote_actions")}
    if "uq_remote_actions_live" not in indexes:
        op.create_index(
            "uq_remote_actions_live",
            "deployment_remote_actions",
            ["deployment_id", "action_type"],
            unique=True,
            postgresql_where=sa.text("status IN ('queued', 'in_progress')"),
            sqlite_where=sa.text("status IN ('queued', 'in_progress')"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "deployment_remote_actions" not in tables:
        return

    indexes = {index["name"] for index in inspector.get_indexes("deployment_remote_actions")}
    if "uq_remote_actions_live" in indexes:
        op.drop_index("uq_remote_actions_live", table_name="deployment_remote_actions")
    op.drop_table("deployment_remote_actions")
