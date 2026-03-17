from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import ApiKeyRecord, TenantPolicy, TenantRecord
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionResult, CompletionUsage, ProviderError
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.chat_service import ChatService
from nebula.services.policy_service import PolicyResolution, PolicyService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouteDecision, RouterService
from tests.support import FakeCacheService, StubProvider

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeGovernanceStore:
    def __init__(self) -> None:
        self.records = []

    def record_usage(self, record) -> None:
        self.records.append(record)


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


@pytest.mark.asyncio
async def test_create_completion_falls_back_to_premium_when_local_provider_fails() -> None:
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

    with pytest.raises(Exception):
        await service.create_completion(
            request,
            tenant_context=tenant_context(),
            request_id="req-policy",
        )

    assert cache_service.lookup_calls == []
    assert store.records[-1].terminal_status == "provider_error"


class RuntimePolicyStore:
    def __init__(self, *, spend_total: float = 0.0) -> None:
        self.spend_total = spend_total

    def tenant_spend_total(self, tenant_id: str) -> float:
        assert tenant_id == "default"
        return self.spend_total


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
    assert resolution.policy_outcome == "cache=disabled;fallback=disabled;soft_budget=exceeded"
