from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import (
    ApiKeyRecord,
    CalibrationEvidenceSummary,
    CalibrationReasonCount,
    PolicySimulationRequest,
    RecommendationBundle,
    TenantPolicy,
    TenantRecord,
    UsageLedgerRecord,
)
from nebula.models.openai import ChatCompletionRequest, EmbeddingsRequest
from nebula.providers.base import CompletionChunk, CompletionResult, CompletionUsage, ProviderError
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.chat_service import ChatService
from nebula.services.embeddings_service import (
    EmbeddingsEmptyResultError,
    EmbeddingsUpstreamError,
    EmbeddingsValidationError,
    OllamaEmbeddingsService,
)
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyResolution, PolicyService
from nebula.services.policy_simulation_service import PolicySimulationService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.recommendation_service import RecommendationService
from nebula.services.router_service import RouteDecision, RouterService
from tests.support import FakeCacheService, StubProvider

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeGovernanceStore:
    def __init__(self) -> None:
        self.records = []
        self.policies: dict[str, TenantPolicy] = {"default": TenantPolicy()}

    def record_usage(self, record) -> None:
        policy = self.get_policy(record.tenant_id)
        governed_record = record.model_copy(
            update={
                "evidence_retention_window": policy.evidence_retention_window,
                "metadata_minimization_level": (
                    "strict"
                    if policy.metadata_minimization_level == "strict" or record.route_signals is None
                    else "standard"
                ),
                "metadata_fields_suppressed": (
                    ["route_signals"]
                    if policy.metadata_minimization_level == "strict" and record.route_signals is not None
                    else []
                ),
                "route_signals": (
                    None
                    if policy.metadata_minimization_level == "strict"
                    else record.route_signals
                ),
                "governance_source": "tenant_policy",
            }
        )
        self.records.append(governed_record)

    def get_policy(self, tenant_id: str) -> TenantPolicy:
        return self.policies.get(tenant_id, TenantPolicy())

    def upsert_policy(self, tenant_id: str, policy: TenantPolicy) -> TenantPolicy:
        self.policies[tenant_id] = policy
        return policy


class StubAsyncResponse:
    def __init__(self, *, status_code: int = 200, json_body: dict | None = None) -> None:
        self.status_code = status_code
        self._json_body = json_body or {}
        self.request = httpx.Request("POST", "http://testserver/api/embed")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status={self.status_code}",
                request=self.request,
                response=httpx.Response(
                    self.status_code,
                    request=self.request,
                    json=self._json_body,
                ),
            )

    def json(self) -> dict:
        return self._json_body


class StubAsyncClient:
    def __init__(self, responses: list[StubAsyncResponse] | None = None, *, error: Exception | None = None) -> None:
        self.responses = responses or []
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    async def post(self, path: str, json: dict) -> StubAsyncResponse:
        self.calls.append((path, json))
        if self.error is not None:
            raise self.error
        assert self.responses, "No stubbed response available"
        return self.responses.pop(0)

    async def aclose(self) -> None:
        return None


class FakePolicyService:
    def __init__(
        self,
        settings: Settings,
        *,
        route_decision: RouteDecision | None = None,
        policy_mode: str = "auto",
        cache_enabled: bool = True,
        fallback_enabled: bool = True,
        policy_outcome: str = "default",
    ) -> None:
        self.settings = settings
        self.route_decision = route_decision
        self.policy_mode = policy_mode
        self.cache_enabled = cache_enabled
        self.fallback_enabled = fallback_enabled
        self.policy_outcome = policy_outcome

    async def resolve(self, *, prompt, request, tenant_context, router_service) -> PolicyResolution:
        decision = self.route_decision or await router_service.choose_target_with_reason(
            prompt,
            request,
            routing_mode=self.policy_mode,
        )
        return PolicyResolution(
            route_decision=decision,
            policy_mode=self.policy_mode,
            cache_enabled=self.cache_enabled,
            fallback_enabled=self.fallback_enabled,
            policy_outcome=self.policy_outcome,
            soft_budget_exceeded=False,
            projected_premium_cost=0.0001 if decision.target == "premium" else 0.0,
        )

    def estimate_usage(self, request: ChatCompletionRequest, response_content: str) -> CompletionUsage:
        return CompletionUsage(prompt_tokens=8, completion_tokens=4, total_tokens=12)

    def estimate_cost(self, model: str, usage: CompletionUsage | None) -> float | None:
        if usage is None:
            return None
        return 0.0001 if model != self.settings.local_model else 0.0


def tenant_context() -> AuthenticatedTenantContext:
    now = datetime.now(UTC)
    return AuthenticatedTenantContext(
        tenant=TenantRecord(
            id="default",
            name="Default",
            created_at=now,
            updated_at=now,
        ),
        api_key=ApiKeyRecord(
            id="key-1",
            name="default",
            key_prefix="nebula-",
            tenant_id="default",
            allowed_tenant_ids=["default"],
            created_at=now,
            updated_at=now,
        ),
        policy=TenantPolicy(allowed_premium_models=["gpt-4o-mini", "openai/gpt-4o-mini"]),
    )


def build_service(
    *,
    cache_service: FakeCacheService | None = None,
    local_provider: StubProvider | None = None,
    premium_provider: StubProvider | None = None,
    settings: Settings | None = None,
    policy_service: FakePolicyService | None = None,
) -> tuple[ChatService, FakeCacheService, StubProvider, StubProvider, FakeGovernanceStore]:
    active_settings = settings or Settings()
    active_cache = cache_service or FakeCacheService()
    active_local = local_provider or StubProvider(
        "ollama",
        completion_result=CompletionResult(
            content="local response",
            model=active_settings.local_model,
            provider="ollama",
            usage=CompletionUsage(prompt_tokens=8, completion_tokens=4, total_tokens=12),
        ),
    )
    active_premium = premium_provider or StubProvider(
        "openai-compatible",
        completion_result=CompletionResult(
            content="premium response",
            model=active_settings.premium_model,
            provider="openai-compatible",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=6, total_tokens=16),
        ),
    )
    store = FakeGovernanceStore()
    service = ChatService(
        settings=active_settings,
        cache_service=active_cache,
        router_service=RouterService(active_settings),
        provider_registry=ProviderRegistry(
            local_provider=active_local,
            premium_provider=active_premium,
        ),
        governance_store=store,
        policy_service=policy_service or FakePolicyService(active_settings),
    )
    return service, active_cache, active_local, active_premium, store


