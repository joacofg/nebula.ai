from fastapi.testclient import TestClient

from nebula.models.governance import TenantPolicy
from nebula.providers.base import CompletionChunk, CompletionResult
from tests.support import (
    FakeCacheService,
    StubProvider,
    admin_headers,
    auth_headers,
    configured_app,
    usage,
)


def test_chat_completions_returns_openai_like_payload() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="local response",
                    model=container.settings.local_model,
                    provider="ollama",
                    usage=usage(),
                ),
            )
            container.provider_registry.local_provider = container.local_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service

            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [
                        {"role": "system", "content": "You are Nebula."},
                        {"role": "user", "content": "Hello Nebula"},
                    ],
                },
            )

    body = response.json()

    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["model"] == "llama3.2:3b"
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Provider"] == "ollama"
    assert float(response.headers["X-Nebula-Route-Score"]) > 0.0
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert response.headers["X-Nebula-Policy-Mode"] == "auto"
    assert body["usage"]["prompt_tokens"] > 0
    assert body["usage"]["completion_tokens"] > 0


def test_chat_completions_streams_sse() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.local_provider = StubProvider(
                "ollama",
                stream_chunks=[
                    CompletionChunk(delta="hello ", model=container.settings.local_model),
                    CompletionChunk(delta="stream", model=container.settings.local_model),
                    CompletionChunk(delta="", model=container.settings.local_model, finish_reason="stop"),
                ],
            )
            container.provider_registry.local_provider = container.local_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service

            with client.stream(
                "POST",
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "stream": True,
                    "messages": [
                        {"role": "user", "content": "Hello streaming"},
                    ],
                },
            ) as response:
                body = b"".join(response.iter_bytes())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["connection"] == "keep-alive"
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Provider"] == "ollama"
    assert float(response.headers["X-Nebula-Route-Score"]) > 0.0
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert response.headers["X-Nebula-Policy-Outcome"] == "default"
    assert b"data: " in body
    assert b"chat.completion.chunk" in body
    assert b"[DONE]" in body


def test_chat_completions_persist_governed_ledger_markers_from_tenant_policy() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.governance_store.upsert_policy(
                "default",
                container.governance_store.get_policy("default").model_copy(
                    update={
                        "evidence_retention_window": "7d",
                        "metadata_minimization_level": "strict",
                    }
                ),
            )
            container.local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="governed local response",
                    model=container.settings.local_model,
                    provider="ollama",
                    usage=usage(9, 4),
                ),
            )
            container.provider_registry.local_provider = container.local_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service

            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "Need a governed ledger row."}],
                },
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers={"X-Nebula-Admin-Key": "nebula-admin-key"},
            )

    assert response.status_code == 200
    assert ledger.status_code == 200
    body = ledger.json()
    assert len(body) == 1
    row = body[0]
    assert row["request_id"] == request_id
    assert row["message_type"] == "chat"
    assert row["evidence_retention_window"] == "7d"
    assert row["metadata_minimization_level"] == "strict"
    assert row["metadata_fields_suppressed"] == ["route_signals"]
    assert row["route_signals"] is None
    assert row["governance_source"] == "tenant_policy"
    assert row["evidence_expires_at"] is not None


