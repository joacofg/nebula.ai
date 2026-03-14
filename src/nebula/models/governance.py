from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

RoutingMode = Literal["auto", "local_only", "premium_only"]
TerminalStatus = Literal[
    "completed",
    "cache_hit",
    "fallback_completed",
    "policy_denied",
    "provider_error",
]


class TenantPolicy(BaseModel):
    routing_mode_default: RoutingMode = "auto"
    allowed_premium_models: list[str] = Field(default_factory=list)
    semantic_cache_enabled: bool = True
    fallback_enabled: bool = True
    max_premium_cost_per_request: float | None = Field(default=None, ge=0)
    soft_budget_usd: float | None = Field(default=None, ge=0)
    prompt_capture_enabled: bool = False
    response_capture_enabled: bool = False


class TenantRecord(BaseModel):
    id: str
    name: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    active: bool = True
    created_at: datetime
    updated_at: datetime


class TenantCreateRequest(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    active: bool = True
    policy: TenantPolicy | None = None


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    metadata: dict[str, Any] | None = None
    active: bool | None = None


class ApiKeyRecord(BaseModel):
    id: str
    name: str
    key_prefix: str
    tenant_id: str | None = None
    allowed_tenant_ids: list[str] = Field(default_factory=list)
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    tenant_id: str | None = None
    allowed_tenant_ids: list[str] = Field(default_factory=list)
    key: str | None = Field(default=None, min_length=8)


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    record: ApiKeyRecord


class UsageLedgerRecord(BaseModel):
    request_id: str
    tenant_id: str
    requested_model: str
    final_route_target: str
    final_provider: str | None = None
    fallback_used: bool
    cache_hit: bool
    response_model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float | None = None
    latency_ms: float | None = None
    timestamp: datetime
    terminal_status: TerminalStatus
    route_reason: str | None = None
    policy_outcome: str | None = None