@pytest.mark.asyncio
async def test_create_completion_persists_calibrated_route_evidence_for_real_request() -> None:
    service, cache_service, local_provider, premium_provider, store = build_service()
    store.upsert_policy(
        "default",
        TenantPolicy(
            allowed_premium_models=["gpt-4o-mini", "openai/gpt-4o-mini"],
            evidence_retention_window="7d",
            metadata_minimization_level="strict",
        ),
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "Please review this architecture tradeoff."}],
    )

    envelope = await service.create_completion_with_metadata(
        request,
        tenant_context=tenant_context(),
        request_id="req-calibrated-evidence",
    )

    assert envelope.metadata.route_target == "premium"
    assert envelope.metadata.route_reason == "token_complexity"
    assert envelope.metadata.route_signals is not None
    assert envelope.metadata.route_signals["route_mode"] == "calibrated"
    assert envelope.metadata.route_signals["score_components"]["total_score"] == envelope.metadata.route_score
    assert premium_provider.completion_result is not None
    assert cache_service.stored_entries == [
        (
            "Please review this architecture tradeoff.",
            "premium response",
            service.settings.premium_model,
        )
    ]
    assert store.records[-1].request_id == "req-calibrated-evidence"
    assert store.records[-1].final_route_target == "premium"
    assert store.records[-1].route_reason == "token_complexity"
    assert store.records[-1].route_signals is None
    assert store.records[-1].message_type == "chat"
    assert store.records[-1].evidence_retention_window == "7d"
    assert store.records[-1].metadata_minimization_level == "strict"
    assert store.records[-1].metadata_fields_suppressed == ["route_signals"]
    assert store.records[-1].governance_source == "tenant_policy"


@pytest.mark.asyncio
async def test_create_completion_routes_complex_prompts_to_premium_provider() -> None:
    service, cache_service, local_provider, premium_provider, store = build_service()
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "Please review this architecture tradeoff."}],
    )

    response = await service.create_completion(
        request,
        tenant_context=tenant_context(),
        request_id="req-premium",
    )

    assert response.model == service.settings.premium_model
    assert response.choices[0].message.content == "premium response"
    assert premium_provider.completion_result is not None
    assert cache_service.stored_entries == [
        (
            "Please review this architecture tradeoff.",
            "premium response",
            service.settings.premium_model,
        )
    ]
    assert store.records[-1].final_route_target == "premium"


    settings = Settings()
    local_provider = StubProvider(
        "ollama",
        completion_error=ProviderError("local provider offline"),
    )
    premium_provider = StubProvider(
        "openai-compatible",
        completion_result=CompletionResult(
            content="fallback response",
            model=settings.premium_model,
            provider="openai-compatible",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=6, total_tokens=16),
        ),
    )
    service, cache_service, _, _, store = build_service(
        local_provider=local_provider,
        premium_provider=premium_provider,
        settings=settings,
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "hello"}],
    )

    response = await service.create_completion(
        request,
        tenant_context=tenant_context(),
        request_id="req-fallback",
    )

    assert response.model == settings.premium_model
    assert response.choices[0].message.content == "fallback response"
    assert cache_service.stored_entries == [("hello", "fallback response", settings.premium_model)]
    assert store.records[-1].fallback_used is True
    assert store.records[-1].terminal_status == "fallback_completed"


@pytest.mark.asyncio
async def test_create_completion_returns_cached_response_without_calling_providers() -> None:
    cache_service = FakeCacheService(cached_response="cached response")
    service, _, _, _, store = build_service(cache_service=cache_service)
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "hello cache"}],
    )

    response = await service.create_completion(
        request,
        tenant_context=tenant_context(),
        request_id="req-cache",
    )

    assert response.model == "nebula-cache"
    assert response.choices[0].message.content == "cached response"
    assert store.records[-1].cache_hit is True
    assert store.records[-1].terminal_status == "cache_hit"


@pytest.mark.asyncio
async def test_stream_completion_falls_back_to_premium_provider() -> None:
    settings = Settings()
    local_provider = StubProvider(
        "ollama",
        stream_error=ProviderError("local stream failed"),
    )
    premium_provider = StubProvider(
        "openai-compatible",
        stream_chunks=[
            CompletionChunk(delta="premium ", model=settings.premium_model),
            CompletionChunk(delta="stream", model=settings.premium_model),
            CompletionChunk(delta="", model=settings.premium_model, finish_reason="stop"),
        ],
    )
    service, cache_service, _, _, store = build_service(
        local_provider=local_provider,
        premium_provider=premium_provider,
        settings=settings,
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        stream=True,
        messages=[{"role": "user", "content": "short"}],
    )

    events = [
        event
        async for event in service.stream_completion(
            request,
            tenant_context=tenant_context(),
            request_id="req-stream",
        )
    ]
    payload = b"".join(events)

    assert f'"model": "{settings.premium_model}"'.encode() in payload
    assert b"premium " in payload
    assert b"stream" in payload
    assert payload.endswith(b"data: [DONE]\n\n")
    assert cache_service.stored_entries == [("short", "premium stream", settings.premium_model)]
    assert store.records[-1].terminal_status == "fallback_completed"


