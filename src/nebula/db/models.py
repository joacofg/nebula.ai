from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TenantModel(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TenantPolicyModel(Base):
    __tablename__ = "tenant_policies"

    tenant_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    routing_mode_default: Mapped[str] = mapped_column(String(32), nullable=False)
    allowed_premium_models_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    semantic_cache_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fallback_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_premium_cost_per_request: Mapped[float | None] = mapped_column(Float, nullable=True)
    soft_budget_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    prompt_capture_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    response_capture_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    allowed_tenant_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeploymentModel(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(64), nullable=False)
    enrollment_state: Mapped[str] = mapped_column(String(32), nullable=False)
    nebula_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capability_flags_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    credential_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    credential_prefix: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dependency_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EnrollmentTokenModel(Base):
    __tablename__ = "enrollment_tokens"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    deployment_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LocalHostedIdentityModel(Base):
    __tablename__ = "local_hosted_identity"

    deployment_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UsageLedgerModel(Base):
    __tablename__ = "usage_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_model: Mapped[str] = mapped_column(String(255), nullable=False)
    final_route_target: Mapped[str] = mapped_column(String(64), nullable=False)
    final_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    response_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terminal_status: Mapped[str] = mapped_column(String(64), nullable=False)
    route_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    policy_outcome: Mapped[str | None] = mapped_column(Text(), nullable=True)
