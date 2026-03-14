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
            premium_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "header-premium"}],
                },
            )
            container.cache_service.cached_response = "cached response"
            cache_response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "header-cache"}],
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

    assert premium_response.headers["X-Nebula-Route-Target"] == "premium"
    assert premium_response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
    assert premium_response.headers["X-Nebula-Provider"] == "mock-premium"

    assert cache_response.headers["X-Nebula-Route-Target"] == "cache"
    assert cache_response.headers["X-Nebula-Route-Reason"] == "cache_hit"
    assert cache_response.headers["X-Nebula-Provider"] == "cache"
    assert cache_response.headers["X-Nebula-Cache-Hit"] == "true"
    assert cache_response.headers["X-Nebula-Fallback-Used"] == "false"

    assert fallback_response.status_code == 200
    assert fallback_response.headers["X-Nebula-Route-Target"] == "premium"
    assert fallback_response.headers["X-Nebula-Route-Reason"] == "local_provider_error_fallback"
    assert fallback_response.headers["X-Nebula-Provider"] == "mock-premium"
    assert fallback_response.headers["X-Nebula-Cache-Hit"] == "false"
    assert fallback_response.headers["X-Nebula-Fallback-Used"] == "true"