@pytest.mark.asyncio
async def test_policy_can_disable_cache_and_block_fallback() -> None:
    settings = Settings()
    cache_service = FakeCacheService(cached_response="should not be used")
    local_provider = StubProvider("ollama", completion_error=ProviderError("local down"))
    service, _, _, _, store = build_service(
        cache_service=cache_service,
        local_provider=local_provider,
        settings=settings,
        policy_service=FakePolicyService(
            settings,
            route_decision=RouteDecision(target="local", reason="policy_local_only"),
            cache_enabled=False,
            fallback_enabled=False,
            policy_mode="local_only",
            policy_outcome="routing_mode=local_only;cache=disabled;fallback=disabled",
        ),
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "policy controlled request"}],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_completion(
            request,
            tenant_context=tenant_context(),
            request_id="req-policy",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Local provider failed and tenant policy disabled premium fallback."
    assert cache_service.lookup_calls == []
    assert store.records[-1].terminal_status == "provider_error"
    assert store.records[-1].route_reason == "local_provider_error_fallback_blocked"
    assert store.records[-1].policy_outcome == "routing_mode=local_only;cache=disabled;fallback=disabled"


class RuntimePolicyStore:
    def __init__(
        self,
        *,
        spend_total: float = 0.0,
        evidence_summary: CalibrationEvidenceSummary | None = None,
    ) -> None:
        self.spend_total = spend_total
        self.evidence_summary = evidence_summary
        self.calls: list[tuple[str, datetime | None]] = []
        self.evidence_summary_calls: list[str] = []

    def tenant_spend_total(self, tenant_id: str, *, before_timestamp: datetime | None = None) -> float:
        assert tenant_id == "default"
        self.calls.append((tenant_id, before_timestamp))
        return self.spend_total

    def summarize_calibration_evidence(self, *, tenant_id: str) -> CalibrationEvidenceSummary:
        assert tenant_id == "default"
        self.evidence_summary_calls.append(tenant_id)
        return self.evidence_summary or CalibrationEvidenceSummary(
            tenant_id=tenant_id,
            scope="tenant",
            state="thin",
            state_reason="No eligible calibrated routing evidence is available yet.",
            generated_at=datetime.now(UTC),
            latest_eligible_request_at=None,
            latest_any_request_at=None,
            eligible_request_count=0,
            sufficient_request_count=0,
            thin_request_threshold=GovernanceStore.CALIBRATION_THIN_REQUEST_THRESHOLD,
            staleness_threshold_hours=GovernanceStore.CALIBRATION_STALENESS_THRESHOLD_HOURS,
            excluded_request_count=0,
            gated_request_count=0,
            degraded_request_count=0,
        )


class FakeSimulationGovernanceStore(RuntimePolicyStore):
    CALIBRATION_THIN_REQUEST_THRESHOLD = GovernanceStore.CALIBRATION_THIN_REQUEST_THRESHOLD
    CALIBRATION_STALENESS_THRESHOLD_HOURS = GovernanceStore.CALIBRATION_STALENESS_THRESHOLD_HOURS
    _CALIBRATION_EXCLUDED_ROUTE_REASONS = GovernanceStore._CALIBRATION_EXCLUDED_ROUTE_REASONS
    _CALIBRATION_GATED_ROUTE_REASONS = GovernanceStore._CALIBRATION_GATED_ROUTE_REASONS

    def __init__(self, records: list[UsageLedgerRecord], *, spend_total: float = 0.0) -> None:
        super().__init__(spend_total=spend_total)
        self.records = list(records)
        self.record_usage_calls: list[UsageLedgerRecord] = []
        self.policy_updates: list[tuple[str, TenantPolicy]] = []
        self.list_usage_records_calls: list[dict[str, object]] = []
        self.calibration_summary_calls: list[dict[str, object]] = []

    def list_usage_records(
        self,
        *,
        request_id: str | None = None,
        tenant_id: str | None = None,
        terminal_status: str | None = None,
        route_target: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 100,
    ) -> list[UsageLedgerRecord]:
        self.list_usage_records_calls.append(
            {
                "request_id": request_id,
                "tenant_id": tenant_id,
                "terminal_status": terminal_status,
                "route_target": route_target,
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
                "limit": limit,
            }
        )
        rows = list(self.records)
        if request_id is not None:
            rows = [row for row in rows if row.request_id == request_id]
        if tenant_id is not None:
            rows = [row for row in rows if row.tenant_id == tenant_id]
        if terminal_status is not None:
            rows = [row for row in rows if row.terminal_status == terminal_status]
        if route_target is not None:
            rows = [row for row in rows if row.final_route_target == route_target]
        if from_timestamp is not None:
            rows = [row for row in rows if row.timestamp >= from_timestamp]
        if to_timestamp is not None:
            rows = [row for row in rows if row.timestamp <= to_timestamp]
        rows = sorted(rows, key=lambda row: row.timestamp, reverse=True)
        return rows[:limit]

    def summarize_calibration_evidence(
        self,
        *,
        tenant_id: str,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 200,
        now: datetime | None = None,
    ) -> CalibrationEvidenceSummary:
        self.calibration_summary_calls.append(
            {
                "tenant_id": tenant_id,
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
                "limit": limit,
                "now": now,
            }
        )
        return GovernanceStore.summarize_calibration_evidence(
            self,
            tenant_id=tenant_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            now=now,
        )

    def _calibration_excluded_reason(self, record: UsageLedgerRecord) -> str | None:
        return GovernanceStore._calibration_excluded_reason(self, record)

    def _calibration_gated_reason(self, record: UsageLedgerRecord) -> str | None:
        return GovernanceStore._calibration_gated_reason(self, record)

    def _calibration_degraded_reason(self, record: UsageLedgerRecord) -> str | None:
        return GovernanceStore._calibration_degraded_reason(self, record)

    def _calibration_state(
        self,
        *,
        current_time: datetime,
        latest_eligible_request_at: datetime | None,
        sufficient_request_count: int,
        degraded_request_count: int,
    ) -> tuple[str, str]:
        return GovernanceStore._calibration_state(
            self,
            current_time=current_time,
            latest_eligible_request_at=latest_eligible_request_at,
            sufficient_request_count=sufficient_request_count,
            degraded_request_count=degraded_request_count,
        )

    def _reason_counts(self, counter):
        return GovernanceStore._reason_counts(self, counter)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _normalize_comparable_datetime(self, value: datetime) -> datetime:
        return GovernanceStore._normalize_comparable_datetime(self, value)

    def record_usage(self, record: UsageLedgerRecord) -> None:
        self.record_usage_calls.append(record)

    def upsert_policy(self, tenant_id: str, policy: TenantPolicy) -> TenantPolicy:
        self.policy_updates.append((tenant_id, policy))
        return policy


@pytest.mark.asyncio
async def test_runtime_policy_resolution_enforces_toggles_and_soft_budget_signal() -> None:
    settings = Settings()
    policy_service = PolicyService(
        settings,
        RuntimePolicyStore(spend_total=5.0),
        PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "simple request"}],
    )
    resolution = await policy_service.resolve(
        prompt="simple request",
        request=request,
        tenant_context=AuthenticatedTenantContext(
            tenant=tenant_context().tenant,
            api_key=tenant_context().api_key,
            policy=TenantPolicy(
                semantic_cache_enabled=False,
                fallback_enabled=False,
                soft_budget_usd=1.0,
            ),
        ),
        router_service=RouterService(settings),
    )

    assert resolution.cache_enabled is False
    assert resolution.fallback_enabled is False
    assert resolution.soft_budget_exceeded is True
    assert resolution.policy_outcome == (
        "cache=disabled;fallback=disabled;soft_budget=exceeded;"
        "outcome_evidence=thin(eligible=0,sufficient=0,degraded=0,gated=0,excluded=0)"
    )


