from fastapi.testclient import TestClient

from nebula.main import app


def test_chat_completions_returns_openai_like_payload() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat/completions",
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
    assert body["model"] in {"llama3.2:3b", "gpt-4o-mini", "openai/gpt-4o-mini", "nebula-cache"}
    assert response.headers["X-Nebula-Route-Target"] in {"local", "premium", "cache"}
    assert response.headers["X-Nebula-Provider"] in {"ollama", "openai-compatible", "cache"}
    assert response.headers["X-Nebula-Cache-Hit"] in {"true", "false"}
    assert response.headers["X-Nebula-Fallback-Used"] in {"true", "false"}
    assert body["usage"]["prompt_tokens"] >= 0
    assert body["usage"]["completion_tokens"] >= 0


def test_chat_completions_streams_sse() -> None:
    with TestClient(app) as client:
        with client.stream(
            "POST",
            "/v1/chat/completions",
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
    assert response.headers["X-Nebula-Route-Target"] in {"local", "premium", "cache"}
    assert response.headers["X-Nebula-Provider"] in {"ollama", "openai-compatible", "cache"}
    assert response.headers["X-Nebula-Cache-Hit"] in {"true", "false"}
    assert response.headers["X-Nebula-Fallback-Used"] in {"true", "false"}
    assert b"chat.completion.chunk" in body
    assert b"[DONE]" in body
