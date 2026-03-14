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
                    {"role": "user", "content": "Hola Nebula"},
                ],
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["model"] in {"llama3.2:3b", "gpt-4o-mini", "nebula-cache"}


def test_chat_completions_streams_sse() -> None:
    with TestClient(app) as client:
        with client.stream(
            "POST",
            "/v1/chat/completions",
            json={
                "model": "nebula-auto",
                "stream": True,
                "messages": [
                    {"role": "user", "content": "Hola streaming"},
                ],
            },
        ) as response:
            body = b"".join(response.iter_bytes())

    assert response.status_code == 200
    assert b"chat.completion.chunk" in body
    assert b"[DONE]" in body