@pytest.mark.asyncio
async def test_runtime_policy_resolution_applies_live_outcome_evidence_to_route_signals_and_score() -> None:
    settings = Settings()
    evidence_summary = CalibrationEvidenceSummary(
        tenant_id="default",
        scope="tenant",
        state="sufficient",
        state_reason="Eligible calibrated routing evidence meets the tenant sufficiency threshold.",
        generated_at=datetime.now(UTC),
        latest_eligible_request_at=datetime.now(UTC),
        latest_any_request_at=datetime.now(UTC),
        eligible_request_count=7,
        sufficient_request_count=7,
        thin_request_threshold=GovernanceStore.CALIBRATION_THIN_REQUEST_THRESHOLD,
        staleness_threshold_hours=GovernanceStore.CALIBRATION_STALENESS_THRESHOLD_HOURS,
        excluded_request_count=1,
        gated_request_count=0,
        degraded_request_count=0,
    )
    store = RuntimePolicyStore(spend_total=0.0, evidence_summary=evidence_summary)
    policy_service = PolicyService(
        settings,
        store,
        PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "a" * 120}],
    )

    resolution = await policy_service.resolve(
        prompt="a" * 120,
        request=request,
        tenant_context=AuthenticatedTenantContext(
            tenant=tenant_context().tenant,
            api_key=tenant_context().api_key,
            policy=TenantPolicy(),
        ),
        router_service=RouterService(settings),
    )

    assert store.evidence_summary_calls == ["default"]
    assert resolution.route_decision.target == "local"
    assert resolution.route_decision.reason == "token_complexity"
    assert resolution.route_decision.signals["outcome_evidence"] == {
        "state": "sufficient",
        "state_reason": "Eligible calibrated routing evidence meets the tenant sufficiency threshold.",
        "eligible_request_count": 7,
        "sufficient_request_count": 7,
        "degraded_request_count": 0,
        "gated_request_count": 0,
        "excluded_request_count": 1,
    }
    assert resolution.route_decision.signals["score_components"]["outcome_bonus"] == 0.15
    assert resolution.route_decision.signals["score_components"]["evidence_penalty"] == 0.0
    assert resolution.route_decision.score == 0.39
    assert "outcome_evidence=sufficient(eligible=7,sufficient=7,degraded=0,gated=0,excluded=1)" in resolution.policy_outcome


@pytest.mark.asyncio
async def test_runtime_policy_resolution_downgrades_hard_budget_exhaustion_to_local() -> None:
    settings = Settings()
    policy_service = PolicyService(
        settings,
        RuntimePolicyStore(spend_total=9.0),
        PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "analyze this architecture tradeoff"}],
    )

    resolution = await policy_service.resolve(
        prompt="analyze this architecture tradeoff",
        request=request,
        tenant_context=AuthenticatedTenantContext(
            tenant=tenant_context().tenant,
            api_key=tenant_context().api_key,
            policy=TenantPolicy(
                hard_budget_limit_usd=5.0,
                hard_budget_enforcement="downgrade",
            ),
        ),
        router_service=RouterService(settings),
    )

    assert resolution.route_decision.target == "local"
    assert resolution.route_decision.reason == "hard_budget_downgrade"
    assert resolution.route_decision.signals["route_mode"] == "calibrated"
    assert resolution.route_decision.signals["score_components"]["total_score"] == resolution.route_decision.score
    assert resolution.hard_budget_exceeded is True
    assert resolution.tenant_spend_total == 9.0
    assert "hard_budget=exceeded" in resolution.policy_outcome
    assert "budget_action=downgraded_to_local" in resolution.policy_outcome
    assert resolution.projected_premium_cost is None


@pytest.mark.asyncio
async def test_policy_simulation_uses_before_timestamp_for_hard_budget_windows() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-budget-window",
            timestamp=now,
            final_route_target="premium",
            requested_model="nebula-auto",
            estimated_cost=0.002,
            prompt_tokens=800,
            completion_tokens=256,
            route_signals={"token_count": 900, "complexity_tier": "medium", "keyword_match": True},
        )
    ]
    store = FakeSimulationGovernanceStore(records, spend_total=9.0)
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings),
        policy_service=PolicyService(settings, store, PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")),
    )

    response = await service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(
                hard_budget_limit_usd=5.0,
                hard_budget_enforcement="downgrade",
            ),
            limit=10,
            changed_sample_limit=10,
        ),
    )

    assert store.calls == [("default", now)]
    assert response.summary.evaluated_rows == 1
    assert response.summary.changed_routes == 1
    changed = response.changed_requests[0]
    assert changed.baseline_route_target == "premium"
    assert changed.simulated_route_target == "local"
    assert changed.simulated_route_reason == "hard_budget_downgrade"
    assert changed.baseline_route_mode == "calibrated"
    assert changed.baseline_calibrated_routing is True
    assert changed.baseline_degraded_routing is False
    assert changed.baseline_route_score == 1.0
    assert changed.simulated_route_mode == "calibrated"
    assert changed.simulated_calibrated_routing is True
    assert changed.simulated_degraded_routing is False
    assert changed.simulated_route_score == 1.0
    assert "hard_budget=exceeded" in (changed.simulated_policy_outcome or "")


@pytest.mark.asyncio
async def test_governance_store_calibration_summary_reports_sufficient_evidence() -> None:
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id=f"req-sufficient-{index}",
            timestamp=now.replace(microsecond=index),
            route_signals={"route_mode": "calibrated", "token_count": 600, "complexity_tier": "medium", "keyword_match": True},
        )
        for index in range(5)
    ]
    store = FakeSimulationGovernanceStore(records)

    summary = store.summarize_calibration_evidence(tenant_id="default", now=now)

    assert summary.state == "sufficient"
    assert summary.scope == "tenant"
    assert summary.eligible_request_count == 5
    assert summary.sufficient_request_count == 5
    assert summary.degraded_request_count == 0
    assert summary.gated_request_count == 0
    assert summary.excluded_request_count == 0
    assert summary.latest_eligible_request_at == max(record.timestamp for record in records)


