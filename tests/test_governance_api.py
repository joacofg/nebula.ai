from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.db.models import UsageLedgerModel
from nebula.models.governance import TenantPolicy
from nebula.providers.base import CompletionResult
from nebula.services.embeddings_service import EmbeddingsResult, EmbeddingVector
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
        container.recommendation_service.semantic_cache_service = cache_service


def test_admin_tenant_recommendations_endpoint_is_admin_protected() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            unauthorized = client.get("/v1/admin/tenants/default/recommendations")
            invalid = client.get(
                "/v1/admin/tenants/default/recommendations",
                headers=admin_headers(admin_api_key="invalid-admin-key"),
            )

    assert unauthorized.status_code == 401
    assert unauthorized.json() == {"detail": "Missing or invalid admin API key."}
    assert invalid.status_code == 401
    assert invalid.json() == {"detail": "Missing or invalid admin API key."}


def test_admin_tenant_recommendations_returns_404_for_missing_tenant() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get(
                "/v1/admin/tenants/missing/recommendations",
                headers=admin_headers(),
            )

    assert response.status_code == 404
    assert response.json() == {"detail": "Tenant not found."}


def test_admin_tenant_recommendations_are_tenant_scoped_and_bounded() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(
                app,
                cache_service=FakeCacheService(),
            )
            client.post(
                "/v1/admin/tenants",
                headers=admin_headers(),
                json={
                    "id": "team-a",
                    "name": "Team A",
                    "policy": {
                        "routing_mode_default": "auto",
                        "allowed_premium_models": ["openai/gpt-4o-mini"],
                    },
                },
            )
            client.post(
                "/v1/admin/tenants",
                headers=admin_headers(),
                json={
                    "id": "team-b",
                    "name": "Team B",
                    "policy": {
                        "routing_mode_default": "auto",
                        "allowed_premium_models": ["openai/gpt-4o-mini"],
                    },
                },
            )
            team_a_key = client.post(
                "/v1/admin/api-keys",
                headers=admin_headers(),
                json={
                    "name": "team-a-key",
                    "tenant_id": "team-a",
                    "allowed_tenant_ids": ["team-a"],
                },
            ).json()["api_key"]
            team_b_key = client.post(
                "/v1/admin/api-keys",
                headers=admin_headers(),
                json={
                    "name": "team-b-key",
                    "tenant_id": "team-b",
                    "allowed_tenant_ids": ["team-b"],
                },
            ).json()["api_key"]

            for index in range(6):
                client.post(
                    "/v1/chat/completions",
                    headers=auth_headers(api_key=team_a_key, tenant_id="team-a"),
                    json={
                        "model": "nebula-auto",
                        "messages": [{"role": "user", "content": f"team a request {index}"}],
                    },
                )
            client.post(
                "/v1/chat/completions",
                headers=auth_headers(api_key=team_b_key, tenant_id="team-b"),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "team b request"}],
                },
            )

            response = client.get(
                "/v1/admin/tenants/team-a/recommendations",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "team-a"
    assert body["window_requests_evaluated"] == 6
    assert len(body["recommendations"]) <= 3
    assert len(body["cache_summary"]["insights"]) <= 2
    assert all(len(item["evidence"]) <= 4 for item in body["recommendations"])
    assert all(item["label"] and item["value"] for rec in body["recommendations"] for item in rec["evidence"])


def test_admin_tenant_recommendations_propagate_degraded_cache_evidence() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _mount_runtime(
                app,
                cache_service=FakeCacheService(
                    health_status_payload={
                        "status": "degraded",
                        "detail": "Qdrant probe timed out.",
                        "required": False,
                        "enabled": True,
                    }
                ),
            )

            response = client.get(
                "/v1/admin/tenants/default/recommendations",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    body = response.json()
    assert body["cache_summary"]["runtime_status"] == "degraded"
    assert body["cache_summary"]["runtime_detail"] == "Qdrant probe timed out."
    assert body["cache_summary"]["insights"][0]["code"] == "cache_runtime_degraded"
    assert body["cache_summary"]["insights"][0]["evidence"][0] == {
        "label": "runtime_status",
        "value": "degraded",
    }
    assert body["recommendations"][0]["code"] == "restore_semantic_cache_runtime"
    assert body["recommendations"][0]["evidence"][1] == {
        "label": "cache_runtime_detail",
        "value": "Qdrant probe timed out.",
    }


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
    assert update_policy.json()["calibrated_routing_enabled"] is True
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
        "calibrated_routing_enabled",
        "allowed_premium_models",
        "semantic_cache_enabled",
        "semantic_cache_similarity_threshold",
        "semantic_cache_max_entry_age_hours",
        "fallback_enabled",
        "max_premium_cost_per_request",
        "hard_budget_limit_usd",
        "hard_budget_enforcement",
        "evidence_retention_window",
        "metadata_minimization_level",
    ]
    assert authorized.json()["soft_signal_fields"] == ["soft_budget_usd"]
    assert authorized.json()["advisory_fields"] == [
        "prompt_capture_enabled",
        "response_capture_enabled",
    ]


def test_policy_options_endpoint_marks_cache_tuning_controls_as_runtime_enforced() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/v1/admin/policy/options", headers=admin_headers())

    assert response.status_code == 200
    body = response.json()
    runtime_fields = body["runtime_enforced_fields"]
    assert runtime_fields.index("semantic_cache_enabled") < runtime_fields.index(
        "semantic_cache_similarity_threshold"
    )
    assert runtime_fields.index("semantic_cache_similarity_threshold") < runtime_fields.index(
        "semantic_cache_max_entry_age_hours"
    )
    assert "semantic_cache_similarity_threshold" not in body["soft_signal_fields"]
    assert "semantic_cache_max_entry_age_hours" not in body["advisory_fields"]


def test_policy_options_endpoint_marks_evidence_governance_controls_as_runtime_enforced() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/v1/admin/policy/options", headers=admin_headers())

    assert response.status_code == 200
    body = response.json()
    runtime_fields = body["runtime_enforced_fields"]
    assert runtime_fields.index("evidence_retention_window") < runtime_fields.index(
        "metadata_minimization_level"
    )
    assert "evidence_retention_window" not in body["soft_signal_fields"]
    assert "metadata_minimization_level" not in body["advisory_fields"]


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
    by_status = {entry["terminal_status"]: entry for entry in body}

    assert ledger.status_code == 200
    assert by_status["completed"]["final_route_target"] == "local"
    assert by_status["completed"]["final_provider"] == "ollama"
    assert by_status["completed"]["fallback_used"] is False
    assert by_status["completed"]["cache_hit"] is False
    assert by_status["completed"]["policy_outcome"] == "default"

    premium_entries = [entry for entry in body if entry["route_reason"] == "explicit_premium_model"]
    assert len(premium_entries) == 1
    assert premium_entries[0]["terminal_status"] == "completed"
    assert premium_entries[0]["final_route_target"] == "premium"
    assert premium_entries[0]["final_provider"] == "mock-premium"
    assert premium_entries[0]["policy_outcome"] == "default"

    assert by_status["cache_hit"]["final_route_target"] == "cache"
    assert by_status["cache_hit"]["final_provider"] == "cache"
    assert by_status["cache_hit"]["route_reason"] == "cache_hit"
    assert by_status["cache_hit"]["cache_hit"] is True
    assert by_status["cache_hit"]["fallback_used"] is False
    assert by_status["cache_hit"]["policy_outcome"] == "default"

    assert by_status["fallback_completed"]["final_route_target"] == "premium"
    assert by_status["fallback_completed"]["final_provider"] == "mock-premium"
    assert by_status["fallback_completed"]["route_reason"] == "local_provider_error_fallback"
    assert by_status["fallback_completed"]["fallback_used"] is True
    assert by_status["fallback_completed"]["cache_hit"] is False
    assert by_status["fallback_completed"]["policy_outcome"] == "default"


def test_embeddings_requests_can_be_correlated_through_usage_ledger() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            async def stub_create_embeddings(*, model: str, input: str | list[str]) -> EmbeddingsResult:
                inputs = [input] if isinstance(input, str) else input
                return EmbeddingsResult(
                    model=model,
                    data=[
                        EmbeddingVector(index=index, embedding=[float(index), float(index) + 0.5])
                        for index, _ in enumerate(inputs)
                    ],
                )

            app.state.container.embeddings_service.create_embeddings = stub_create_embeddings
            response = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": ["first", "second"]},
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    assert request_id
    assert ledger.status_code == 200
    body = ledger.json()
    assert len(body) == 1
    assert body[0]["request_id"] == request_id
    assert body[0]["tenant_id"] == "default"
    assert body[0]["requested_model"] == "nomic-embed-text"
    assert body[0]["final_route_target"] == "embeddings"
    assert body[0]["final_provider"] == "ollama"
    assert body[0]["terminal_status"] == "completed"
    assert body[0]["route_reason"] == "embeddings_direct"
    assert body[0]["policy_outcome"] == "embeddings=completed"
    assert body[0]["message_type"] == "embeddings"
    assert body[0]["evidence_retention_window"] == "30d"
    assert body[0]["metadata_minimization_level"] == "strict"
    assert body[0]["metadata_fields_suppressed"] == []
    assert body[0]["governance_source"] == "tenant_policy"
    assert body[0]["evidence_expires_at"] is not None
    assert "input" not in body[0]
    assert "embedding" not in body[0]


def test_governed_usage_ledger_cleanup_deletes_only_rows_with_persisted_expiration_markers() -> None:
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
                cache_service=FakeCacheService(),
            )
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    evidence_retention_window="24h",
                    metadata_minimization_level="strict",
                ).model_dump(mode="json"),
            )
            expired_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "expired governed request"}],
                },
            )
            expired_request_id = expired_response.headers["X-Request-ID"]
            expired_before_cleanup = client.get(
                f"/v1/admin/usage/ledger?request_id={expired_request_id}",
                headers=admin_headers(),
            )
            store = app.state.container.governance_store
            expired_record = store.list_usage_records(request_id=expired_request_id)[0]

            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    evidence_retention_window="90d",
                    metadata_minimization_level="standard",
                ).model_dump(mode="json"),
            )
            surviving_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "surviving governed request"}],
                },
            )
            surviving_request_id = surviving_response.headers["X-Request-ID"]
            surviving_before_cleanup = client.get(
                f"/v1/admin/usage/ledger?request_id={surviving_request_id}",
                headers=admin_headers(),
            )

            with store.session_factory() as session:
                session.add(
                    UsageLedgerModel(
                        request_id="no-expiration-marker",
                        tenant_id=expired_record.tenant_id,
                        requested_model=expired_record.requested_model,
                        final_route_target=expired_record.final_route_target,
                        final_provider=expired_record.final_provider,
                        fallback_used=expired_record.fallback_used,
                        cache_hit=expired_record.cache_hit,
                        response_model=expired_record.response_model,
                        prompt_tokens=expired_record.prompt_tokens,
                        completion_tokens=expired_record.completion_tokens,
                        total_tokens=expired_record.total_tokens,
                        estimated_cost=expired_record.estimated_cost,
                        latency_ms=expired_record.latency_ms,
                        timestamp=expired_record.timestamp,
                        terminal_status=expired_record.terminal_status,
                        route_reason=expired_record.route_reason,
                        policy_outcome=expired_record.policy_outcome,
                        route_signals=expired_record.route_signals,
                        message_type=expired_record.message_type,
                        evidence_retention_window=expired_record.evidence_retention_window,
                        evidence_expires_at=None,
                        metadata_minimization_level=expired_record.metadata_minimization_level,
                        metadata_fields_suppressed_json=list(
                            expired_record.metadata_fields_suppressed
                        ),
                        governance_source=expired_record.governance_source,
                    )
                )
                session.commit()
            no_expiration_before_cleanup = client.get(
                "/v1/admin/usage/ledger?request_id=no-expiration-marker",
                headers=admin_headers(),
            )

            cleanup = client.app.state.container
            lifecycle_result = cleanup.retention_lifecycle_service
            cleanup_result = client.app.state.container
            cleanup = None
            cleanup_run = client.app.state.container.retention_lifecycle_service.run_cleanup_once
            import asyncio
            cleanup = asyncio.run(cleanup_run(now=expired_record.evidence_expires_at))
            lifecycle_health = asyncio.run(client.app.state.container.retention_lifecycle_service.health_status())
            ledger_after_cleanup = client.get(
                "/v1/admin/usage/ledger?tenant_id=default&limit=10",
                headers=admin_headers(),
            )
            expired_after_cleanup = client.get(
                f"/v1/admin/usage/ledger?request_id={expired_request_id}",
                headers=admin_headers(),
            )
            surviving_after_cleanup = client.get(
                f"/v1/admin/usage/ledger?request_id={surviving_request_id}",
                headers=admin_headers(),
            )
            no_expiration_after_cleanup = client.get(
                "/v1/admin/usage/ledger?request_id=no-expiration-marker",
                headers=admin_headers(),
            )
            second_cleanup = store.delete_expired_usage_records(now=expired_record.evidence_expires_at)

    assert expired_response.status_code == 200
    assert surviving_response.status_code == 200
    assert expired_before_cleanup.status_code == 200
    assert surviving_before_cleanup.status_code == 200
    assert no_expiration_before_cleanup.status_code == 200

    expired_row = expired_before_cleanup.json()[0]
    surviving_row = surviving_before_cleanup.json()[0]
    no_expiration_row = no_expiration_before_cleanup.json()[0]

    assert expired_row["request_id"] == expired_request_id
    assert expired_row["evidence_retention_window"] == "24h"
    assert expired_row["metadata_minimization_level"] == "strict"
    assert expired_row["metadata_fields_suppressed"] == ["route_signals"]
    assert expired_row["route_signals"] is None
    assert expired_row["governance_source"] == "tenant_policy"
    assert expired_row["evidence_expires_at"] is not None

    assert surviving_row["request_id"] == surviving_request_id
    assert surviving_row["evidence_retention_window"] == "90d"
    assert surviving_row["metadata_minimization_level"] == "standard"
    assert surviving_row["metadata_fields_suppressed"] == []
    assert surviving_row["route_signals"] is not None
    assert surviving_row["governance_source"] == "tenant_policy"
    assert surviving_row["evidence_expires_at"] is not None

    assert no_expiration_row["request_id"] == "no-expiration-marker"
    assert no_expiration_row["evidence_expires_at"] is None
    assert no_expiration_row["governance_source"] == "tenant_policy"

    assert cleanup["eligible_count"] == 1
    assert cleanup["deleted_count"] == 1
    assert cleanup["cutoff"].isoformat() == store._normalize_comparable_datetime(
        expired_record.evidence_expires_at
    ).isoformat()
    assert ledger_after_cleanup.status_code == 200
    ledger_request_ids = {entry["request_id"] for entry in ledger_after_cleanup.json()}
    assert expired_request_id not in ledger_request_ids
    assert surviving_request_id in ledger_request_ids
    assert "no-expiration-marker" in ledger_request_ids
    assert expired_after_cleanup.status_code == 200
    assert expired_after_cleanup.json() == []
    assert surviving_after_cleanup.status_code == 200
    assert len(surviving_after_cleanup.json()) == 1
    assert surviving_after_cleanup.json()[0]["request_id"] == surviving_request_id
    assert no_expiration_after_cleanup.status_code == 200
    assert len(no_expiration_after_cleanup.json()) == 1
    assert no_expiration_after_cleanup.json()[0]["request_id"] == "no-expiration-marker"

    assert second_cleanup["eligible_count"] == 0
    assert second_cleanup["deleted_count"] == 0
    assert second_cleanup["cutoff"].isoformat() == store._normalize_comparable_datetime(
        expired_record.evidence_expires_at
    ).isoformat()


