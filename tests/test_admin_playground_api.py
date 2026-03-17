from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.providers.base import CompletionResult
from tests.support import FakeCacheService, StubProvider, admin_headers, configured_app, usage


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
            model="openai/gpt-4o-mini",
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
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hello from playground"}],
                    "stream": False,
                },
            )

            request_id = response.headers.get("X-Request-ID")
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    assert request_id
    assert response.json()["request_id"] == request_id
    assert response.json()["choices"][0]["message"]["content"] == "premium response"
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Provider"] == "mock-premium"
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert response.headers["X-Nebula-Policy-Outcome"]
    assert ledger.status_code == 200
    assert len(ledger.json()) == 1
    assert ledger.json()[0]["request_id"] == request_id


def test_usage_ledger_request_id_filter() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(app)
            first = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "first"}],
                    "stream": False,
                },
            )
            second = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "openai/gpt-4o-mini",
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
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": False,
                },
            )

    assert response.status_code == 404
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
                    "model": "openai/gpt-4o-mini",
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
