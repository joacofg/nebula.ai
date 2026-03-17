from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.models.governance import TenantPolicy
from nebula.providers.base import CompletionResult
from tests.support import (
    FakeCacheService,
    StubProvider,
    admin_headers,
    auth_headers,
    configured_app,
    provider_error,
    usage,
)


def _mount_runtime(app, *, local_provider=None, premium_provider=None, cache_service=None) -> None:
    container = app.state.container
    if local_provider is not None:
        container.local_provider = local_provider
        container.provider_registry.local_provider = local_provider
    if premium_provider is not None:
        container.premium_provider = premium_provider
        container.provider_registry.premium_provider = premium_provider
    if cache_service is not None:
        container.cache_service = cache_service
        container.chat_service.cache_service = cache_service


def test_authentication_returns_401_and_403_for_missing_invalid_and_unauthorized_credentials() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            payload = {"model": "nebula-auto", "messages": [{"role": "user", "content": "hello"}]}

            missing = client.post("/v1/chat/completions", json=payload)
            invalid = client.post(
                "/v1/chat/completions",
                headers=auth_headers(api_key="invalid-key"),
                json=payload,
            )
            client.post(
                "/v1/admin/tenants",
                headers=admin_headers(),
                json={"id": "other", "name": "Other Workspace"},
            )
            forbidden = client.post(
                "/v1/chat/completions",
                headers=auth_headers(tenant_id="other"),
                json=payload,
            )

    assert missing.status_code == 401
    assert missing.json() == {"detail": "Missing client API key."}
    assert invalid.status_code == 401
    assert invalid.json() == {"detail": "Invalid client API key."}
    assert forbidden.status_code == 403
    assert forbidden.json() == {"detail": "API key is not authorized for the requested tenant."}


def test_admin_endpoints_manage_tenants_keys_and_policy() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            create_tenant = client.post(
                "/v1/admin/tenants",
                headers=admin_headers(),
                json={
                    "id": "team-a",
                    "name": "Team A",
                    "description": "Platform team",
                    "policy": {
                        "routing_mode_default": "premium_only",
                        "allowed_premium_models": ["openai/gpt-4o-mini"],
                    },
                },
            )
            create_key = client.post(
                "/v1/admin/api-keys",
                headers=admin_headers(),
                json={
                    "name": "team-a-key",
                    "tenant_id": "team-a",
                    "allowed_tenant_ids": ["team-a"],
                },
            )
            policy = client.get("/v1/admin/tenants/team-a/policy", headers=admin_headers())
            update_policy = client.put(
                "/v1/admin/tenants/team-a/policy",
                headers=admin_headers(),
                json={
                    "routing_mode_default": "auto",
                    "allowed_premium_models": ["openai/gpt-4o-mini", "gpt-4o-mini"],
                    "semantic_cache_enabled": False,
                    "fallback_enabled": False,
                    "max_premium_cost_per_request": 0.5,
                },
            )
            listed_keys = client.get("/v1/admin/api-keys?tenant_id=team-a", headers=admin_headers())

    assert create_tenant.status_code == 201
    assert create_key.status_code == 201
    assert create_key.json()["api_key"].startswith("nbk_")
    assert policy.json()["routing_mode_default"] == "premium_only"
    assert update_policy.status_code == 200
    assert update_policy.json()["semantic_cache_enabled"] is False
    assert listed_keys.status_code == 200
    assert listed_keys.json()[0]["tenant_id"] == "team-a"


def test_admin_session_endpoint() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            unauthorized = client.get("/v1/admin/session")
            invalid = client.get(
                "/v1/admin/session",
                headers=admin_headers(admin_api_key="invalid-admin-key"),
            )
            authorized = client.get("/v1/admin/session", headers=admin_headers())

    assert unauthorized.status_code == 401
    assert unauthorized.json() == {"detail": "Missing or invalid admin API key."}
    assert invalid.status_code == 401
    assert invalid.json() == {"detail": "Missing or invalid admin API key."}
    assert authorized.status_code == 200
    assert authorized.json() == {"status": "ok"}


def test_policy_options_endpoint_is_admin_protected_and_includes_default_model() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            unauthorized = client.get("/v1/admin/policy/options")
            invalid = client.get(
                "/v1/admin/policy/options",
                headers=admin_headers(admin_api_key="invalid-admin-key"),
            )
            authorized = client.get("/v1/admin/policy/options", headers=admin_headers())

    assert unauthorized.status_code == 401
    assert unauthorized.json() == {"detail": "Missing or invalid admin API key."}
    assert invalid.status_code == 401
    assert invalid.json() == {"detail": "Missing or invalid admin API key."}
    assert authorized.status_code == 200
    assert authorized.json()["default_premium_model"] == "openai/gpt-4o-mini"
    assert "openai/gpt-4o-mini" in authorized.json()["known_premium_models"]
    assert authorized.json()["runtime_enforced_fields"] == [
        "routing_mode_default",
        "allowed_premium_models",
        "semantic_cache_enabled",
        "fallback_enabled",
        "max_premium_cost_per_request",
    ]
    assert authorized.json()["soft_signal_fields"] == ["soft_budget_usd"]
    assert authorized.json()["advisory_fields"] == [
        "prompt_capture_enabled",
        "response_capture_enabled",
    ]