def test_tenant_policy_crud_and_governed_ledger_rows_apply_evidence_controls() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            update_policy = client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    evidence_retention_window="7d",
                    metadata_minimization_level="strict",
                ).model_dump(mode="json"),
            )
            fetched_policy = client.get(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
            )
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
                cache_service=FakeCacheService(),
            )
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "local evidence governance"}],
                },
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert update_policy.status_code == 200
    assert fetched_policy.status_code == 200
    assert fetched_policy.json()["evidence_retention_window"] == "7d"
    assert fetched_policy.json()["metadata_minimization_level"] == "strict"
    assert response.status_code == 200
    assert ledger.status_code == 200
    row = ledger.json()[0]
    assert row["message_type"] == "chat"
    assert row["evidence_retention_window"] == "7d"
    assert row["metadata_minimization_level"] == "strict"
    assert row["metadata_fields_suppressed"] == ["route_signals"]
    assert row["route_signals"] is None
    assert row["governance_source"] == "tenant_policy"
    assert row["evidence_expires_at"] is not None


def test_admin_policy_simulation_returns_404_for_missing_tenant() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/admin/tenants/missing/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy().model_dump(mode="json"),
                    "limit": 5,
                    "changed_sample_limit": 3,
                },
            )

    assert response.status_code == 404
    assert response.json() == {"detail": "Tenant not found."}