@pytest.mark.asyncio
async def test_governance_store_calibration_summary_reports_thin_evidence_and_excludes_overrides() -> None:
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-calibrated-1",
            timestamp=now.replace(microsecond=1),
            route_signals={"route_mode": "calibrated", "token_count": 400, "complexity_tier": "low", "keyword_match": False},
        ),
        _ledger_record(
            request_id="req-calibrated-2",
            timestamp=now.replace(microsecond=2),
            route_signals={"route_mode": "calibrated", "token_count": 520, "complexity_tier": "medium", "keyword_match": True},
        ),
        _ledger_record(
            request_id="req-explicit",
            timestamp=now.replace(microsecond=3),
            route_reason="explicit_premium_model",
            route_signals=None,
        ),
        _ledger_record(
            request_id="req-policy-forced",
            timestamp=now.replace(microsecond=4),
            route_reason="policy_local_only",
            route_signals=None,
        ),
    ]
    store = FakeSimulationGovernanceStore(records)

    summary = store.summarize_calibration_evidence(tenant_id="default", now=now)

    assert summary.state == "thin"
    assert summary.sufficient_request_count == 2
    assert summary.eligible_request_count == 2
    assert summary.excluded_request_count == 2
    assert summary.gated_request_count == 0
    assert summary.degraded_request_count == 0


@pytest.mark.asyncio
async def test_governance_store_calibration_summary_reports_degraded_state_precedence_over_sufficient() -> None:
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id=f"req-calibrated-{index}",
            timestamp=now.replace(microsecond=index),
            route_signals={"route_mode": "calibrated", "token_count": 700, "complexity_tier": "medium", "keyword_match": True},
        )
        for index in range(5)
    ]
    records.append(
        _ledger_record(
            request_id="req-degraded-precedence",
            timestamp=now.replace(microsecond=99),
            route_signals={"route_mode": "degraded", "token_count": 650, "complexity_tier": "medium", "keyword_match": True},
        )
    )
    store = FakeSimulationGovernanceStore(records)

    summary = store.summarize_calibration_evidence(tenant_id="default", now=now)

    # Compatibility note: downstream code still reads calibration_summary, but degraded is a
    # summary-state outcome, not only a per-row reason, so it takes precedence over sufficient.
    assert summary.state == "degraded"
    assert summary.sufficient_request_count == 5
    assert summary.eligible_request_count == 6
    assert summary.degraded_request_count == 1
    assert summary.degraded_reasons[0].reason == "degraded_replay_signals"
    assert summary.degraded_reasons[0].count == 1


@pytest.mark.asyncio
async def test_governance_store_calibration_summary_reports_stale_and_distinguishes_gated_from_degraded() -> None:
    now = datetime.now(UTC)
    stale_base = now.replace(day=max(1, now.day - 2))
    records = [
        _ledger_record(
            request_id=f"req-stale-{index}",
            timestamp=stale_base.replace(microsecond=index),
            route_signals={"route_mode": "calibrated", "token_count": 700, "complexity_tier": "medium", "keyword_match": True},
        )
        for index in range(5)
    ]
    records.extend(
        [
            _ledger_record(
                request_id="req-gated",
                timestamp=now.replace(microsecond=11),
                route_reason="calibrated_routing_disabled",
                route_signals=None,
            ),
            _ledger_record(
                request_id="req-degraded-mode",
                timestamp=stale_base.replace(microsecond=12),
                route_signals={"route_mode": "degraded", "token_count": 900, "complexity_tier": "medium", "keyword_match": True},
            ),
            _ledger_record(
                request_id="req-missing-signals",
                timestamp=stale_base.replace(microsecond=13),
                route_signals=None,
            ),
        ]
    )
    store = FakeSimulationGovernanceStore(records)

    summary = store.summarize_calibration_evidence(tenant_id="default", now=now)

    # Once enough sufficient rows exist, degraded evidence takes summary precedence over stale so
    # operator/replay consumers can diagnose the weakened window before reasoning about freshness.
    assert summary.state == "degraded"
    assert summary.sufficient_request_count == 5
    assert summary.eligible_request_count == 7
    assert summary.gated_request_count == 1
    assert summary.degraded_request_count == 2
    assert summary.gated_reasons == [CalibrationReasonCount(reason="calibrated_routing_disabled", count=1)]
    assert summary.degraded_reasons == [
        CalibrationReasonCount(reason="degraded_replay_signals", count=1),
        CalibrationReasonCount(reason="missing_route_signals", count=1),
    ]


@pytest.mark.asyncio
async def test_governance_store_calibration_summary_is_tenant_and_window_scoped() -> None:
    now = datetime.now(UTC)
    in_window = now.replace(microsecond=10)
    out_of_window = now.replace(year=now.year - 1, microsecond=11)
    records = [
        _ledger_record(
            request_id=f"req-default-{index}",
            tenant_id="default",
            timestamp=in_window.replace(microsecond=10 + index),
            route_signals={"route_mode": "calibrated", "token_count": 500, "complexity_tier": "medium", "keyword_match": True},
        )
        for index in range(5)
    ]
    records.extend(
        [
            _ledger_record(
                request_id="req-default-old",
                tenant_id="default",
                timestamp=out_of_window,
                route_signals={"route_mode": "degraded", "token_count": 500, "complexity_tier": "medium", "keyword_match": True},
            ),
            _ledger_record(
                request_id="req-other-tenant",
                tenant_id="other",
                timestamp=in_window.replace(microsecond=99),
                route_signals={"route_mode": "degraded", "token_count": 500, "complexity_tier": "medium", "keyword_match": True},
            ),
        ]
    )
    store = FakeSimulationGovernanceStore(records)

    summary = store.summarize_calibration_evidence(
        tenant_id="default",
        from_timestamp=now.replace(second=max(0, now.second - 1)),
        to_timestamp=now.replace(second=min(59, now.second + 1)),
        now=now,
    )

    assert summary.scope == "tenant_window"
    assert summary.state == "sufficient"
    assert summary.eligible_request_count == 5
    assert summary.sufficient_request_count == 5
    assert summary.degraded_request_count == 0
    assert summary.latest_any_request_at == max(record.timestamp for record in records[:5])


