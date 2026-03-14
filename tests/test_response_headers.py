from __future__ import annotations

import os
from contextlib import contextmanager
from uuid import uuid4

from fastapi.testclient import TestClient

from nebula.core.config import get_settings
from nebula.main import create_app


@contextmanager
def configured_app(**env_overrides: str):
    original_values = {key: os.environ.get(key) for key in env_overrides}
    for key, value in env_overrides.items():
        os.environ[key] = value
    get_settings.cache_clear()
    app = create_app()
    try:
        yield app
    finally:
        for key, value in original_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


def test_response_headers_cover_local_premium_cache_and_fallback() -> None:
    with configured_app(
        NEBULA_PREMIUM_PROVIDER="mock",
        NEBULA_PREMIUM_MODEL="gpt-4o-mini",
        NEBULA_SEMANTIC_CACHE_THRESHOLD="1.1",
    ) as app:
        settings = get_settings()
        with TestClient(app) as client:
            local_response = client.post(
                "/v1/chat/completions",
                json={
                    "model": settings.local_model,
                    "messages": [{"role": "user", "content": f"header-local-{uuid4().hex}"}],
                },
            )
            premium_response = client.post(
                "/v1/chat/completions",
                json={
                    "model": settings.premium_model,
                    "messages": [{"role": "user", "content": f"header-premium-{uuid4().hex}"}],
                },
            )

        assert local_response.headers["X-Nebula-Route-Target"] == "local"
        assert local_response.headers["X-Nebula-Route-Reason"] == "explicit_local_model"
        assert local_response.headers["X-Nebula-Provider"] == "ollama"
        assert local_response.headers["X-Nebula-Cache-Hit"] == "false"
        assert local_response.headers["X-Nebula-Fallback-Used"] == "false"
        assert local_response.json()["usage"]["total_tokens"] > 0

        assert premium_response.headers["X-Nebula-Route-Target"] == "premium"
        assert premium_response.headers["X-Nebula-Route-Reason"] == "explicit_premium_model"
        assert premium_response.headers["X-Nebula-Provider"] == "mock-premium"
        assert premium_response.headers["X-Nebula-Fallback-Used"] == "false"

    with configured_app(
        NEBULA_PREMIUM_PROVIDER="mock",
        NEBULA_PREMIUM_MODEL="gpt-4o-mini",
        NEBULA_SEMANTIC_CACHE_COLLECTION=f"nebula-test-cache-{uuid4().hex}",
    ) as app:
        settings = get_settings()
        unique_prompt = f"cache-sequence-{uuid4().hex}"
        with TestClient(app) as client:
            cold_response = client.post(
                "/v1/chat/completions",
                json={
                    "model": settings.default_model,
                    "messages": [{"role": "user", "content": unique_prompt}],
                },
            )
            warm_response = client.post(
                "/v1/chat/completions",
                json={
                    "model": settings.default_model,
                    "messages": [{"role": "user", "content": unique_prompt}],
                },
            )

        assert cold_response.headers["X-Nebula-Route-Target"] == "local"
        assert cold_response.headers["X-Nebula-Cache-Hit"] == "false"

        assert warm_response.headers["X-Nebula-Route-Target"] == "cache"
        assert warm_response.headers["X-Nebula-Route-Reason"] == "cache_hit"
        assert warm_response.headers["X-Nebula-Provider"] == "cache"
        assert warm_response.headers["X-Nebula-Cache-Hit"] == "true"
        assert warm_response.headers["X-Nebula-Fallback-Used"] == "false"


def test_response_headers_show_fallback_when_local_provider_is_unavailable() -> None:
    with configured_app(
        NEBULA_PREMIUM_PROVIDER="mock",
        NEBULA_PREMIUM_MODEL="gpt-4o-mini",
        NEBULA_OLLAMA_BASE_URL="http://127.0.0.1:9",
    ) as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": f"hello-fallback-{uuid4().hex}"}],
                },
            )

    assert response.status_code == 200
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Route-Reason"] == "local_provider_error_fallback"
    assert response.headers["X-Nebula-Provider"] == "mock-premium"
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "true"