def test_admin_policy_simulation_rejects_inverted_time_windows() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy().model_dump(mode="json"),
                    "from_timestamp": "2026-01-02T00:00:00Z",
                    "to_timestamp": "2026-01-01T00:00:00Z",
                },
            )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "from_timestamp must be less than or equal to to_timestamp."
    }


def test_admin_policy_simulation_returns_summary_and_preserves_saved_policy() -> None:
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
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    routing_mode_default="auto",
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    hard_budget_limit_usd=12.5,
                    hard_budget_enforcement="deny",
                ).model_dump(mode="json"),
            )

            local_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "hello local route"}],
                },
            )
            premium_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "premium route"}],
                },
            )
            degraded_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Need a deliberately complex architecture analysis "
                            "covering orchestrator routing safeguards, fallback tradeoffs, "
                            "tenant governance, replay visibility, policy simulation parity, "
                            "observability seams, and premium escalation handling.",
                        }
                    ],
                },
            )
            local_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={local_response.headers['X-Request-ID']}",
                headers=admin_headers(),
            )
            premium_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={premium_response.headers['X-Request-ID']}",
                headers=admin_headers(),
            )
            degraded_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={degraded_response.headers['X-Request-ID']}",
                headers=admin_headers(),
            )
            ledger = client.get(
                "/v1/admin/usage/ledger?tenant_id=default&limit=10",
                headers=admin_headers(),
            )
            earliest_timestamp = ledger.json()[-1]["timestamp"]
            degraded_request_id = degraded_response.headers["X-Request-ID"]
            store = app.state.container.governance_store
            degraded_record = store.list_usage_records(request_id=degraded_request_id)[0]
            store.record_usage(
                degraded_record.model_copy(
                    update={
                        "request_id": f"{degraded_request_id}-suppressed",
                        "route_signals": None,
                        "metadata_fields_suppressed": ["route_signals"],
                    }
                )
            )

            simulation = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy(
                        routing_mode_default="premium_only",
                        allowed_premium_models=["openai/gpt-4o-mini"],
                    ).model_dump(mode="json"),
                    "from_timestamp": earliest_timestamp,
                    "limit": 10,
                    "changed_sample_limit": 10,
                },
            )
            persisted_policy = client.get(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
            )

    assert local_response.status_code == 200
    assert premium_response.status_code == 200
    assert degraded_response.status_code == 200
    assert local_ledger.status_code == 200
    assert premium_ledger.status_code == 200
    assert degraded_ledger.status_code == 200
    assert simulation.status_code == 200
    body = simulation.json()
    assert body["tenant_id"] == "default"
    assert body["summary"]["evaluated_rows"] == 4
    assert body["summary"]["changed_routes"] == 1
    assert body["summary"]["newly_denied"] == 0
    assert body["calibration_summary"]["tenant_id"] == "default"
    assert body["calibration_summary"]["scope"] == "tenant_window"
    # Payloads keep calibration_summary for compatibility, but the state carries outcome-evidence semantics.
    assert body["calibration_summary"]["state"] == "thin"
    assert body["calibration_summary"]["state_reason"] == (
        "Eligible calibrated routing evidence is still below the tenant sufficiency threshold."
    )
    assert body["calibration_summary"]["eligible_request_count"] == 3
    assert body["calibration_summary"]["sufficient_request_count"] == 2
    assert body["calibration_summary"]["excluded_request_count"] == 1
    assert body["calibration_summary"]["gated_request_count"] == 0
    assert body["calibration_summary"]["degraded_request_count"] == 1
    assert body["calibration_summary"]["thin_request_threshold"] == 5
    assert body["calibration_summary"]["excluded_reasons"] == [
        {"reason": "explicit_model_override", "count": 1}
    ]
    assert body["calibration_summary"]["gated_reasons"] == []
    assert body["calibration_summary"]["degraded_reasons"] == [
        {"reason": "missing_route_signals", "count": 1},
    ]
    assert len(body["changed_requests"]) == 4

    local_row = local_ledger.json()[0]
    premium_row = premium_ledger.json()[0]
    degraded_row = degraded_ledger.json()[0]
    suppressed_change = next(
        item
        for item in body["changed_requests"]
        if item["request_id"] == f"{degraded_request_id}-suppressed"
    )
    local_change = next(
        item for item in body["changed_requests"] if item["request_id"] == local_row["request_id"]
    )
    premium_cost_change = next(
        item for item in body["changed_requests"] if item["request_id"] == premium_row["request_id"]
    )
    degraded_change = next(
        item for item in body["changed_requests"] if item["request_id"] == degraded_row["request_id"]
    )

    assert local_row["route_reason"] == local_response.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert local_row["route_signals"]["route_mode"] == local_response.headers["X-Nebula-Route-Mode"] == "calibrated"
    assert local_change["baseline_route_target"] == local_response.headers["X-Nebula-Route-Target"] == "local"
    assert local_change["baseline_route_reason"] == local_row["route_reason"]
    assert local_change["baseline_route_mode"] == local_row["route_signals"]["route_mode"]
    assert local_change["baseline_calibrated_routing"] == local_row["route_signals"]["calibrated_routing"] is True
    assert local_change["baseline_degraded_routing"] == local_row["route_signals"]["degraded_routing"] is False
    assert local_change["baseline_route_score"] == float(local_response.headers["X-Nebula-Route-Score"])
    assert local_change["baseline_route_score"] == local_row["route_signals"]["score_components"]["total_score"]
    assert local_change["simulated_route_target"] == "premium"
    assert local_change["simulated_route_reason"] == "policy_premium_only"
    assert local_change["simulated_route_mode"] is None
    assert local_change["simulated_calibrated_routing"] is None
    assert local_change["simulated_degraded_routing"] is None
    assert local_change["simulated_route_score"] is None

    assert premium_row["route_reason"] == premium_response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert premium_response.headers.get("X-Nebula-Route-Mode") is None
    assert premium_row["route_signals"] is None
    assert premium_cost_change["baseline_route_target"] == premium_response.headers["X-Nebula-Route-Target"] == "premium"
    assert premium_cost_change["baseline_route_reason"] == premium_row["route_reason"]
    assert premium_cost_change["baseline_route_mode"] is None
    assert premium_cost_change["baseline_calibrated_routing"] is None
    assert premium_cost_change["baseline_degraded_routing"] is None
    assert premium_cost_change["baseline_route_score"] is None
    assert premium_cost_change["simulated_route_target"] == "premium"
    assert premium_cost_change["simulated_route_reason"] == "explicit_premium_model"
    assert premium_cost_change["baseline_policy_outcome"] != premium_cost_change["simulated_policy_outcome"]
    assert premium_cost_change["simulated_policy_outcome"].startswith("routing_mode=premium_only")

    assert degraded_row["route_reason"] == degraded_response.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert degraded_row["route_signals"]["route_mode"] == degraded_response.headers["X-Nebula-Route-Mode"] == "calibrated"
    assert degraded_change["baseline_route_target"] == degraded_response.headers["X-Nebula-Route-Target"] == "premium"
    assert degraded_change["baseline_route_reason"] == degraded_row["route_reason"]
    assert degraded_change["baseline_route_mode"] == degraded_row["route_signals"]["route_mode"]
    assert degraded_change["baseline_calibrated_routing"] == degraded_row["route_signals"]["calibrated_routing"] is True
    assert degraded_change["baseline_degraded_routing"] == degraded_row["route_signals"]["degraded_routing"] is False
    assert degraded_change["baseline_route_score"] == float(degraded_response.headers["X-Nebula-Route-Score"])
    assert degraded_change["baseline_route_score"] == degraded_row["route_signals"]["score_components"]["total_score"]
    assert degraded_change["simulated_route_target"] == "premium"
    assert degraded_change["simulated_route_reason"] == "policy_premium_only"
    assert degraded_change["simulated_route_mode"] is None
    assert degraded_change["simulated_calibrated_routing"] is None
    assert degraded_change["simulated_degraded_routing"] is None
    assert degraded_change["simulated_route_score"] is None

    assert suppressed_change["baseline_route_target"] == "premium"
    assert suppressed_change["simulated_route_target"] == "premium"
    assert suppressed_change["baseline_route_reason"] == degraded_row["route_reason"]
    assert suppressed_change["baseline_policy_outcome"] == degraded_row["policy_outcome"]
    assert suppressed_change["baseline_route_mode"] is None
    assert suppressed_change["baseline_calibrated_routing"] is None
    assert suppressed_change["baseline_degraded_routing"] is None
    assert suppressed_change["baseline_route_score"] is None
    assert suppressed_change["simulated_route_mode"] is None
    assert suppressed_change["simulated_calibrated_routing"] is None
    assert suppressed_change["simulated_degraded_routing"] is None
    assert suppressed_change["simulated_route_score"] is None

    assert body["window"]["requested_limit"] == 10
    assert body["window"]["returned_rows"] == 4
    assert persisted_policy.status_code == 200
    assert persisted_policy.json() == TenantPolicy(
        routing_mode_default="auto",
        allowed_premium_models=["openai/gpt-4o-mini"],
        hard_budget_limit_usd=12.5,
        hard_budget_enforcement="deny",
    ).model_dump(mode="json")


