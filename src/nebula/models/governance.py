from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from nebula.models.openai import ChatCompletionRequest, ChatCompletionResponse

RoutingMode = Literal["auto", "local_only", "premium_only"]
TerminalStatus = Literal[
    "completed",
    "cache_hit",
    "fallback_completed",
    "policy_denied",
    "provider_error",
]
CalibrationEvidenceState = Literal["sufficient", "thin", "stale"]
CalibrationEvidenceScope = Literal["tenant", "tenant_window"]
CalibrationDegradedReason = Literal[
    "missing_route_signals",
    "degraded_replay_signals",
]
CalibrationExcludedReason = Literal[
    "explicit_model_override",
    "policy_forced_routing",
]
CalibrationGatedReason = Literal["calibrated_routing_disabled"]


class TenantPolicy(BaseModel):
    routing_mode_default: RoutingMode = "auto"
    calibrated_routing_enabled: bool = True
    allowed_premium_models: list[str] = Field(default_factory=list)
    semantic_cache_enabled: bool = True
    semantic_cache_similarity_threshold: float = Field(default=0.9, ge=0, le=1)
    semantic_cache_max_entry_age_hours: int = Field(default=168, ge=1, le=720)
    fallback_enabled: bool = True
    max_premium_cost_per_request: float | None = Field(default=None, ge=0)
    hard_budget_limit_usd: float | None = Field(default=None, ge=0)
    hard_budget_enforcement: Literal["downgrade", "deny"] | None = None
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


class AdminPlaygroundRequest(ChatCompletionRequest):
    tenant_id: str = Field(min_length=1)


class PlaygroundResponse(ChatCompletionResponse):
    request_id: str | None = None


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
    route_signals: dict[str, Any] | None = None


class CalibrationReasonCount(BaseModel):
    reason: str = Field(min_length=1)
    count: int = Field(ge=0)


class CalibrationEvidenceSummary(BaseModel):
    tenant_id: str = Field(min_length=1)
    scope: CalibrationEvidenceScope = "tenant"
    state: CalibrationEvidenceState
    state_reason: str = Field(min_length=1, max_length=280)
    generated_at: datetime
    latest_eligible_request_at: datetime | None = None
    latest_any_request_at: datetime | None = None
    eligible_request_count: int = Field(ge=0)
    sufficient_request_count: int = Field(ge=0)
    thin_request_threshold: int = Field(default=5, ge=1)
    staleness_threshold_hours: int = Field(default=24, ge=1)
    excluded_request_count: int = Field(ge=0)
    gated_request_count: int = Field(ge=0)
    degraded_request_count: int = Field(ge=0)
    excluded_reasons: list[CalibrationReasonCount] = Field(default_factory=list, max_length=4)
    gated_reasons: list[CalibrationReasonCount] = Field(default_factory=list, max_length=2)
    degraded_reasons: list[CalibrationReasonCount] = Field(default_factory=list, max_length=4)


class AdminSessionStatus(BaseModel):
    status: Literal["ok"] = "ok"


class PolicyOptionsResponse(BaseModel):
    routing_modes: list[RoutingMode]
    known_premium_models: list[str] = Field(default_factory=list)
    default_premium_model: str
    runtime_enforced_fields: list[str] = Field(default_factory=list)
    soft_signal_fields: list[str] = Field(default_factory=list)
    advisory_fields: list[str] = Field(default_factory=list)


class PolicySimulationRequest(BaseModel):
    candidate_policy: TenantPolicy
    from_timestamp: datetime | None = None
    to_timestamp: datetime | None = None
    limit: int = Field(default=50, ge=1, le=200)
    changed_sample_limit: int = Field(default=10, ge=1, le=50)


class PolicySimulationWindow(BaseModel):
    requested_from: datetime | None = None
    requested_to: datetime | None = None
    evaluated_from: datetime | None = None
    evaluated_to: datetime | None = None
    requested_limit: int
    changed_sample_limit: int
    returned_rows: int


class PolicySimulationOutcomeCounts(BaseModel):
    evaluated_rows: int = 0
    changed_routes: int = 0
    newly_denied: int = 0
    baseline_premium_cost: float = 0.0
    simulated_premium_cost: float = 0.0
    premium_cost_delta: float = 0.0


class PolicySimulationChangedRequest(BaseModel):
    request_id: str
    timestamp: datetime
    requested_model: str
    baseline_route_target: str
    simulated_route_target: str
    baseline_terminal_status: TerminalStatus
    simulated_terminal_status: TerminalStatus
    baseline_policy_outcome: str | None = None
    simulated_policy_outcome: str | None = None
    baseline_route_reason: str | None = None
    simulated_route_reason: str | None = None
    baseline_estimated_cost: float = 0.0
    simulated_estimated_cost: float = 0.0


class PolicySimulationResponse(BaseModel):
    tenant_id: str
    candidate_policy: TenantPolicy
    approximation_notes: list[str] = Field(default_factory=list)
    window: PolicySimulationWindow
    summary: PolicySimulationOutcomeCounts
    changed_requests: list[PolicySimulationChangedRequest] = Field(default_factory=list)


class RecommendationEvidence(BaseModel):
    label: str = Field(min_length=1)
    value: str = Field(min_length=1)


class RecommendationCard(BaseModel):
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    priority: int = Field(ge=1, le=9)
    category: Literal["policy", "cache", "info"]
    summary: str = Field(min_length=1, max_length=280)
    recommended_action: str = Field(min_length=1, max_length=280)
    evidence: list[RecommendationEvidence] = Field(default_factory=list, max_length=4)


class CacheInsight(BaseModel):
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    level: Literal["info", "notice", "warning"]
    summary: str = Field(min_length=1, max_length=280)
    evidence: list[RecommendationEvidence] = Field(default_factory=list, max_length=4)


class CacheControlSummary(BaseModel):
    enabled: bool
    similarity_threshold: float = Field(ge=0, le=1)
    max_entry_age_hours: int = Field(ge=1)
    runtime_status: Literal["ready", "degraded", "not_ready", "unknown"]
    runtime_detail: str = Field(min_length=1, max_length=280)
    estimated_hit_rate: float = Field(ge=0, le=1)
    avoided_premium_cost_usd: float = Field(ge=0)
    insights: list[CacheInsight] = Field(default_factory=list, max_length=2)


class RecommendationBundle(BaseModel):
    tenant_id: str = Field(min_length=1)
    generated_at: datetime
    window_requests_evaluated: int = Field(ge=0, le=200)
    recommendations: list[RecommendationCard] = Field(default_factory=list, max_length=3)
    cache_summary: CacheControlSummary
