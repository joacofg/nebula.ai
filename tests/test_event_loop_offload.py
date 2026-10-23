"""B17: the sync SQLAlchemy governance store never runs on the event loop.

A blocking store call on the loop stalls every other request in flight. The only
deliberate exception is the ledger write in the streaming `finally`, which must not be
awaited while the generator may be closing after a client disconnect.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from nebula.api.dependencies import get_embeddings_service
from nebula.models.governance import TenantPolicy
from nebula.providers.base import CompletionChunk, CompletionResult
from tests.support import StubProvider, admin_headers, auth_headers, configured_app, usage

POLICY_READS = ("tenant_spend_total", "summarize_calibration_evidence")
CHAT_BODY = {"model": "nebula-auto", "messages": [{"role": "user", "content": "hi"}]}


def record_loop_calls(store, names) -> list[tuple[str, bool]]:
    """Wrap the named store methods; each call appends (name, on_loop)."""
    calls: list[tuple[str, bool]] = []

    def wrap(name: str, method: Callable):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            try:
                asyncio.get_running_loop()
                on_loop = True
            except RuntimeError:
                on_loop = False
            calls.append((name, on_loop))
            return method(*args, **kwargs)

        return wrapper

    for name in names:
        setattr(store, name, wrap(name, getattr(store, name)))
    return calls


def _stub_local(app) -> None:
    container = app.state.container
    model = container.settings.local_model
    container.local_provider = container.provider_registry.local_provider = StubProvider(
        "ollama",
        completion_result=CompletionResult(content="ok", model=model, provider="ollama", usage=usage()),
        stream_chunks=[
            CompletionChunk(delta="ok", model=model),
            CompletionChunk(delta="", model=model, finish_reason="stop"),
        ],
    )


def _no_cache(app, **policy) -> None:
    """Keep the semantic cache (and its Qdrant lookups) out of these requests."""
    app.state.container.governance_store.upsert_policy(
        "default", TenantPolicy(semantic_cache_enabled=False, **policy)
    )


def _calls_named(calls: list[tuple[str, bool]], name: str) -> list[bool]:
    return [on_loop for called, on_loop in calls if called == name]


def test_chat_completion_store_calls_run_off_the_loop() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _stub_local(app)
            _no_cache(app)
            calls = record_loop_calls(
                app.state.container.governance_store,
                (*POLICY_READS, "record_usage"),
            )
            response = client.post("/v1/chat/completions", headers=auth_headers(), json=CHAT_BODY)

    assert response.status_code == 200
    for name in (*POLICY_READS, "record_usage"):
        assert _calls_named(calls, name), f"{name} was never called"
    assert [c for c in calls if c[1]] == []


def test_streaming_ledger_write_is_the_only_on_loop_call() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _stub_local(app)
            _no_cache(app)
            calls = record_loop_calls(
                app.state.container.governance_store,
                (*POLICY_READS, "record_usage"),
            )
            response = client.post(
                "/v1/chat/completions", headers=auth_headers(), json={**CHAT_BODY, "stream": True}
            )

    assert response.status_code == 200
    # The documented exception: the stream's `finally` cannot await while the generator closes.
    assert _calls_named(calls, "record_usage") == [True]
    for name in POLICY_READS:
        assert _calls_named(calls, name) and not any(_calls_named(calls, name))


class _Embeddings:
    async def create_embeddings(self, *, model, input):
        return type(
            "R",
            (),
            {
                "model": model,
                "data": [type("EmbeddingVector", (), {"index": 0, "embedding": [0.1, 0.2]})],
            },
        )

    async def close(self) -> None:
        return None


def test_embeddings_ledger_write_runs_off_the_loop() -> None:
    with configured_app() as app:
        app.dependency_overrides[get_embeddings_service] = lambda: _Embeddings()
        with TestClient(app) as client:
            calls = record_loop_calls(app.state.container.governance_store, ("record_usage",))
            response = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": "hola"},
            )

    assert response.status_code == 200
    assert _calls_named(calls, "record_usage") == [False]


def test_rate_limited_rejection_write_runs_off_the_loop() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _stub_local(app)
            _no_cache(app, rate_limit_requests_per_minute=1)
            calls = record_loop_calls(app.state.container.governance_store, ("record_usage",))
            first = client.post("/v1/chat/completions", headers=auth_headers(), json=CHAT_BODY)
            rejected = client.post("/v1/chat/completions", headers=auth_headers(), json=CHAT_BODY)

    assert (first.status_code, rejected.status_code) == (200, 429)
    # One row for the served request and one for the rejection, both off the loop.
    assert _calls_named(calls, "record_usage") == [False, False]


def test_policy_denial_write_runs_off_the_loop() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _stub_local(app)
            _no_cache(app, allowed_premium_models=["not-the-premium-model"])
            calls = record_loop_calls(app.state.container.governance_store, ("record_usage",))
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={"model": app.state.container.settings.premium_model, "messages": CHAT_BODY["messages"]},
            )

    assert response.status_code == 403
    assert _calls_named(calls, "record_usage") == [False]


ADMIN_STORE_METHODS = (
    "list_tenants",
    "get_tenant",
    "get_policy",
    "upsert_policy",
    "list_usage_records",
    "list_api_keys",
    "operator_api_key",
    "summarize_calibration_evidence",
    "tenant_spend_total",
    "tenant_spend_before",
)


@pytest.mark.parametrize(
    ("method", "path", "expected_store_method"),
    [
        ("GET", "/v1/admin/tenants", "list_tenants"),
        ("GET", "/v1/admin/tenants/default/policy", "get_policy"),
        ("PUT", "/v1/admin/tenants/default/policy", "upsert_policy"),
        ("GET", "/v1/admin/usage/ledger", "list_usage_records"),
        ("POST", "/v1/admin/tenants/default/policy/simulate", "tenant_spend_before"),
        ("GET", "/v1/admin/tenants/default/recommendations", "summarize_calibration_evidence"),
        ("GET", "/v1/admin/api-keys", "list_api_keys"),
    ],
)
def test_admin_store_calls_run_off_the_loop(
    method: str, path: str, expected_store_method: str
) -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _stub_local(app)
            _no_cache(app)
            # A ledger row, so the simulation has something to replay.
            seeded = client.post("/v1/chat/completions", headers=auth_headers(), json=CHAT_BODY)
            assert seeded.status_code == 200
            policy = client.get("/v1/admin/tenants/default/policy", headers=admin_headers()).json()
            bodies = {
                "PUT": policy,
                "POST": {"candidate_policy": policy},
            }
            calls = record_loop_calls(app.state.container.governance_store, ADMIN_STORE_METHODS)
            response = client.request(method, path, headers=admin_headers(), json=bodies.get(method))

    assert response.status_code == 200, response.text
    assert _calls_named(calls, expected_store_method), f"{expected_store_method} was never called"
    assert [c for c in calls if c[1]] == []


def test_simulation_without_records_skips_the_spend_read() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            policy = client.get("/v1/admin/tenants/default/policy", headers=admin_headers()).json()
            calls = record_loop_calls(app.state.container.governance_store, ADMIN_STORE_METHODS)
            response = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={"candidate_policy": policy},
            )

    assert response.status_code == 200, response.text
    assert response.json()["summary"]["evaluated_rows"] == 0
    assert _calls_named(calls, "list_usage_records")
    assert not _calls_named(calls, "tenant_spend_before")


def test_playground_store_calls_run_off_the_loop() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _stub_local(app)
            _no_cache(app)
            calls = record_loop_calls(
                app.state.container.governance_store, (*ADMIN_STORE_METHODS, "record_usage")
            )
            response = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={**CHAT_BODY, "tenant_id": "default"},
            )

    assert response.status_code == 200, response.text
    assert calls
    assert [c for c in calls if c[1]] == []