def test_admin_policy_simulation_detects_newly_denied_replays() -> None:
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
            )
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    routing_mode_default="premium_only",
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    max_premium_cost_per_request=1.0,
                ).model_dump(mode="json"),
            )
            premium_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "max_tokens": 64,
                    "messages": [{"role": "user", "content": "premium allowed baseline"}],
                },
            )

            simulation = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy(
                        routing_mode_default="premium_only",
                        allowed_premium_models=["openai/gpt-4o-mini"],
                        max_premium_cost_per_request=0.000001,
                    ).model_dump(mode="json"),
                    "limit": 10,
                    "changed_sample_limit": 10,
                },
            )

    assert premium_response.status_code == 200
    assert simulation.status_code == 200
    body = simulation.json()
    assert body["summary"]["evaluated_rows"] == 1
    assert body["summary"]["changed_routes"] == 1
    assert body["summary"]["newly_denied"] == 1
    assert body["changed_requests"][0]["baseline_terminal_status"] == "completed"
    assert body["changed_requests"][0]["simulated_terminal_status"] == "policy_denied"
    assert body["changed_requests"][0]["simulated_policy_outcome"].startswith(
        "routing_mode=premium_only;denied=Request exceeds the tenant premium spend guardrail."
    )
    assert body["changed_requests"][0]["simulated_route_target"] == "denied"


