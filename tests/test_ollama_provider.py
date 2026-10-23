from __future__ import annotations

import json

import httpx
import pytest

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import ProviderError
from nebula.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_provider_extracts_usage_from_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "llama3.2:3b",
                "message": {"content": "local ok"},
                "prompt_eval_count": 14,
                "eval_count": 9,
            },
        )

    provider = OllamaProvider(Settings())
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(
        base_url="http://localhost:11434",
        transport=httpx.MockTransport(handler),
    )

    result = await provider.complete(
        ChatCompletionRequest(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": "hello"}],
        )
    )

    assert result.usage is not None
    assert result.usage.prompt_tokens == 14
    assert result.usage.completion_tokens == 9
    assert result.usage.total_tokens == 23
    await provider.close()


def _provider_with_handler(handler) -> OllamaProvider:
    provider = OllamaProvider(Settings())
    provider.client = httpx.AsyncClient(
        base_url="http://localhost:11434",
        transport=httpx.MockTransport(handler),
    )
    return provider


def _hello_request() -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model="x",
        messages=[{"role": "user", "content": "hello"}],
    )


@pytest.mark.asyncio
async def test_http_error_keeps_upstream_status_and_body() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model 'x' not found"})

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        await provider.complete(_hello_request())

    assert "completion failed: HTTP 404: " in str(exc_info.value)
    assert "model 'x' not found" in str(exc_info.value)
    await provider.close()


def _streamed_response(status_code: int, body: bytes, **kwargs) -> httpx.Response:
    """A response whose body is still on the wire, as a real streaming upstream sends it.

    `httpx.Response(..., json=...)` is pre-read by MockTransport, which hides a missing `aread()`.
    """

    async def body_stream():
        yield body

    return httpx.Response(status_code, content=body_stream(), **kwargs)


@pytest.mark.asyncio
async def test_stream_http_error_keeps_upstream_status_and_body() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(404, b'{"error": "model \'x\' not found"}')

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        async for _ in provider.stream_complete(_hello_request()):
            pass

    assert "stream failed: HTTP 404: " in str(exc_info.value)
    assert "model 'x' not found" in str(exc_info.value)
    await provider.close()


@pytest.mark.asyncio
async def test_stream_redirect_response_is_a_provider_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(
            308,
            b"moved permanently",
            headers={"location": "http://elsewhere.example/api/chat"},
        )

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        async for _ in provider.stream_complete(_hello_request()):
            pass

    assert "stream failed: HTTP 308: moved permanently" in str(exc_info.value)
    await provider.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("done_reason", "expected"), [("length", "length"), ("load", "stop"), ("stop", "stop"), (None, "stop")]
)
async def test_ollama_maps_done_reason(done_reason, expected) -> None:
    body = {"model": "x", "message": {"content": "hi"}, "done": True}
    if done_reason is not None:
        body["done_reason"] = done_reason

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    provider = _provider_with_handler(handler)
    result = await provider.complete(_hello_request())

    assert result.finish_reason == expected
    await provider.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(("done_reason", "expected"), [("length", "length"), ("load", "stop")])
async def test_ollama_stream_final_chunk_maps_done_reason(done_reason, expected) -> None:
    lines = [
        {"model": "x", "message": {"content": "hi"}, "done": False},
        {"model": "x", "message": {"content": ""}, "done": True, "done_reason": done_reason},
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(200, ("\n".join(json.dumps(line) for line in lines)).encode())

    provider = _provider_with_handler(handler)
    chunks = [chunk async for chunk in provider.stream_complete(_hello_request())]

    assert [chunk.finish_reason for chunk in chunks] == [None, expected]
    await provider.close()