@pytest.mark.asyncio
async def test_policy_simulation_exposes_window_calibration_summary_with_gated_and_degraded_counts() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id=f"req-calibrated-{index}",
            timestamp=now.replace(microsecond=index),
            route_signals={"route_mode": "calibrated", "token_count": 700, "complexity_tier": "medium", "keyword_match": True},
        )
        for index in range(4)
    ]
    records.extend(
        [
            _ledger_record(
                request_id="req-gated",
                timestamp=now.replace(microsecond=10),
                route_reason="calibrated_routing_disabled",
                route_signals=None,
            ),
            _ledger_record(
                request_id="req-degraded",
                timestamp=now.replace(microsecond=11),
                route_signals={"route_mode": "degraded", "token_count": 650, "complexity_tier": "medium", "keyword_match": True},
            ),
            _ledger_record(
                request_id="req-suppressed",
                timestamp=now.replace(microsecond=12),
                route_signals=None,
                policy_outcome="metadata_minimization=strict",
            ),
        ]
    )
    store = FakeSimulationGovernanceStore(records)
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings),
        policy_service=PolicyService(settings, store, PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")),
    )

    response = await service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(),
            limit=10,
            changed_sample_limit=10,
        ),
    )

    assert response.calibration_summary.scope == "tenant"
    assert response.calibration_summary.state == "thin"
    assert response.calibration_summary.state_reason == (
        "Eligible calibrated routing evidence is still below the tenant sufficiency threshold."
    )
    assert response.calibration_summary.sufficient_request_count == 4
    assert response.calibration_summary.eligible_request_count == 6
    assert response.calibration_summary.gated_request_count == 1
    assert response.calibration_summary.degraded_request_count == 2
    assert response.calibration_summary.gated_reasons[0].reason == "calibrated_routing_disabled"
    assert response.calibration_summary.gated_reasons[0].count == 1
    assert response.calibration_summary.degraded_reasons == [
        CalibrationReasonCount(reason="degraded_replay_signals", count=1),
        CalibrationReasonCount(reason="missing_route_signals", count=1),
    ]


def _ledger_record(
    *,
    request_id: str,
    tenant_id: str = "default",
    requested_model: str = "nebula-auto",
    final_route_target: str = "local",
    terminal_status: str = "completed",
    timestamp: datetime,
    prompt_tokens: int = 80,
    completion_tokens: int = 40,
    estimated_cost: float | None = 0.0,
    route_reason: str = "token_complexity",
    policy_outcome: str = "default",
    route_signals: dict | None = None,
) -> UsageLedgerRecord:
    total_tokens = prompt_tokens + completion_tokens
    return UsageLedgerRecord(
        request_id=request_id,
        tenant_id=tenant_id,
        requested_model=requested_model,
        final_route_target=final_route_target,
        final_provider="mock",
        fallback_used=False,
        cache_hit=False,
        response_model=("llama3.2" if final_route_target == "local" else "openai/gpt-4o-mini"),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        latency_ms=25.0,
        timestamp=timestamp,
        terminal_status=terminal_status,  # type: ignore[arg-type]
        route_reason=route_reason,
        policy_outcome=policy_outcome,
        route_signals=route_signals,
    )


@pytest.mark.asyncio
async def test_policy_simulation_replays_recent_ledger_rows_and_reports_changed_routes() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-1",
            timestamp=now,
            final_route_target="local",
            prompt_tokens=80,
            completion_tokens=40,
            route_signals={"token_count": 120, "complexity_tier": "low", "keyword_match": False},
        ),
        _ledger_record(
            request_id="req-2",
            timestamp=now.replace(microsecond=1),
            final_route_target="local",
            prompt_tokens=60,
            completion_tokens=30,
            route_signals={"token_count": 80, "complexity_tier": "low", "keyword_match": False},
        ),
    ]
    store = FakeSimulationGovernanceStore(records)
    simulation_service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings),
        policy_service=PolicyService(settings, store, PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")),
    )

    response = await simulation_service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(routing_mode_default="premium_only"),
            limit=10,
            changed_sample_limit=10,
        ),
    )

    assert response.summary.evaluated_rows == 2
    assert response.summary.changed_routes == 2
    assert response.summary.newly_denied == 0
    assert response.window.returned_rows == 2
    assert [item.request_id for item in response.changed_requests] == ["req-2", "req-1"]
    assert all(item.baseline_route_target == "local" for item in response.changed_requests)
    assert all(item.simulated_route_target == "premium" for item in response.changed_requests)
    assert all(item.baseline_route_mode == "calibrated" for item in response.changed_requests)
    assert all(item.baseline_calibrated_routing is True for item in response.changed_requests)
    assert all(item.baseline_degraded_routing is False for item in response.changed_requests)
    assert all(item.baseline_route_score is not None for item in response.changed_requests)
    assert all(item.simulated_route_mode is None for item in response.changed_requests)
    assert all(item.simulated_calibrated_routing is None for item in response.changed_requests)
    assert all(item.simulated_degraded_routing is None for item in response.changed_requests)
    assert all(item.simulated_route_score is None for item in response.changed_requests)
    assert store.record_usage_calls == []
    assert store.policy_updates == []


@pytest.mark.asyncio
async def test_policy_simulation_preserves_gated_null_mode_for_changed_request_samples() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-gated-parity",
            timestamp=now,
            final_route_target="premium",
            requested_model="nebula-auto",
            estimated_cost=0.002,
            prompt_tokens=800,
            completion_tokens=256,
            route_signals={
                "route_mode": "calibrated",
                "calibrated_routing": True,
                "degraded_routing": False,
                "token_count": 900,
                "complexity_tier": "medium",
                "keyword_match": True,
                "score_components": {"total_score": 1.0},
            },
        )
    ]
    store = FakeSimulationGovernanceStore(records)
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings),
        policy_service=PolicyService(settings, store, PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")),
    )

    response = await service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(calibrated_routing_enabled=False),
            limit=10,
            changed_sample_limit=10,
        ),
    )

    assert response.summary.evaluated_rows == 1
    assert response.summary.changed_routes == 1
    changed = response.changed_requests[0]
    assert changed.baseline_route_target == "premium"
    assert changed.simulated_route_target == "local"
    assert changed.simulated_route_reason == "calibrated_routing_disabled"
    assert changed.simulated_policy_outcome == "calibrated_routing=disabled"
    assert changed.baseline_route_mode == "calibrated"
    assert changed.baseline_calibrated_routing is True
    assert changed.baseline_degraded_routing is False
    assert changed.baseline_route_score == 1.0
    assert changed.simulated_route_mode is None
    assert changed.simulated_calibrated_routing is None
    assert changed.simulated_degraded_routing is None
    assert changed.simulated_route_score is None