def test_admin_policy_simulation_can_disable_calibrated_routing_for_runtime_and_replay() -> None:
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
            baseline = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "analyze this architecture tradeoff"}],
                },
            )
            request_id = baseline.headers["X-Request-ID"]
            baseline_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )
            simulation = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy(
                        routing_mode_default="auto",
                        calibrated_routing_enabled=False,
                        allowed_premium_models=["openai/gpt-4o-mini"],
                    ).model_dump(mode="json"),
                    "limit": 10,
                    "changed_sample_limit": 10,
                },
            )
            updated_policy = client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    routing_mode_default="auto",
                    calibrated_routing_enabled=False,
                    allowed_premium_models=["openai/gpt-4o-mini"],
                ).model_dump(mode="json"),
            )
            gated = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "analyze this architecture tradeoff"}],
                },
            )
            gated_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={gated.headers['X-Request-ID']}",
                headers=admin_headers(),
            )

    assert baseline.status_code == 200
    assert baseline.headers["X-Request-ID"] == request_id
    assert baseline.headers["X-Nebula-Route-Target"] == "premium"
    assert baseline.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert baseline.headers["X-Nebula-Route-Mode"] == "calibrated"
    baseline_score = float(baseline.headers["X-Nebula-Route-Score"])
    assert baseline_score > 0.0

    assert baseline_ledger.status_code == 200
    baseline_rows = baseline_ledger.json()
    assert len(baseline_rows) == 1
    baseline_row = baseline_rows[0]
    assert baseline_row["request_id"] == request_id
    assert baseline_row["final_route_target"] == baseline.headers["X-Nebula-Route-Target"] == "premium"
    assert baseline_row["final_provider"] == baseline.headers["X-Nebula-Provider"] == "mock-premium"
    assert baseline_row["route_reason"] == baseline.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert baseline_row["policy_outcome"] == baseline.headers["X-Nebula-Policy-Outcome"]
    assert baseline_row["route_signals"]["route_mode"] == baseline.headers["X-Nebula-Route-Mode"] == "calibrated"
    assert baseline_row["route_signals"]["calibrated_routing"] is True
    assert baseline_row["route_signals"]["degraded_routing"] is False
    assert baseline_row["route_signals"]["score_components"]["total_score"] == baseline_score

    assert simulation.status_code == 200
    body = simulation.json()
    assert body["candidate_policy"]["calibrated_routing_enabled"] is False
    assert body["summary"]["changed_routes"] == 1
    assert body["summary"]["newly_denied"] == 0
    assert body["window"]["returned_rows"] == 1
    changed = body["changed_requests"][0]
    assert changed["request_id"] == request_id == baseline_row["request_id"]
    assert changed["baseline_route_target"] == baseline.headers["X-Nebula-Route-Target"] == baseline_row["final_route_target"] == "premium"
    assert changed["baseline_route_reason"] == baseline.headers["X-Nebula-Route-Reason"] == baseline_row["route_reason"]
    assert changed["baseline_policy_outcome"] == baseline.headers["X-Nebula-Policy-Outcome"] == baseline_row["policy_outcome"]
    assert changed["baseline_route_mode"] == baseline.headers["X-Nebula-Route-Mode"] == baseline_row["route_signals"]["route_mode"]
    assert changed["baseline_calibrated_routing"] == baseline_row["route_signals"]["calibrated_routing"] is True
    assert changed["baseline_degraded_routing"] == baseline_row["route_signals"]["degraded_routing"] is False
    assert changed["baseline_route_score"] == baseline_score
    assert changed["simulated_route_target"] == "local"
    assert changed["simulated_route_reason"] == "calibrated_routing_disabled"
    assert changed["simulated_policy_outcome"] == "calibrated_routing=disabled"
    assert changed["simulated_route_mode"] is None
    assert changed["simulated_calibrated_routing"] is None
    assert changed["simulated_degraded_routing"] is None
    assert changed["simulated_route_score"] is None

    assert updated_policy.status_code == 200
    assert updated_policy.json()["calibrated_routing_enabled"] is False

    assert gated.status_code == 200
    gated_request_id = gated.headers["X-Request-ID"]
    assert gated_request_id
    assert gated_request_id != request_id
    assert gated.headers["X-Nebula-Route-Target"] == "local"
    assert gated.headers["X-Nebula-Route-Reason"] == "calibrated_routing_disabled"
    assert gated.headers.get("X-Nebula-Route-Mode") is None
    assert gated.headers["X-Nebula-Policy-Outcome"] == "calibrated_routing=disabled"

    assert gated_ledger.status_code == 200
    gated_rows = gated_ledger.json()
    assert len(gated_rows) == 1
    gated_row = gated_rows[0]
    assert gated_row["request_id"] == gated_request_id
    assert gated_row["final_route_target"] == gated.headers["X-Nebula-Route-Target"] == "local"
    assert gated_row["final_provider"] == gated.headers["X-Nebula-Provider"] == "ollama"
    assert gated_row["route_reason"] == gated.headers["X-Nebula-Route-Reason"] == "calibrated_routing_disabled"
    assert gated_row["policy_outcome"] == gated.headers["X-Nebula-Policy-Outcome"] == "calibrated_routing=disabled"
    assert gated_row["route_signals"] is None


