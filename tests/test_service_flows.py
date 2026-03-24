from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import ApiKeyRecord, TenantPolicy, TenantRecord
from nebula.models.openai import ChatCompletionRequest, EmbeddingsRequest
from nebula.services.embeddings_service import (
    EmbeddingsEmptyResultError,
    EmbeddingsUpstreamError,
    EmbeddingsValidationError,
    OllamaEmbeddingsService,
)
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


def test_embeddings_request_accepts_string_or_flat_list_only() -> None:
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