@pytest.mark.asyncio
async def test_policy_simulation_reports_newly_denied_requests_without_mutation() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-premium",
            timestamp=now,
            final_route_target="premium",
            requested_model="openai/gpt-4o-mini",
            estimated_cost=0.002,
            prompt_tokens=400,
            completion_tokens=512,
            route_signals={"token_count": 400, "complexity_tier": "low", "keyword_match": False},
        )
    ]
    store = FakeSimulationGovernanceStore(records)
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings),
        policy_service=PolicyService(settings, store, PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")),
    )

    response = await service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(
                routing_mode_default="premium_only",
                allowed_premium_models=["openai/gpt-4o-mini"],
                max_premium_cost_per_request=0.000001,
            ),
            limit=5,
            changed_sample_limit=5,
        ),
    )

    assert response.summary.evaluated_rows == 1
    assert response.summary.newly_denied == 1
    assert response.changed_requests[0].baseline_route_target == "premium"
    assert response.changed_requests[0].simulated_route_target == "denied"
    assert response.changed_requests[0].simulated_terminal_status == "policy_denied"
    assert "Request exceeds the tenant premium spend guardrail." in (
        response.changed_requests[0].simulated_policy_outcome or ""
    )
    assert store.record_usage_calls == []
    assert store.policy_updates == []


@pytest.mark.asyncio
async def test_policy_simulation_scopes_by_tenant_and_window_and_handles_empty_results() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-in-window",
            timestamp=now,
            tenant_id="default",
            route_signals={"token_count": 120, "complexity_tier": "low", "keyword_match": False},
        ),
        _ledger_record(
            request_id="req-other-tenant",
            timestamp=now,
            tenant_id="other",
            route_signals={"token_count": 120, "complexity_tier": "low", "keyword_match": False},
        ),
        _ledger_record(
            request_id="req-old",
            timestamp=now.replace(year=now.year - 1),
            tenant_id="default",
            route_signals={"token_count": 120, "complexity_tier": "low", "keyword_match": False},
        ),
    ]
    store = FakeSimulationGovernanceStore(records)
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings),
        policy_service=PolicyService(settings, store, PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")),
    )

    response = await service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(),
            from_timestamp=now.replace(second=max(0, now.second - 1)),
            to_timestamp=now.replace(second=min(59, now.second + 1)),
            limit=10,
            changed_sample_limit=10,
        ),
    )

    assert response.summary.evaluated_rows == 1
    assert response.window.returned_rows == 1
    assert response.changed_requests == []

    empty_response = await service.simulate(
        tenant_context=tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=TenantPolicy(),
            from_timestamp=now.replace(year=now.year - 2),
            to_timestamp=now.replace(year=now.year - 2),
            limit=10,
            changed_sample_limit=10,
        ),
    )

    assert empty_response.summary.evaluated_rows == 0
    assert empty_response.summary.changed_routes == 0
    assert empty_response.summary.newly_denied == 0
    assert empty_response.window.returned_rows == 0
    assert empty_response.changed_requests == []


def test_policy_simulation_response_model_is_bounded_and_comparison_first() -> None:
    response = PolicySimulationRequest(
        candidate_policy=TenantPolicy(),
        limit=200,
        changed_sample_limit=50,
    )

    assert response.limit == 200
    assert response.changed_sample_limit == 50

    with pytest.raises(ValidationError):
        PolicySimulationRequest(
            candidate_policy=TenantPolicy(),
            changed_sample_limit=51,
        )


@pytest.mark.asyncio
async def test_recommendation_service_orders_and_bounds_recommendations_without_mutation() -> None:
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id="req-premium-1",
            timestamp=now,
            final_route_target="premium",
            estimated_cost=0.020,
            prompt_tokens=900,
            completion_tokens=300,
        ),
        _ledger_record(
            request_id="req-premium-2",
            timestamp=now.replace(microsecond=1),
            final_route_target="premium",
            estimated_cost=0.015,
            prompt_tokens=850,
            completion_tokens=280,
        ),
        _ledger_record(
            request_id="req-premium-3",
            timestamp=now.replace(microsecond=2),
            final_route_target="premium",
            estimated_cost=0.012,
            prompt_tokens=820,
            completion_tokens=260,
        ),
        _ledger_record(
            request_id="req-cache-hit",
            timestamp=now.replace(microsecond=3),
            final_route_target="premium",
            terminal_status="cache_hit",
            estimated_cost=0.008,
            route_reason="semantic_cache",
        ).model_copy(update={"cache_hit": True}),
        _ledger_record(
            request_id="req-denied",
            timestamp=now.replace(microsecond=4),
            final_route_target="premium",
            terminal_status="policy_denied",
            estimated_cost=0.0,
            policy_outcome="denied=Request exceeds the tenant premium spend guardrail.",
        ),
    ]
    store = FakeSimulationGovernanceStore(records)
    cache_service = FakeCacheService(
        health_status_payload={
            "status": "degraded",
            "required": False,
            "detail": "Qdrant unavailable: connection refused",
            "enabled": False,
        }
    )
    settings = Settings()
    recommendation_service = RecommendationService(
        governance_store=store,
        policy_simulation_service=PolicySimulationService(
            governance_store=store,
            router_service=RouterService(settings),
            policy_service=PolicyService(
                settings,
                store,
                PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
            ),
        ),
        semantic_cache_service=cache_service,
    )

    bundle = await recommendation_service.build_summary(
        tenant_context=AuthenticatedTenantContext(
            tenant=tenant_context().tenant,
            api_key=tenant_context().api_key,
            policy=TenantPolicy(
                semantic_cache_enabled=True,
                semantic_cache_similarity_threshold=0.82,
                semantic_cache_max_entry_age_hours=48,
            ),
        )
    )

    assert isinstance(bundle, RecommendationBundle)
    assert bundle.window_requests_evaluated == 5
    assert len(bundle.recommendations) == 3
    assert [item.code for item in bundle.recommendations] == [
        "restore_semantic_cache_runtime",
        "review_premium_routing_pressure",
        "inspect_policy_denials",
    ]
    assert bundle.cache_summary.runtime_status == "degraded"
    assert bundle.cache_summary.similarity_threshold == 0.82
    assert bundle.cache_summary.max_entry_age_hours == 48
    assert bundle.cache_summary.avoided_premium_cost_usd == 0.008
    assert len(bundle.cache_summary.insights) == 2
    assert store.record_usage_calls == []
    assert store.policy_updates == []
    assert store.list_usage_records_calls[-1]["tenant_id"] == "default"
    assert store.list_usage_records_calls[-1]["limit"] == 200