def test_admin_policy_simulation_supports_unchanged_and_empty_windows() -> None:
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
            )
            baseline = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "steady local request"}],
                },
            )
            unchanged = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy(
                        routing_mode_default="auto",
                        allowed_premium_models=["openai/gpt-4o-mini"],
                    ).model_dump(mode="json"),
                    "limit": 10,
                    "changed_sample_limit": 5,
                },
            )
            empty = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy().model_dump(mode="json"),
                    "from_timestamp": "2099-01-01T00:00:00Z",
                    "limit": 10,
                    "changed_sample_limit": 5,
                },
            )

    assert baseline.status_code == 200
    assert unchanged.status_code == 200
    unchanged_body = unchanged.json()
    assert unchanged_body["summary"]["evaluated_rows"] == 1
    assert unchanged_body["summary"]["changed_routes"] == 0
    assert unchanged_body["summary"]["newly_denied"] == 0
    assert unchanged_body["changed_requests"] == []
    assert empty.status_code == 200
    empty_body = empty.json()
    assert empty_body["summary"]["evaluated_rows"] == 0
    assert empty_body["summary"]["changed_routes"] == 0
    assert empty_body["summary"]["newly_denied"] == 0
    assert empty_body["window"]["returned_rows"] == 0
    assert empty_body["changed_requests"] == []


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
    assert premium_denied.json()["detail"] in denied_by_request.json()[0]["policy_outcome"]
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
    assert denied.headers["X-Nebula-Route-Target"] == "premium"
    assert denied.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert denied.headers["X-Nebula-Provider"] == "policy"
    assert ledger.status_code == 200
    assert ledger.json()[0]["request_id"] == request_id
    assert ledger.json()[0]["final_route_target"] == "denied"
    assert ledger.json()[0]["final_provider"] is None
    assert ledger.json()[0]["route_reason"] == denied.headers["X-Nebula-Route-Reason"]
    assert ledger.json()[0]["policy_outcome"].endswith(denied.json()["detail"])


