"""governance baseline

Revision ID: 20260315_0001
Revises:
Create Date: 2026-03-15 23:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260315_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "tenants" not in tables:
        op.create_table(
            "tenants",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "tenant_policies" not in tables:
        op.create_table(
            "tenant_policies",
            sa.Column("tenant_id", sa.String(length=255), sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("routing_mode_default", sa.String(length=32), nullable=False),
            sa.Column("allowed_premium_models_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("semantic_cache_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("fallback_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("max_premium_cost_per_request", sa.Float(), nullable=True),
            sa.Column("soft_budget_usd", sa.Float(), nullable=True),
            sa.Column("prompt_capture_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("response_capture_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "api_keys" not in tables:
        op.create_table(
            "api_keys",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("key_hash", sa.String(length=64), nullable=False, unique=True),
            sa.Column("key_prefix", sa.String(length=32), nullable=False),
            sa.Column("tenant_id", sa.String(length=255), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
            sa.Column("allowed_tenant_ids_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "usage_ledger" not in tables:
        op.create_table(
            "usage_ledger",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("request_id", sa.String(length=255), nullable=False),
            sa.Column("tenant_id", sa.String(length=255), nullable=False),
            sa.Column("requested_model", sa.String(length=255), nullable=False),
            sa.Column("final_route_target", sa.String(length=64), nullable=False),
            sa.Column("final_provider", sa.String(length=255), nullable=True),
            sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("response_model", sa.String(length=255), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("estimated_cost", sa.Float(), nullable=True),
            sa.Column("latency_ms", sa.Float(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("terminal_status", sa.String(length=64), nullable=False),
            sa.Column("route_reason", sa.Text(), nullable=True),
            sa.Column("policy_outcome", sa.Text(), nullable=True),
        )

    index_names = {index["name"] for index in inspector.get_indexes("usage_ledger")} if "usage_ledger" in inspector.get_table_names() else set()
    if "idx_usage_ledger_tenant_timestamp" not in index_names:
        op.create_index(
            "idx_usage_ledger_tenant_timestamp",
            "usage_ledger",
            ["tenant_id", "timestamp"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("idx_usage_ledger_tenant_timestamp", table_name="usage_ledger")
    op.drop_table("usage_ledger")
    op.drop_table("api_keys")
    op.drop_table("tenant_policies")
    op.drop_table("tenants")