@pytest.mark.asyncio
async def test_recommendation_service_surfaces_low_cache_hit_guidance_when_runtime_is_healthy() -> None:
    now = datetime.now(UTC)
    records = [
        _ledger_record(
            request_id=f"req-{index}",
            timestamp=now.replace(microsecond=index),
            final_route_target="local" if index % 2 == 0 else "premium",
            estimated_cost=0.003 if index % 2 else 0.0,
            prompt_tokens=120,
            completion_tokens=40,
        )
        for index in range(6)
    ]
    store = FakeSimulationGovernanceStore(records)
    cache_service = FakeCacheService()
    settings = Settings()
    recommendation_service = RecommendationService(
        governance_store=store,
        policy_simulation_service=PolicySimulationService(
            governance_store=store,
            router_service=RouterService(settings),
            policy_service=PolicyService(
                settings,
                store,
                PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
            ),
        ),
        semantic_cache_service=cache_service,
    )

    bundle = await recommendation_service.build_summary(
        tenant_context=AuthenticatedTenantContext(
            tenant=tenant_context().tenant,
            api_key=tenant_context().api_key,
            policy=TenantPolicy(
                semantic_cache_enabled=True,
                semantic_cache_similarity_threshold=0.95,
                semantic_cache_max_entry_age_hours=24,
            ),
        )
    )

    assert bundle.cache_summary.runtime_status == "ready"
    assert bundle.cache_summary.estimated_hit_rate == 0
    assert bundle.recommendations[0].code == "tune_semantic_cache_threshold"
    assert bundle.recommendations[0].evidence[1].value == "0.95"
    assert store.record_usage_calls == []
    assert store.policy_updates == []


@pytest.mark.asyncio
async def test_recommendation_service_returns_no_action_summary_for_quiet_healthy_window() -> None:
    store = FakeSimulationGovernanceStore([])
    cache_service = FakeCacheService()
    settings = Settings()
    recommendation_service = RecommendationService(
        governance_store=store,
        policy_simulation_service=PolicySimulationService(
            governance_store=store,
            router_service=RouterService(settings),
            policy_service=PolicyService(
                settings,
                store,
                PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
            ),
        ),
        semantic_cache_service=cache_service,
    )

    bundle = await recommendation_service.build_summary(tenant_context=tenant_context())

    assert bundle.window_requests_evaluated == 0
    assert [item.code for item in bundle.recommendations] == ["no_action_needed"]
    assert bundle.cache_summary.runtime_status == "ready"
    assert bundle.cache_summary.insights[0].code == "cache_runtime_ready"
    assert store.record_usage_calls == []
    assert store.policy_updates == []


    single = EmbeddingsRequest(model="nomic-embed-text", input="hello")
    batch = EmbeddingsRequest(model="nomic-embed-text", input=["first", "second"])

    assert single.input == "hello"
    assert batch.input == ["first", "second"]

    with pytest.raises(ValidationError):
        EmbeddingsRequest(model="nomic-embed-text", input=[])

    with pytest.raises(ValidationError):
        EmbeddingsRequest(model="nomic-embed-text", input=[["nested"]])

    with pytest.raises(ValidationError):
        EmbeddingsRequest(model="   ", input="hello")


@pytest.mark.asyncio
async def test_embeddings_service_passes_through_requested_model_for_single_input() -> None:
    service = OllamaEmbeddingsService(Settings())
    stub_client = StubAsyncClient(
        responses=[StubAsyncResponse(json_body={"embeddings": [[0.1, 0.2, 0.3]]})]
    )
    service.client = stub_client  # type: ignore[assignment]

    result = await service.create_embeddings(model="custom-embed-model", input="hello")

    assert stub_client.calls == [
        (
            "/api/embed",
            {"model": "custom-embed-model", "input": "hello"},
        )
    ]
    assert result.model == "custom-embed-model"
    assert result.data[0].index == 0
    assert result.data[0].embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embeddings_service_preserves_batch_ordering() -> None:
    service = OllamaEmbeddingsService(Settings())
    stub_client = StubAsyncClient(
        responses=[
            StubAsyncResponse(
                json_body={
                    "embeddings": [
                        [1.0, 1.1],
                        [2.0, 2.2],
                    ]
                }
            )
        ]
    )
    service.client = stub_client  # type: ignore[assignment]

    result = await service.create_embeddings(
        model="batch-model",
        input=["first prompt", "second prompt"],
    )

    assert stub_client.calls == [
        (
            "/api/embed",
            {"model": "batch-model", "input": ["first prompt", "second prompt"]},
        )
    ]
    assert [item.index for item in result.data] == [0, 1]
    assert [item.embedding for item in result.data] == [[1.0, 1.1], [2.0, 2.2]]


@pytest.mark.asyncio
async def test_embeddings_service_rejects_blank_input_explicitly() -> None:
    service = OllamaEmbeddingsService(Settings())

    with pytest.raises(EmbeddingsValidationError) as exc_info:
        await service.create_embeddings(model="batch-model", input="   ")

    assert str(exc_info.value) == "Embedding input must not be blank."


@pytest.mark.asyncio
async def test_embeddings_service_raises_upstream_error_on_http_failure() -> None:
    service = OllamaEmbeddingsService(Settings())
    stub_client = StubAsyncClient(error=httpx.ConnectError("connection refused"))
    service.client = stub_client  # type: ignore[assignment]

    with pytest.raises(EmbeddingsUpstreamError) as exc_info:
        await service.create_embeddings(model="batch-model", input="hello")

    assert str(exc_info.value) == "Ollama embeddings request failed."


@pytest.mark.asyncio
async def test_embeddings_service_rejects_empty_upstream_embeddings() -> None:
    service = OllamaEmbeddingsService(Settings())
    stub_client = StubAsyncClient(responses=[StubAsyncResponse(json_body={"embeddings": []})])
    service.client = stub_client  # type: ignore[assignment]

    with pytest.raises(EmbeddingsEmptyResultError) as exc_info:
        await service.create_embeddings(model="batch-model", input="hello")

    assert str(exc_info.value) == "Ollama returned no embeddings."
