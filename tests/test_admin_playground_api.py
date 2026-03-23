from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.providers.base import CompletionResult
from tests.support import FakeCacheService, StubProvider, admin_headers, auth_headers, configured_app, usage


def _mount_runtime(app) -> None:
    container = app.state.container
    container.local_provider = StubProvider(
        "ollama",
        completion_result=CompletionResult(
            content="local response",
            model="llama3.2:3b",
            provider="ollama",
            usage=usage(),
        ),
    )
    container.provider_registry.local_provider = container.local_provider
    container.premium_provider = StubProvider(
        "mock-premium",
        completion_result=CompletionResult(
            content="premium response",
            model="gpt-4o-mini",
            provider="mock-premium",
            usage=usage(12, 6),
        ),
    )
    container.provider_registry.premium_provider = container.premium_provider
    container.cache_service = FakeCacheService()
    container.chat_service.cache_service = container.cache_service


def test_admin_playground_completion() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            response = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hello from playground"}],
                    "stream": False,
                },
            )

            request_id = response.headers.get("X-Request-ID")
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    ledger_body = ledger.json()

    assert response.status_code == 200
    assert request_id
    assert response.json()["request_id"] == request_id
    assert response.json()["choices"][0]["message"]["content"] == "premium response"
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert response.headers["X-Nebula-Provider"] == "mock-premium"
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert response.headers["X-Nebula-Policy-Mode"] == "auto"
    assert response.headers["X-Nebula-Policy-Outcome"] == "default"
    assert ledger.status_code == 200
    assert len(ledger_body) == 1
    assert ledger_body[0]["request_id"] == request_id
    assert ledger_body[0]["tenant_id"] == response.headers["X-Nebula-Tenant-ID"]
    assert ledger_body[0]["final_route_target"] == response.headers["X-Nebula-Route-Target"]
    assert ledger_body[0]["final_provider"] == response.headers["X-Nebula-Provider"]
    assert ledger_body[0]["fallback_used"] is False
    assert ledger_body[0]["cache_hit"] is False
    assert ledger_body[0]["route_reason"] == response.headers["X-Nebula-Route-Reason"]
    assert ledger_body[0]["policy_outcome"] == response.headers["X-Nebula-Policy-Outcome"]
    assert ledger_body[0]["terminal_status"] == "completed"
    assert response.headers["X-Nebula-Route-Target"] != "local"


def test_usage_ledger_request_id_filter() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            first = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "first"}],
                    "stream": False,
                },
            )
            second = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "second"}],
                    "stream": False,
                },
            )
            filtered = client.get(
                f"/v1/admin/usage/ledger?request_id={first.headers['X-Request-ID']}",
                headers=admin_headers(),
            )

    assert first.status_code == 200
    assert second.status_code == 200
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["request_id"] == first.headers["X-Request-ID"]


def test_admin_playground_completion_rejects_unknown_tenant() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            response = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "missing-tenant",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": False,
                },
            )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"]
    assert response.json() == {"detail": "Tenant not found."}


def test_admin_playground_completion_rejects_inactive_tenant_without_usage_record() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            app.state.container.governance_store.update_tenant("default", active=False)
            response = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "inactive"}],
                    "stream": False,
                },
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert response.status_code == 403
    assert response.json() == {"detail": "Tenant is inactive."}
    assert ledger.status_code == 200
    assert ledger.json() == []


def test_admin_playground_is_admin_only_and_not_public_auth_compatible() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            response = client.post(
                "/v1/admin/playground/completions",
                headers=auth_headers(),
                json={
                    "tenant_id": "default",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": False,
                },
            )

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid admin API key."}
    assert "X-Nebula-Tenant-ID" not in response.headers
    assert "X-Nebula-Route-Target" not in response.headers


def test_admin_playground_rejects_streaming_even_for_admin_requests() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            response = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hello from playground"}],
                    "stream": True,
                },
            )

    assert response.status_code == 400
    assert response.headers["X-Request-ID"]
    assert response.json() == {
        "detail": "Playground only supports non-streaming requests in Phase 3."
    }
