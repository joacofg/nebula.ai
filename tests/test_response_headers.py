from fastapi.testclient import TestClient

from nebula.providers.base import CompletionResult
from tests.support import (
    FakeCacheService,
    StubProvider,
    auth_headers,
    configured_app,
    provider_error,
    usage,
)


def test_response_headers_cover_local_premium_cache_and_fallback() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="local response",
                    model=container.settings.local_model,
                    provider="ollama",
                    usage=usage(),
                ),
            )
            premium_provider = StubProvider(
                "mock-premium",
                completion_result=CompletionResult(
                    content="premium response",
                    model=container.settings.premium_model,
                    provider="mock-premium",
                    usage=usage(10, 6),
                ),
            )
            container.local_provider = local_provider
            container.provider_registry.local_provider = local_provider
            container.premium_provider = premium_provider
            container.provider_registry.premium_provider = premium_provider
            container.cache_service = FakeCacheService()
            container.chat_service.cache_service = container.cache_service

            local_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": container.settings.local_model,
                    "messages": [{"role": "user", "content": "header-local"}],
                },
            )
            premium_alias_denied_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "header-premium"}],
                },
            )
            cache_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "header-cache"}],
                },
            )
            container.cache_service.cached_response = "cached response"
            cache_hit_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "header-cache-hit"}],
                },
            )
            container.cache_service.cached_response = None
            local_provider.completion_error = provider_error("local down")
            fallback_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "header-fallback"}],
                },
            )

    assert local_response.headers["X-Nebula-Route-Target"] == "local"
    assert local_response.headers["X-Nebula-Route-Reason"] == "explicit_local_model"
    assert local_response.headers["X-Nebula-Provider"] == "ollama"
    assert local_response.headers["X-Nebula-Tenant-ID"] == "default"
    assert local_response.headers["X-Nebula-Cache-Hit"] == "false"
    assert local_response.headers["X-Nebula-Fallback-Used"] == "false"
    assert local_response.headers["X-Nebula-Policy-Mode"] == "auto"

    assert premium_alias_denied_response.status_code == 403
    assert premium_alias_denied_response.headers["X-Nebula-Route-Target"] == "premium"
    assert premium_alias_denied_response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert premium_alias_denied_response.headers["X-Nebula-Provider"] == "policy"
    assert premium_alias_denied_response.headers["X-Nebula-Policy-Outcome"] != ""

    assert cache_response.headers["X-Nebula-Route-Target"] == "local"
    assert cache_response.headers["X-Nebula-Route-Reason"] == "simple_prompt"
    assert cache_response.headers["X-Nebula-Provider"] == "ollama"
    assert cache_response.headers["X-Nebula-Cache-Hit"] == "false"
    assert cache_response.headers["X-Nebula-Fallback-Used"] == "false"

    assert cache_hit_response.headers["X-Nebula-Route-Target"] == "cache"
    assert cache_hit_response.headers["X-Nebula-Route-Reason"] == "cache_hit"
    assert cache_hit_response.headers["X-Nebula-Provider"] == "cache"
    assert cache_hit_response.headers["X-Nebula-Cache-Hit"] == "true"
    assert cache_hit_response.headers["X-Nebula-Fallback-Used"] == "false"

    assert fallback_response.status_code == 200
    assert fallback_response.headers["X-Nebula-Route-Target"] == "premium"
    assert fallback_response.headers["X-Nebula-Route-Reason"] == "local_provider_error_fallback"
    assert fallback_response.headers["X-Nebula-Provider"] == "mock-premium"
    assert fallback_response.headers["X-Nebula-Cache-Hit"] == "false"
    assert fallback_response.headers["X-Nebula-Fallback-Used"] == "true"


def test_denied_and_fallback_blocked_paths_expose_nebula_metadata_headers() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container = app.state.container
            container.governance_store.upsert_policy(
                "default",
                container.governance_store.get_policy("default").model_copy(
                    update={
                        "routing_mode_default": "premium_only",
                        "fallback_enabled": False,
                        "allowed_premium_models": [container.settings.premium_model],
                    }
                ),
            )

            premium_denied_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4.1-mini",
                    "messages": [{"role": "user", "content": "denied premium"}],
                },
            )

            explicit_local_denied_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": container.settings.local_model,
                    "messages": [{"role": "user", "content": "denied local"}],
                },
            )

            container.governance_store.upsert_policy(
                "default",
                container.governance_store.get_policy("default").model_copy(
                    update={
                        "routing_mode_default": "auto",
                        "fallback_enabled": False,
                        "allowed_premium_models": [container.settings.premium_model],
                    }
                ),
            )
            local_provider = StubProvider("ollama", completion_error=provider_error("local down"))
            container.local_provider = local_provider
            container.provider_registry.local_provider = local_provider
            fallback_blocked_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "blocked fallback"}],
                },
            )

    assert premium_denied_response.status_code == 403
    assert premium_denied_response.json() == {
        "detail": "Premium model 'openai/gpt-4.1-mini' is not allowed for this tenant."
    }
    assert premium_denied_response.headers["X-Nebula-Route-Target"] == "premium"
    assert premium_denied_response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert premium_denied_response.headers["X-Nebula-Policy-Outcome"] != ""

    assert explicit_local_denied_response.status_code == 403
    assert explicit_local_denied_response.headers["X-Nebula-Route-Target"] == "local"
    assert explicit_local_denied_response.headers["X-Nebula-Route-Reason"] == "explicit_local_model"
    assert explicit_local_denied_response.headers["X-Nebula-Policy-Outcome"] != ""

    assert fallback_blocked_response.status_code == 502
    assert fallback_blocked_response.json() == {
        "detail": "Local provider failed and tenant policy disabled premium fallback."
    }
    assert fallback_blocked_response.headers["X-Nebula-Route-Target"] == "local"
    assert (
        fallback_blocked_response.headers["X-Nebula-Route-Reason"]
        == "local_provider_error_fallback_blocked"
    )
    assert fallback_blocked_response.headers["X-Nebula-Policy-Outcome"] != ""


def test_validation_failures_do_not_emit_nebula_route_headers() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [
                        {"role": "system", "content": "Only system context."},
                        {"role": "assistant", "content": "No user turn present."},
                    ],
                },
            )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0]["msg"] == "Value error, At least one user message is required."
    assert "X-Nebula-Route-Target" not in response.headers
    assert "X-Nebula-Policy-Outcome" not in response.headers
