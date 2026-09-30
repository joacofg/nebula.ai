from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from nebula.models.governance import TenantPolicy
from tests.support import admin_headers, configured_app


def test_rate_limit_defaults_to_unlimited_and_rejects_nonsense() -> None:
    assert TenantPolicy().rate_limit_requests_per_minute is None
    assert TenantPolicy(rate_limit_requests_per_minute=60).rate_limit_requests_per_minute == 60
    for bad in (0, -1, 100_001):
        with pytest.raises(ValidationError):
            TenantPolicy(rate_limit_requests_per_minute=bad)


def test_store_round_trips_the_rate_limit_and_options_list_it() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            store = app.state.container.governance_store
            store.upsert_policy("default", TenantPolicy(rate_limit_requests_per_minute=30))
            reread = store.get_policy("default")
            options = client.get("/v1/admin/policy/options", headers=admin_headers()).json()

    assert reread.rate_limit_requests_per_minute == 30
    assert "rate_limit_requests_per_minute" in options["runtime_enforced_fields"]


from nebula.api.dependencies import get_embeddings_service  # noqa: E402
from nebula.providers.base import CompletionChunk, CompletionResult  # noqa: E402
from tests.support import StubProvider, auth_headers, usage  # noqa: E402


class _CountingProvider(StubProvider):
    def __init__(self, name: str, model: str) -> None:
        super().__init__(
            name,
            completion_result=CompletionResult(content="ok", model=model, provider=name, usage=usage()),
            stream_chunks=[CompletionChunk(delta="ok", model=model),
                           CompletionChunk(delta="", model=model, finish_reason="stop")],
        )
        self.calls = 0

    async def complete(self, request):
        self.calls += 1
        return await super().complete(request)

    def stream_complete(self, request):
        self.calls += 1
        return super().stream_complete(request)


class _Embeddings:
    def __init__(self) -> None:
        self.calls = 0

    async def create_embeddings(self, *, model, input):
        self.calls += 1

        class R:
            pass

        r = R()
        r.model = model
        r.data = [type("EmbeddingVector", (), {"index": 0, "embedding": [0.1, 0.2]})]
        return r

    async def close(self) -> None:
        return None


def _mount(app):
    container = app.state.container
    local = _CountingProvider("ollama", container.settings.local_model)
    premium = _CountingProvider("openai-compatible", container.settings.premium_model)
    container.local_provider = container.provider_registry.local_provider = local
    container.premium_provider = container.provider_registry.premium_provider = premium
    return local, premium


def _chat(client, *, stream=False, key="nebula-dev-key"):
    return client.post("/v1/chat/completions", headers=auth_headers(key),
                       json={"model": "nebula-auto", "stream": stream,
                             "messages": [{"role": "user", "content": "hi"}]})


def _limit(app, tenant="default", rpm=2):
    store = app.state.container.governance_store
    store.upsert_policy(tenant, TenantPolicy(rate_limit_requests_per_minute=rpm, semantic_cache_enabled=False))


def test_the_request_over_the_limit_is_429_and_never_reaches_a_provider() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            local, premium = _mount(app)
            _limit(app)
            first, second, third = (_chat(client) for _ in range(3))
            calls = local.calls + premium.calls

    assert first.status_code == second.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "2"
    assert first.headers["X-RateLimit-Remaining"] == "1"
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert third.status_code == 429
    assert int(third.headers["Retry-After"]) >= 1
    assert third.headers["X-Nebula-Route-Target"] == "denied"
    assert third.headers["X-Nebula-Route-Reason"] == "rate_limited"
    assert calls == 2


def test_streaming_responses_carry_the_rate_limit_headers() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount(app)
            _limit(app, rpm=5)
            response = _chat(client, stream=True)

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "5"
    assert response.headers["X-RateLimit-Remaining"] == "4"


def test_without_a_limit_nothing_changes() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount(app)
            responses = [_chat(client) for _ in range(5)]

    assert all(r.status_code == 200 for r in responses)
    assert "X-RateLimit-Limit" not in responses[0].headers


def test_the_rejection_is_in_the_ledger() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount(app)
            _limit(app, rpm=1)
            _chat(client)
            denied = _chat(client)
            rows = client.get(f"/v1/admin/usage/ledger?request_id={denied.headers['X-Request-ID']}",
                              headers=admin_headers()).json()

    assert len(rows) == 1
    assert rows[0]["terminal_status"] == "rate_limited"
    assert rows[0]["final_route_target"] == "denied"
    assert rows[0]["route_reason"] == "rate_limited"
    assert rows[0]["message_type"] == "chat"


def test_embeddings_are_limited_too() -> None:
    with configured_app() as app:
        service = _Embeddings()
        app.dependency_overrides[get_embeddings_service] = lambda: service
        with TestClient(app) as client:
            _limit(app, rpm=1)
            body = {"model": "nomic-embed-text", "input": "hola"}
            ok = client.post("/v1/embeddings", headers=auth_headers(), json=body)
            denied = client.post("/v1/embeddings", headers=auth_headers(), json=body)

    assert ok.status_code == 200 and denied.status_code == 429
    assert service.calls == 1