def test_hard_budget_guardrail_downgrades_auto_routes_and_denies_explicit_premium_requests() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
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
            baseline = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": "baseline premium spend"}],
                },
            )
            baseline_request_id = baseline.headers["X-Request-ID"]
            baseline_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={baseline_request_id}",
                headers=admin_headers(),
            )
            baseline_cost = baseline_ledger.json()[0]["estimated_cost"]
            client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json=TenantPolicy(
                    routing_mode_default="auto",
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    hard_budget_limit_usd=max(baseline_cost / 2, 0.0000001),
                    hard_budget_enforcement="downgrade",
                ).model_dump(mode="json"),
            )
            downgraded = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "analyze this architecture tradeoff"}],
                },
            )
            denied = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "explicit premium after budget exhausted"}],
                },
            )
            denied_request_id = denied.headers["X-Request-ID"]
            denied_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={denied_request_id}",
                headers=admin_headers(),
            )

    assert downgraded.status_code == 200
    assert baseline.status_code == 200
    assert baseline_ledger.status_code == 200
    assert downgraded.json()["model"] == "llama3.2:3b"
    assert downgraded.headers["X-Nebula-Route-Target"] == "local"
    assert downgraded.headers["X-Nebula-Route-Reason"] == "hard_budget_downgrade"
    assert "hard_budget=exceeded" in downgraded.headers["X-Nebula-Policy-Outcome"]
    assert "budget_action=downgraded_to_local" in downgraded.headers["X-Nebula-Policy-Outcome"]

    assert denied.status_code == 403
    expected_limit = max(baseline_cost / 2, 0.0000001)
    expected_spent = f"{baseline_cost:.6f}".rstrip("0").rstrip(".")
    expected_limit_text = f"{expected_limit:.6f}".rstrip("0").rstrip(".")
    expected_detail = (
        "Tenant hard budget limit reached; premium routing is blocked "
        f"(spent_usd={expected_spent}, limit_usd={expected_limit_text})."
    )
    assert denied.json() == {"detail": expected_detail}
    assert denied.headers["X-Nebula-Route-Target"] == "premium"
    assert denied.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert denied_ledger.status_code == 200
    assert denied_ledger.json()[0]["final_route_target"] == "denied"
    assert denied_ledger.json()[0]["policy_outcome"].endswith(denied.json()["detail"])