def test_usage_ledger_tracks_local_premium_cache_and_fallback_outcomes() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(
                app,
                local_provider=StubProvider(
                    "ollama",
                    completion_result=CompletionResult(
                        content="local response",
                        model="llama3.2:3b",
                        provider="ollama",
                        usage=usage(),
                    ),
                ),
                premium_provider=StubProvider(
                    "mock-premium",
                    completion_result=CompletionResult(
                        content="premium response",
                        model="openai/gpt-4o-mini",
                        provider="mock-premium",
                        usage=usage(10, 5),
                    ),
                ),
                cache_service=FakeCacheService(),
            )

            client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "llama3.2:3b",
                    "messages": [{"role": "user", "content": "local"}],
                },
            )
            client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "premium"}],
                },
            )
            app.state.container.cache_service.cached_response = "cached response"
            client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "cache"}],
                },
            )
            app.state.container.cache_service.cached_response = None
            app.state.container.local_provider.completion_error = provider_error("offline")
            client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "fallback"}],
                },
            )
            ledger = client.get(
                "/v1/admin/usage/ledger?tenant_id=default&limit=10",
                headers=admin_headers(),
            )

    body = ledger.json()
    statuses = {(entry["terminal_status"], entry["final_route_target"]) for entry in body}

    assert ledger.status_code == 200
    assert ("completed", "local") in statuses
    assert ("completed", "premium") in statuses
    assert ("cache_hit", "cache") in statuses
    assert ("fallback_completed", "premium") in statuses


def test_policy_can_block_premium_models_and_fallback() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(
                app,
                local_provider=StubProvider(
                    "ollama",
                    completion_error=provider_error("offline"),
                ),
                premium_provider=StubProvider(
                    "mock-premium",
                    completion_result=CompletionResult(
                        content="premium response",
                        model="openai/gpt-4o-mini",
                        provider="mock-premium",
                        usage=usage(10, 5),
                    ),
                ),
                cache_service=FakeCacheService(),
            )
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    fallback_enabled=False,
                ).model_dump(mode="json"),
            )
            premium_denied = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4.1-mini",
                    "messages": [{"role": "user", "content": "premium denied"}],
                },
            )
            fallback_blocked = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "fallback blocked"}],
                },
            )
            denied_entries = client.get(
                "/v1/admin/usage/ledger?tenant_id=default&terminal_status=policy_denied",
                headers=admin_headers(),
            )
            denied_request_id = premium_denied.headers["X-Request-ID"]
            denied_by_request = client.get(
                f"/v1/admin/usage/ledger?request_id={denied_request_id}",
                headers=admin_headers(),
            )
            fallback_request_id = fallback_blocked.headers["X-Request-ID"]
            fallback_by_request = client.get(
                f"/v1/admin/usage/ledger?request_id={fallback_request_id}",
                headers=admin_headers(),
            )

    assert premium_denied.status_code == 403
    assert premium_denied.json() == {
        "detail": "Premium model 'openai/gpt-4.1-mini' is not allowed for this tenant."
    }
    assert fallback_blocked.status_code == 502
    assert fallback_blocked.json() == {
        "detail": "Local provider failed and tenant policy disabled premium fallback."
    }
    assert denied_entries.status_code == 200
    assert denied_entries.json()[0]["final_route_target"] == "denied"
    assert denied_by_request.status_code == 200
    assert denied_by_request.json()[0]["request_id"] == denied_request_id
    assert denied_by_request.json()[0]["route_reason"] == "explicit_premium_model"
    assert denied_by_request.json()[0]["policy_outcome"] == premium_denied.json()["detail"]
    assert fallback_by_request.status_code == 200
    assert fallback_by_request.json()[0]["request_id"] == fallback_request_id
    assert fallback_by_request.json()[0]["route_reason"] == "local_provider_error_fallback_blocked"
    assert (
        fallback_by_request.json()[0]["policy_outcome"]
        == fallback_blocked.headers["X-Nebula-Policy-Outcome"]
    )


def test_policy_can_disable_cache() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            cache_service = FakeCacheService(cached_response="cached response")
            _mount_runtime(
                app,
                local_provider=StubProvider(
                    "ollama",
                    completion_result=CompletionResult(
                        content="local response",
                        model="llama3.2:3b",
                        provider="ollama",
                        usage=usage(),
                    ),
                ),
                cache_service=cache_service,
            )
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    allowed_premium_models=["gpt-4o-mini"],
                    semantic_cache_enabled=False,
                ).model_dump(mode="json"),
            )
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "cache disabled"}],
                },
            )

    assert response.status_code == 200
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Policy-Outcome"] == "cache=disabled"
    assert cache_service.lookup_calls == []


def test_inactive_tenant_chat_request_returns_exact_403_detail() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            app.state.container.governance_store.update_tenant("default", active=False)
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "inactive tenant"}],
                },
            )

    assert response.status_code == 403
    assert response.json() == {"detail": "Resolved tenant is inactive or does not exist."}


def test_spend_guardrail_denial_returns_exact_detail_and_ledger_correlation() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            _mount_runtime(
                app,
                premium_provider=StubProvider(
                    "mock-premium",
                    completion_result=CompletionResult(
                        content="premium response",
                        model="openai/gpt-4o-mini",
                        provider="mock-premium",
                        usage=usage(10, 5),
                    ),
                ),
                cache_service=FakeCacheService(),
            )
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    routing_mode_default="premium_only",
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    max_premium_cost_per_request=0.0001,
                ).model_dump(mode="json"),
            )
            denied = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": "guardrail denied"}],
                },
            )
            request_id = denied.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert denied.status_code == 403
    assert denied.json() == {"detail": "Request exceeds the tenant premium spend guardrail."}
    assert ledger.status_code == 200
    assert ledger.json()[0]["request_id"] == request_id
    assert ledger.json()[0]["policy_outcome"] == "Request exceeds the tenant premium spend guardrail."
