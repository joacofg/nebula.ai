"""Premium fallback after a local failure obeys the tenant policy, streaming or not."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from nebula.providers.base import CompletionChunk, CompletionResult
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
def fallback_client(**policy_updates: object) -> Iterator[tuple[TestClient, object, StubProvider]]:
    """A gateway whose local provider is down and whose premium provider records its calls."""
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
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


def _ledger_rows(client: TestClient, response) -> list[dict]:
    ledger = client.get(
        f"/v1/admin/usage/ledger?request_id={response.headers['X-Request-ID']}",
        headers=admin_headers(),
    )
    assert ledger.status_code == 200
    return ledger.json()


@STREAM_MODES
def test_failed_fallback_records_premium_row(stream: bool) -> None:
    with fallback_client() as (client, _container, premium):
        premium.completion_error = provider_error("premium down")
        premium.stream_error = provider_error("premium down")
        response = _chat(client, stream=stream)
        rows = _ledger_rows(client, response)

    assert response.status_code == 502
    assert response.json() == {"detail": "premium down"}
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
    assert response.json() == {"detail": detail}
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