def test_admin_policy_simulation_applies_hard_budget_replay_window_semantics() -> None:
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
            prior_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": "prior premium spend for replay window"}],
                },
            )
            prior_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={prior_response.headers['X-Request-ID']}",
                headers=admin_headers(),
            )
            prior_cost = prior_ledger.json()[0]["estimated_cost"]
            premium_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "analyze premium baseline replay spend architecture"}],
                },
            )
            baseline_ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={premium_response.headers['X-Request-ID']}",
                headers=admin_headers(),
            )
            ledger = client.get(
                "/v1/admin/usage/ledger?tenant_id=default&limit=10",
                headers=admin_headers(),
            )
            baseline_row = next(entry for entry in ledger.json() if entry["request_id"] == premium_response.headers["X-Request-ID"])
            simulation = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={
                    "candidate_policy": TenantPolicy(
                        hard_budget_limit_usd=max(prior_cost / 2, 0.0000001),
                        hard_budget_enforcement="downgrade",
                        allowed_premium_models=["openai/gpt-4o-mini"],
                    ).model_dump(mode="json"),
                    "from_timestamp": baseline_row["timestamp"],
                    "limit": 10,
                    "changed_sample_limit": 10,
                },
            )

    assert prior_response.status_code == 200
    assert prior_ledger.status_code == 200
    assert premium_response.status_code == 200
    assert baseline_ledger.status_code == 200
    assert simulation.status_code == 200
    body = simulation.json()
    assert body["summary"]["evaluated_rows"] == 1
    assert body["summary"]["changed_routes"] == 1
    assert body["changed_requests"][0]["baseline_route_target"] == "premium"
    assert body["changed_requests"][0]["simulated_route_target"] == "local"
    assert body["changed_requests"][0]["simulated_route_reason"] == "hard_budget_downgrade"
    assert "hard_budget=exceeded" in body["changed_requests"][0]["simulated_policy_outcome"]
