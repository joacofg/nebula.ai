"""Premium fallback after a local failure obeys the tenant policy, streaming or not."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from nebula.core.container import ServiceContainer
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionResult, ProviderError
from nebula.services.auth_service import AuthenticatedTenantContext
from tests.support import (
    FakeCacheService,
    StubProvider,
    admin_headers,
    auth_headers,
    configured_app,
    provider_error,
    usage,
)

STREAM_MODES = pytest.mark.parametrize("stream", [False, True], ids=["non_stream", "stream"])


@contextmanager
def fallback_client(
    **policy_updates: object,
) -> Iterator[tuple[TestClient, ServiceContainer, StubProvider]]:
    """A gateway whose local provider is down and whose premium provider records its calls."""
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container: ServiceContainer = app.state.container
            settings = container.settings
            local = StubProvider(
                "ollama",
                completion_error=provider_error("ollama down"),
                stream_error=provider_error("ollama down"),
            )
            premium = StubProvider(
                "mock-premium",
                completion_result=CompletionResult(
                    content="premium answer",
                    model=settings.premium_model,
                    provider="mock-premium",
                    usage=usage(),
                ),
                stream_chunks=[
                    CompletionChunk(delta="premium answer", model=settings.premium_model),
                    CompletionChunk(delta="", model=settings.premium_model, finish_reason="stop"),
                ],
            )
            container.local_provider = local
            container.provider_registry.local_provider = local
            container.premium_provider = premium
            container.provider_registry.premium_provider = premium
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service
            if policy_updates:
                store = container.governance_store
                store.upsert_policy(
                    "default", store.get_policy("default").model_copy(update=policy_updates)
                )
            yield client, container, premium


def _chat(client: TestClient, *, stream: bool, model: str = "nebula-auto", **extra: object):
    return client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={
            "model": model,
            "stream": stream,
            "messages": [{"role": "user", "content": "Say hi."}],
            **extra,
        },
    )


def _ledger_rows_for(client: TestClient, request_id: str) -> list[dict]:
    ledger = client.get(
        f"/v1/admin/usage/ledger?request_id={request_id}",
        headers=admin_headers(),
    )
    assert ledger.status_code == 200
    return ledger.json()


def _ledger_rows(client: TestClient, response) -> list[dict]:
    return _ledger_rows_for(client, response.headers["X-Request-ID"])


@STREAM_MODES
def test_failed_fallback_records_premium_row(stream: bool) -> None:
    with fallback_client() as (client, _container, premium):
        premium.completion_error = provider_error("premium down")
        premium.stream_error = provider_error("premium down")
        response = _chat(client, stream=stream)
        rows = _ledger_rows(client, response)

    assert response.status_code == 502
    assert response.json()["detail"] == "premium down"
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Route-Reason"] == "local_provider_error_fallback"
    assert response.headers["X-Nebula-Provider"] == "mock-premium"
    assert response.headers["X-Nebula-Fallback-Used"] == "true"
    assert len(rows) == 1
    assert rows[0]["final_route_target"] == "premium"
    assert rows[0]["route_reason"] == "local_provider_error_fallback"
    assert rows[0]["final_provider"] == "mock-premium"
    assert rows[0]["fallback_used"] is True
    assert rows[0]["terminal_status"] == "provider_error"


def _assert_fallback_blocked(client: TestClient, response, premium: StubProvider, detail: str) -> None:
    rows = _ledger_rows(client, response)
    assert response.status_code == 502
    assert response.json()["detail"] == detail
    assert premium.requests == []
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Route-Reason"] == "local_provider_error_fallback_blocked"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert len(rows) == 1
    assert rows[0]["final_route_target"] == "local"
    assert rows[0]["route_reason"] == "local_provider_error_fallback_blocked"
    assert rows[0]["terminal_status"] == "provider_error"
    assert rows[0]["fallback_used"] is False


@STREAM_MODES
def test_fallback_blocked_by_local_only(stream: bool) -> None:
    with fallback_client(routing_mode_default="local_only") as (client, _container, premium):
        response = _chat(client, stream=stream)
        _assert_fallback_blocked(
            client,
            response,
            premium,
            "Local provider failed and tenant policy restricts routing to local only.",
        )


@STREAM_MODES
def test_fallback_blocked_by_hard_budget(stream: bool) -> None:
    # Spend 0 already meets a 0.0 limit; downgrade enforcement must not open a premium fallback.
    with fallback_client(hard_budget_limit_usd=0.0, hard_budget_enforcement="downgrade") as (
        client,
        _container,
        premium,
    ):
        response = _chat(client, stream=stream)
        _assert_fallback_blocked(
            client,
            response,
            premium,
            "Local provider failed and the tenant hard budget is exhausted.",
        )


@STREAM_MODES
def test_fallback_sends_explicit_premium_model(stream: bool) -> None:
    with fallback_client() as (client, container, premium):
        settings = container.settings
        assert settings.economy_model is None
        response = _chat(client, stream=stream, model=settings.local_model)

    assert response.status_code == 200
    assert response.headers["X-Nebula-Fallback-Used"] == "true"
    assert response.headers["X-Nebula-Route-Tier"] == "frontier"
    assert [sent.model for sent in premium.requests] == [settings.premium_model]


@STREAM_MODES
def test_fallback_blocked_by_allowlist(stream: bool) -> None:
    with fallback_client(allowed_premium_models=["some/other-model"]) as (client, container, premium):
        settings = container.settings
        assert settings.economy_model is None
        response = _chat(client, stream=stream)
        _assert_fallback_blocked(
            client,
            response,
            premium,
            "Local provider failed and premium model "
            f"'{settings.premium_model}' is not allowed for this tenant.",
        )


@STREAM_MODES
def test_fallback_allowed_with_empty_allowlist(stream: bool) -> None:
    # An empty allowlist means "any model", not "nothing allowed".
    with fallback_client(allowed_premium_models=[]) as (client, _container, premium):
        response = _chat(client, stream=stream)

    assert response.status_code == 200
    assert response.headers["X-Nebula-Fallback-Used"] == "true"
    assert len(premium.requests) == 1


@STREAM_MODES
def test_fallback_blocked_by_cost_cap(stream: bool) -> None:
    with fallback_client(max_premium_cost_per_request=0.0000001) as (client, _container, premium):
        response = _chat(client, stream=stream, max_tokens=4000)
        _assert_fallback_blocked(
            client,
            response,
            premium,
            "Local provider failed and the premium fallback exceeds the tenant per-request cost limit.",
        )


@STREAM_MODES
def test_fallback_blocked_by_disabled_fallback(stream: bool) -> None:
    with fallback_client(fallback_enabled=False) as (client, _container, premium):
        response = _chat(client, stream=stream)
        _assert_fallback_blocked(
            client,
            response,
            premium,
            "Local provider failed and tenant policy disabled premium fallback.",
        )


@STREAM_MODES
def test_primary_premium_failure_records_one_row_with_headers(stream: bool) -> None:
    with fallback_client() as (client, container, premium):
        premium.completion_error = provider_error("premium down")
        premium.stream_error = provider_error("premium down")
        response = _chat(client, stream=stream, model=container.settings.premium_model)
        rows = _ledger_rows(client, response)

    assert response.status_code == 502
    assert response.json()["detail"] == "premium down"
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert response.headers["X-Nebula-Provider"] == "mock-premium"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert len(rows) == 1
    assert rows[0]["final_route_target"] == "premium"
    assert rows[0]["route_reason"] == "explicit_premium_model"
    assert rows[0]["final_provider"] == "mock-premium"
    assert rows[0]["fallback_used"] is False
    assert rows[0]["terminal_status"] == "provider_error"


# Every fallback guard holds at once; each case relaxes the guards above it in the spec table,
# so the detail must name the first guard still holding.
_ALL_GUARDS: dict[str, object] = {
    "fallback_enabled": False,
    "routing_mode_default": "local_only",
    "hard_budget_limit_usd": 0.0,
    "hard_budget_enforcement": "downgrade",
    "allowed_premium_models": ["some/other-model"],
    "max_premium_cost_per_request": 0.0000001,
}
_NO_LOCAL_ONLY: dict[str, object] = {"fallback_enabled": True, "routing_mode_default": "auto"}
_NO_BUDGET: dict[str, object] = {
    **_NO_LOCAL_ONLY,
    "hard_budget_limit_usd": None,
    "hard_budget_enforcement": None,
}
_DISALLOWED_PREMIUM = (
    "Local provider failed and premium model '{premium_model}' is not allowed for this tenant."
)


@STREAM_MODES
@pytest.mark.parametrize(
    ("relaxed", "detail"),
    [
        ({}, "Local provider failed and tenant policy disabled premium fallback."),
        (
            {"fallback_enabled": True},
            "Local provider failed and tenant policy restricts routing to local only.",
        ),
        (_NO_LOCAL_ONLY, "Local provider failed and the tenant hard budget is exhausted."),
        (_NO_BUDGET, _DISALLOWED_PREMIUM),
    ],
    ids=["disabled_first", "local_only_next", "hard_budget_next", "allowlist_next"],
)
def test_fallback_block_reason_follows_table_order(
    stream: bool, relaxed: dict[str, object], detail: str
) -> None:
    with fallback_client(**{**_ALL_GUARDS, **relaxed}) as (client, container, premium):
        response = _chat(client, stream=stream, max_tokens=4000)
        expected = detail.format(premium_model=container.settings.premium_model)
        _assert_fallback_blocked(client, response, premium, expected)


# Streams the client abandons or the upstream cuts short: one ledger row each, whatever the exit.


class _MidStreamProvider(StubProvider):
    """Streams one chunk, then `then` runs: the upstream failing or stalling."""

    def __init__(self, name: str, *, model: str, then: Callable[[], Awaitable[None]]) -> None:
        super().__init__(name)
        self.model = model
        self.then = then

    def stream_complete(self, request: ChatCompletionRequest):
        self.requests.append(request)

        async def iterator():
            yield CompletionChunk(delta="partial answer", model=self.model)
            await self.then()

        return iterator()


async def _upstream_dies() -> None:
    raise provider_error("upstream died")


async def _upstream_stalls() -> None:
    await asyncio.Event().wait()


def _use_premium(container: ServiceContainer, provider: StubProvider) -> None:
    container.premium_provider = provider
    container.provider_registry.premium_provider = provider


def _stream_request(model: str) -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model=model,
        stream=True,
        messages=[{"role": "user", "content": "Say hi."}],
    )


def _tenant_context(container: ServiceContainer) -> AuthenticatedTenantContext:
    return container.auth_service.resolve_tenant_context(
        raw_api_key="nebula-dev-key", explicit_tenant_id="default"
    )


def _content_of(event: bytes) -> str | None:
    payload = event.removeprefix(b"data: ").strip()
    if payload == b"[DONE]":
        return None
    return json.loads(payload)["choices"][0]["delta"].get("content")


async def _read_first_content(stream: AsyncIterator[bytes]) -> None:
    async for event in stream:
        if _content_of(event):
            return
    raise AssertionError("the stream ended without any content")


async def test_abandoned_premium_stream_is_recorded() -> None:
    with fallback_client() as (client, container, premium):
        model = container.settings.premium_model
        premium.stream_chunks = [
            *(CompletionChunk(delta=f"word{n} ", model=model) for n in range(4)),
            CompletionChunk(delta="", model=model, finish_reason="stop"),
        ]
        envelope = await container.chat_service.stream_completion_with_metadata(
            _stream_request(model),
            tenant_context=_tenant_context(container),
            request_id="req-abandoned",
        )
        await _read_first_content(envelope.stream)
        await envelope.stream.aclose()  # what a disconnecting client does to the generator
        rows = _ledger_rows_for(client, "req-abandoned")

    assert len(rows) == 1
    assert rows[0]["terminal_status"] == "client_disconnected"
    assert rows[0]["final_route_target"] == "premium"
    assert rows[0]["completion_tokens"] > 0
    assert rows[0]["estimated_cost"] > 0


async def test_cancelled_premium_stream_is_recorded() -> None:
    # Starlette cancels the task serving a response when the client drops the connection.
    with fallback_client() as (client, container, _premium):
        model = container.settings.premium_model
        _use_premium(container, _MidStreamProvider("mock-premium", model=model, then=_upstream_stalls))
        envelope = await container.chat_service.stream_completion_with_metadata(
            _stream_request(model),
            tenant_context=_tenant_context(container),
            request_id="req-cancelled",
        )
        first_content = asyncio.Event()

        async def serve() -> None:
            async for event in envelope.stream:
                if _content_of(event):
                    first_content.set()

        serving = asyncio.create_task(serve())
        await asyncio.wait_for(first_content.wait(), timeout=5)
        serving.cancel()
        with pytest.raises(asyncio.CancelledError):
            await serving
        rows = _ledger_rows_for(client, "req-cancelled")

    assert len(rows) == 1
    assert rows[0]["terminal_status"] == "client_disconnected"
    assert rows[0]["completion_tokens"] > 0
    assert rows[0]["estimated_cost"] > 0


async def test_abandoned_stream_counts_toward_the_hard_budget() -> None:
    # Spend 0 is under this limit, so the first stream runs; whatever it cost must then count.
    with fallback_client(hard_budget_limit_usd=0.000000001) as (client, container, premium):
        model = container.settings.premium_model
        premium.stream_chunks = [
            CompletionChunk(delta="word ", model=model),
            CompletionChunk(delta="", model=model, finish_reason="stop"),
        ]
        envelope = await container.chat_service.stream_completion_with_metadata(
            _stream_request(model),
            tenant_context=_tenant_context(container),
            request_id="req-budget",
        )
        await _read_first_content(envelope.stream)
        await envelope.stream.aclose()
        follow_up = _chat(client, stream=False, model=model)

    assert follow_up.status_code == 403
    assert "hard_budget=exceeded" in follow_up.headers["X-Nebula-Policy-Outcome"]


@pytest.mark.parametrize("via_fallback", [False, True], ids=["premium_primary", "after_fallback"])
async def test_mid_stream_error_records_one_row(via_fallback: bool) -> None:
    # Once a chunk is out the stream cannot fall back again, so the wrapper alone records it.
    with fallback_client() as (client, container, _premium):
        model = container.settings.premium_model
        _use_premium(container, _MidStreamProvider("mock-premium", model=model, then=_upstream_dies))
        envelope = await container.chat_service.stream_completion_with_metadata(
            _stream_request("nebula-auto" if via_fallback else model),
            tenant_context=_tenant_context(container),
            request_id="req-mid-stream",
        )
        with pytest.raises(ProviderError, match="upstream died"):
            async for _event in envelope.stream:
                pass
        rows = _ledger_rows_for(client, "req-mid-stream")

    assert envelope.metadata.fallback_used is via_fallback
    assert len(rows) == 1
    assert rows[0]["terminal_status"] == "provider_error"
    assert rows[0]["final_provider"] == "mock-premium"
    assert rows[0]["fallback_used"] is via_fallback