def test_chat_completions_outcome_grounded_request_persists_matching_route_signals() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="seeded local route",
                    model=container.settings.local_model,
                    provider="ollama",
                    usage=usage(12, 4),
                ),
            )
            container.provider_registry.local_provider = container.local_provider
            container.premium_provider = StubProvider(
                "mock-premium",
                completion_result=CompletionResult(
                    content="outcome grounded premium route",
                    model=container.settings.premium_model,
                    provider="mock-premium",
                    usage=usage(24, 8),
                ),
            )
            container.provider_registry.premium_provider = container.premium_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service

            for index in range(5):
                seeded = client.post(
                    "/v1/chat/completions",
                    headers=auth_headers(),
                    json={
                        "model": "nebula-auto",
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Seed thin evidence request {index}.",
                            }
                        ],
                    },
                )
                assert seeded.status_code == 200
                assert seeded.headers["X-Nebula-Route-Target"] == "local"

            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Analyze a short routing answer.",
                        }
                    ],
                },
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert response.headers["X-Nebula-Route-Mode"] == "calibrated"
    assert "outcome_evidence=sufficient" in response.headers["X-Nebula-Policy-Outcome"]
    route_score = float(response.headers["X-Nebula-Route-Score"])
    assert route_score == 0.466

    assert ledger.status_code == 200
    rows = ledger.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["request_id"] == request_id
    assert row["final_route_target"] == response.headers["X-Nebula-Route-Target"] == "premium"
    assert row["final_provider"] == response.headers["X-Nebula-Provider"] == "mock-premium"
    assert row["route_reason"] == response.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert row["policy_outcome"] == response.headers["X-Nebula-Policy-Outcome"]
    assert row["route_signals"]["route_mode"] == response.headers["X-Nebula-Route-Mode"]
    assert row["route_signals"]["calibrated_routing"] is True
    assert row["route_signals"]["degraded_routing"] is False
    assert row["route_signals"]["replay"] is False
    assert row["route_signals"]["outcome_evidence"] == {
        "state": "sufficient",
        "state_reason": "Eligible calibrated routing evidence meets the tenant sufficiency threshold.",
        "eligible_request_count": 5,
        "sufficient_request_count": 5,
        "degraded_request_count": 0,
        "gated_request_count": 0,
        "excluded_request_count": 0,
    }
    assert row["route_signals"]["score_components"] == {
        "token_score": 0.016,
        "keyword_bonus": 0.2,
        "policy_bonus": 0.1,
        "budget_penalty": 0.0,
        "outcome_bonus": 0.15,
        "evidence_penalty": 0.0,
        "total_score": route_score,
    }


def test_chat_completions_outcome_grounded_policy_denial_persists_evidence_state_without_route_signals() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="seeded local route",
                    model=container.settings.local_model,
                    provider="ollama",
                    usage=usage(12, 4),
                ),
            )
            container.provider_registry.local_provider = container.local_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    routing_mode_default="auto",
                    allowed_premium_models=[container.settings.premium_model],
                    max_premium_cost_per_request=0.000001,
                ).model_dump(mode="json"),
            )

            for index in range(5):
                seeded = client.post(
                    "/v1/chat/completions",
                    headers=auth_headers(),
                    json={
                        "model": "nebula-auto",
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Seed thin evidence request {index}.",
                            }
                        ],
                    },
                )
                assert seeded.status_code == 200

            denied = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": "deny expensive premium route"}],
                },
            )
            request_id = denied.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert denied.status_code == 403
    assert denied.headers["X-Nebula-Route-Target"] == "premium"
    assert denied.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert "X-Nebula-Route-Mode" not in denied.headers
    assert "outcome_evidence=sufficient" in denied.headers["X-Nebula-Policy-Outcome"]
    assert denied.json() == {"detail": "Request exceeds the tenant premium spend guardrail."}

    assert ledger.status_code == 200
    rows = ledger.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["request_id"] == request_id
    assert row["final_route_target"] == "denied"
    assert row["final_provider"] is None
    assert row["terminal_status"] == "policy_denied"
    assert row["route_reason"] == denied.headers["X-Nebula-Route-Reason"]
    assert row["policy_outcome"] == denied.headers["X-Nebula-Policy-Outcome"]
    assert row["route_signals"] is None


def test_chat_completions_require_nebula_auth_headers_not_bearer_authorization() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer nebula-dev-key"},
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "hello"}],
                },
            )

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing client API key."}
    assert "X-Nebula-Tenant-ID" not in response.headers


def test_chat_completions_allow_bootstrap_key_without_explicit_tenant_header() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="local response",
                    model=container.settings.local_model,
                    provider="ollama",
                    usage=usage(),
                ),
            )
            container.provider_registry.local_provider = container.local_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service

            response = client.post(
                "/v1/chat/completions",
                headers={"X-Nebula-API-Key": "nebula-dev-key"},
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "hello"}],
                },
            )

    assert response.status_code == 200
    assert response.headers["X-Nebula-Tenant-ID"] == "default"


def test_chat_completions_reject_requests_without_a_user_message() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [
                        {"role": "system", "content": "You are Nebula."},
                        {"role": "assistant", "content": "How can I help?"},
                    ],
                },
            )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0]["loc"] == ["body"]
    assert detail[0]["type"] == "value_error"
    assert detail[0]["msg"] == "Value error, At least one user message is required."
