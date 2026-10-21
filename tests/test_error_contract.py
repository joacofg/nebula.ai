"""Errors on the OpenAI-facing routes look like OpenAI's and keep every header; admin routes do not change."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from nebula.api.dependencies import get_embeddings_service
from nebula.models.governance import TenantPolicy
from nebula.services.embeddings_service import EmbeddingsUpstreamError
from tests.support import admin_headers, auth_headers, configured_app
from tests.test_embeddings_api import StubEmbeddingsResult, StubEmbeddingsService
from tests.test_fallback_guardrails import fallback_client

CHAT = "/v1/chat/completions"
EMBEDDINGS = "/v1/embeddings"
VALID_CHAT = {"model": "nebula-auto", "messages": [{"role": "user", "content": "hi"}]}
VALID_EMBEDDINGS = {"model": "nomic-embed-text", "input": "hola"}


def test_a_missing_key_on_chat_is_an_openai_authentication_error() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(CHAT, json=VALID_CHAT)

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "message": "Missing client API key.",
            "type": "authentication_error",
            "code": None,
        },
        "detail": "Missing client API key.",
    }
    assert response.headers["X-Request-ID"]


def _set_policy(app, **updates: object) -> None:
    store = app.state.container.governance_store
    policy = store.get_policy("default")
    # Validated, unlike model_copy(update=...), so a mistyped field name fails loudly.
    store.upsert_policy("default", TenantPolicy.model_validate({**policy.model_dump(), **updates}))


def test_a_policy_denial_keeps_the_rate_limit_headers_and_names_the_route_reason() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _set_policy(app, rate_limit_requests_per_minute=10, routing_mode_default="local_only")
            response = client.post(
                CHAT,
                headers=auth_headers(),
                json={**VALID_CHAT, "model": "openai/gpt-4o-mini"},
            )

    body = response.json()
    assert response.status_code == 403
    assert response.headers["X-RateLimit-Limit"] == "10"
    assert response.headers["X-RateLimit-Remaining"] == "9"
    assert response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert body["error"]["type"] == "permission_error"
    assert body["error"]["code"] == response.headers["X-Nebula-Route-Reason"]
    assert body["error"]["message"] == body["detail"]


@pytest.mark.parametrize(
    ("path", "invalid_body"),
    [(CHAT, {"messages": []}), (EMBEDDINGS, {"input": []})],
    ids=["chat", "embeddings"],
)
def test_a_validation_failure_is_an_invalid_request_error_that_keeps_the_detail_list(
    path: str, invalid_body: dict
) -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(path, headers=auth_headers(), json=invalid_body)

    body = response.json()
    assert response.status_code == 422
    assert body["error"]["type"] == "invalid_request_error"
    assert body["error"]["code"] is None
    assert "messages" in body["error"]["message"] or "input" in body["error"]["message"]
    # Existing clients index into the FastAPI error list, so `detail` stays that list.
    assert isinstance(body["detail"], list) and body["detail"][0]["loc"][0] == "body"


def test_a_provider_failure_keeps_the_rate_limit_and_route_headers() -> None:
    with fallback_client(rate_limit_requests_per_minute=10, fallback_enabled=False) as (
        client,
        _container,
        _premium,
    ):
        response = client.post(CHAT, headers=auth_headers(), json=VALID_CHAT)

    body = response.json()
    assert response.status_code == 502
    assert response.headers["X-RateLimit-Limit"] == "10"
    assert response.headers["X-Nebula-Route-Tier"]
    assert body["error"]["type"] == "api_error"
    assert body["error"]["code"] == "local_provider_error_fallback_blocked"
    assert body["error"]["code"] == response.headers["X-Nebula-Route-Reason"]


def test_the_429_is_a_rate_limit_error_with_each_header_once() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            _set_policy(app, rate_limit_requests_per_minute=1, semantic_cache_enabled=False)
            client.post(CHAT, headers=auth_headers(), json=VALID_CHAT)
            response = client.post(CHAT, headers=auth_headers(), json=VALID_CHAT)

    body = response.json()
    assert response.status_code == 429
    assert body["error"] == {
        "message": "Tenant rate limit of 1 requests per minute exceeded.",
        "type": "rate_limit_error",
        "code": "rate_limited",
    }
    assert body["detail"] == body["error"]["message"]
    # A header merged twice would read "1, 1".
    assert response.headers["X-RateLimit-Limit"] == "1"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert int(response.headers["Retry-After"]) >= 1


def test_a_rate_limited_tenant_gets_the_headers_on_embeddings_successes_and_failures() -> None:
    with configured_app() as app:
        app.dependency_overrides[get_embeddings_service] = lambda: StubEmbeddingsService(
            result=StubEmbeddingsResult(model="nomic-embed-text", vectors=[[0.1, 0.2]])
        )
        with TestClient(app) as client:
            _set_policy(app, rate_limit_requests_per_minute=10)
            ok = client.post(EMBEDDINGS, headers=auth_headers(), json=VALID_EMBEDDINGS)
            app.dependency_overrides[get_embeddings_service] = lambda: StubEmbeddingsService(
                error=EmbeddingsUpstreamError("Ollama embeddings request failed.")
            )
            failed = client.post(EMBEDDINGS, headers=auth_headers(), json=VALID_EMBEDDINGS)

    assert ok.status_code == 200
    assert ok.headers["X-RateLimit-Limit"] == "10"
    assert failed.status_code == 502
    assert failed.headers["X-RateLimit-Limit"] == "10"
    assert failed.headers["X-RateLimit-Remaining"] == "8"
    assert failed.json() == {
        "error": {"message": "Ollama embeddings request failed.", "type": "api_error", "code": None},
        "detail": "Ollama embeddings request failed.",
    }


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [
        (400, "invalid_request_error"),
        (401, "authentication_error"),
        (403, "permission_error"),
        (404, "not_found_error"),
        (409, "conflict_error"),
        (422, "invalid_request_error"),
        (429, "rate_limit_error"),
        (500, "api_error"),
        (502, "api_error"),
        (503, "api_error"),
    ],
)
def test_the_error_type_follows_the_status(status_code: int, error_type: str) -> None:
    def failing_service():
        raise HTTPException(
            status_code=status_code,
            detail="boom",
            headers={"X-Nebula-Route-Reason": "some_reason"},
        )

    with configured_app() as app:
        app.dependency_overrides[get_embeddings_service] = failing_service
        with TestClient(app) as client:
            response = client.post(EMBEDDINGS, headers=auth_headers(), json=VALID_EMBEDDINGS)

    assert response.status_code == status_code
    assert response.json() == {
        "error": {"message": "boom", "type": error_type, "code": "some_reason"},
        "detail": "boom",
    }
    assert response.headers["X-Nebula-Route-Reason"] == "some_reason"


def test_admin_routes_keep_the_default_detail_body() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            missing = client.get("/v1/admin/tenants/missing", headers=admin_headers())
            unauthorized = client.get("/v1/admin/tenants/missing")
            invalid = client.post("/v1/admin/tenants", headers=admin_headers(), json={})
            unknown_route = client.get("/v1/not-a-route")

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Tenant not found."}
    assert unauthorized.status_code == 401
    assert unauthorized.json() == {"detail": "Missing or invalid admin API key."}
    assert invalid.status_code == 422
    assert set(invalid.json()) == {"detail"} and isinstance(invalid.json()["detail"], list)
    assert unknown_route.status_code == 404
    assert unknown_route.json() == {"detail": "Not Found"}


def test_the_api_prefix_setting_decides_which_routes_get_the_openai_shape() -> None:
    with configured_app(NEBULA_API_V1_PREFIX="/gateway/v9") as app:
        with TestClient(app) as client:
            chat = client.post("/gateway/v9/chat/completions", json=VALID_CHAT)
            embeddings = client.post("/gateway/v9/embeddings", json=VALID_EMBEDDINGS)
            admin = client.get("/gateway/v9/admin/tenants/missing", headers=admin_headers())

    assert chat.json()["error"]["type"] == "authentication_error"
    assert embeddings.json()["error"]["type"] == "authentication_error"
    assert admin.json() == {"detail": "Tenant not found."}
