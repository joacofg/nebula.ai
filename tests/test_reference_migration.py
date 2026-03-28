from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.providers.base import CompletionResult
from tests.support import (
    FakeCacheService,
    StubProvider,
    admin_headers,
    configured_app,
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


MIGRATED_CHAT_COMPLETIONS_REQUEST = {
    "model": "nebula-auto",
    "messages": [
        {"role": "system", "content": "You are a concise migration assistant."},
        {"role": "user", "content": "Summarize why this request proves minimal migration."},
    ],
}


def test_reference_migration_proves_public_headers_and_usage_ledger_correlation() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            _mount_runtime(
                app,
                local_provider=StubProvider(
                    "ollama",
                    completion_result=CompletionResult(
                        content="Nebula preserved the chat-completions shape.",
                        model=container.settings.local_model,
                        provider="ollama",
                        usage=usage(12, 6),
                    ),
                ),
                premium_provider=StubProvider(
                    "mock-premium",
                    completion_result=CompletionResult(
                        content="premium fallback response",
                        model=container.settings.premium_model,
                        provider="mock-premium",
                        usage=usage(18, 7),
                    ),
                ),
                cache_service=FakeCacheService(),
            )

            response = client.post(
                "/v1/chat/completions",
                headers={"X-Nebula-API-Key": "nebula-dev-key"},
                json=MIGRATED_CHAT_COMPLETIONS_REQUEST,
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )
            playground = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": response.headers["X-Nebula-Tenant-ID"],
                    "model": container.settings.premium_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Corroborate the routed result without changing the public proof boundary.",
                        }
                    ],
                    "stream": False,
                },
            )
            playground_request_id = playground.headers["X-Request-ID"]
            playground_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={playground_request_id}",
                headers=admin_headers(),
            )

    body = response.json()
    ledger_body = ledger.json()
    playground_body = playground.json()
    playground_ledger_body = playground_ledger.json()

    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == (
        "Nebula preserved the chat-completions shape."
    )
    assert body["model"] == "llama3.2:3b"
    assert body["usage"] == {
        "prompt_tokens": 12,
        "completion_tokens": 6,
        "total_tokens": 18,
    }

    public_evidence = {
        "request_id": request_id,
        "tenant_id": response.headers["X-Nebula-Tenant-ID"],
        "route_target": response.headers["X-Nebula-Route-Target"],
        "route_reason": response.headers["X-Nebula-Route-Reason"],
        "provider": response.headers["X-Nebula-Provider"],
        "cache_hit": response.headers["X-Nebula-Cache-Hit"],
        "fallback_used": response.headers["X-Nebula-Fallback-Used"],
        "policy_mode": response.headers["X-Nebula-Policy-Mode"],
        "policy_outcome": response.headers["X-Nebula-Policy-Outcome"],
    }

    assert public_evidence == {
        "request_id": request_id,
        "tenant_id": "default",
        "route_target": "local",
        "route_reason": "token_complexity",
        "provider": "ollama",
        "cache_hit": "false",
        "fallback_used": "false",
        "policy_mode": "auto",
        "policy_outcome": "default",
    }

    assert ledger.status_code == 200
    assert len(ledger_body) == 1
    assert ledger_body[0]["request_id"] == public_evidence["request_id"]
    assert ledger_body[0]["tenant_id"] == public_evidence["tenant_id"]
    assert ledger_body[0]["requested_model"] == MIGRATED_CHAT_COMPLETIONS_REQUEST["model"]
    assert ledger_body[0]["final_route_target"] == public_evidence["route_target"]
    assert ledger_body[0]["final_provider"] == public_evidence["provider"]
    assert ledger_body[0]["fallback_used"] is False
    assert ledger_body[0]["cache_hit"] is False
    assert ledger_body[0]["response_model"] == body["model"]
    assert ledger_body[0]["prompt_tokens"] == body["usage"]["prompt_tokens"]
    assert ledger_body[0]["completion_tokens"] == body["usage"]["completion_tokens"]
    assert ledger_body[0]["total_tokens"] == body["usage"]["total_tokens"]
    assert ledger_body[0]["terminal_status"] == "completed"
    assert ledger_body[0]["route_reason"] == public_evidence["route_reason"]
    assert ledger_body[0]["policy_outcome"] == public_evidence["policy_outcome"]

    assert playground.status_code == 200
    assert playground_request_id
    assert playground_request_id != request_id
    assert playground_body["request_id"] == playground_request_id
    assert playground.headers["X-Nebula-Tenant-ID"] == public_evidence["tenant_id"]
    assert playground.headers["X-Nebula-Route-Target"] == "premium"
    assert playground.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert playground.headers["X-Nebula-Provider"] == "mock-premium"
    assert playground.headers["X-Nebula-Policy-Outcome"] == "default"

    assert playground_ledger.status_code == 200
    assert len(playground_ledger_body) == 1
    assert playground_ledger_body[0]["request_id"] == playground_request_id
    assert playground_ledger_body[0]["tenant_id"] == public_evidence["tenant_id"]
    assert playground_ledger_body[0]["final_route_target"] == playground.headers["X-Nebula-Route-Target"]
    assert playground_ledger_body[0]["final_provider"] == playground.headers["X-Nebula-Provider"]
    assert playground_ledger_body[0]["route_reason"] == playground.headers["X-Nebula-Route-Reason"]
    assert playground_ledger_body[0]["policy_outcome"] == playground.headers["X-Nebula-Policy-Outcome"]



