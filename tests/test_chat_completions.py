from fastapi.testclient import TestClient

from nebula.providers.base import CompletionChunk, CompletionResult
from tests.support import FakeCacheService, StubProvider, auth_headers, configured_app, usage


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
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Provider"] == "ollama"
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
    assert response.headers["X-Nebula-Tenant-ID"] == "default"
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Provider"] == "ollama"
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert response.headers["X-Nebula-Policy-Outcome"] == "default"
    assert b"chat.completion.chunk" in body
    assert b"[DONE]" in body