def test_reference_migration_requires_tenant_header_only_for_ambiguous_multi_tenant_keys() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            _mount_runtime(
                app,
                local_provider=StubProvider(
                    "ollama",
                    completion_result=CompletionResult(
                        content="tenant-specific response",
                        model=container.settings.local_model,
                        provider="ollama",
                        usage=usage(9, 5),
                    ),
                ),
                cache_service=FakeCacheService(),
            )
            client.post(
                "/v1/admin/tenants",
                headers=admin_headers(),
                json={"id": "team-b", "name": "Team B"},
            )
            create_key = client.post(
                "/v1/admin/api-keys",
                headers=admin_headers(),
                json={
                    "name": "shared-reference-key",
                    "tenant_id": None,
                    "allowed_tenant_ids": ["default", "team-b"],
                },
            )
            shared_key = create_key.json()["api_key"]

            missing_tenant = client.post(
                "/v1/chat/completions",
                headers={"X-Nebula-API-Key": shared_key},
                json=MIGRATED_CHAT_COMPLETIONS_REQUEST,
            )
            resolved_tenant = client.post(
                "/v1/chat/completions",
                headers={
                    "X-Nebula-API-Key": shared_key,
                    "X-Nebula-Tenant-ID": "team-b",
                },
                json=MIGRATED_CHAT_COMPLETIONS_REQUEST,
            )
            request_id = resolved_tenant.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    ledger_body = ledger.json()

    assert create_key.status_code == 201

    assert missing_tenant.status_code == 403
    assert missing_tenant.json() == {"detail": "Tenant header is required for this API key."}
    assert "X-Nebula-Tenant-ID" not in missing_tenant.headers
    assert "X-Nebula-Route-Target" not in missing_tenant.headers

    assert resolved_tenant.status_code == 200
    assert resolved_tenant.json()["object"] == "chat.completion"
    assert resolved_tenant.headers["X-Nebula-Tenant-ID"] == "team-b"
    assert resolved_tenant.headers["X-Nebula-Route-Target"] == "local"
    assert resolved_tenant.headers["X-Nebula-Provider"] == "ollama"
    assert resolved_tenant.headers["X-Nebula-Policy-Outcome"] == "default"

    assert ledger.status_code == 200
    assert len(ledger_body) == 1
    assert ledger_body[0]["request_id"] == request_id
    assert ledger_body[0]["tenant_id"] == "team-b"
    assert ledger_body[0]["terminal_status"] == "completed"
    assert ledger_body[0]["final_route_target"] == resolved_tenant.headers["X-Nebula-Route-Target"]
    assert ledger_body[0]["policy_outcome"] == resolved_tenant.headers["X-Nebula-Policy-Outcome"]
