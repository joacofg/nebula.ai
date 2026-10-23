from __future__ import annotations

import json

import httpx
import pytest

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionUsage, ProviderError
from nebula.providers.openai_compatible import OpenAICompatibleProvider


@pytest.mark.asyncio
async def test_openai_compatible_provider_keeps_base_path_when_calling_chat_completions() -> None:
    captured_url: str | None = None
    captured_payload: bytes | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload, captured_url
        captured_url = str(request.url)
        captured_payload = await request.aread()
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "premium ok"}, "finish_reason": "stop"}],
                "model": "openai/gpt-4o-mini",
            },
        )

    settings = Settings(
        premium_provider="openai_compatible",
        premium_base_url="https://openrouter.ai/api/v1",
        premium_api_key="test-key",
        premium_model="openai/gpt-4o-mini",
    )
    provider = OpenAICompatibleProvider(settings)
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(
        base_url=settings.premium_base_url,
        transport=httpx.MockTransport(handler),
    )

    result = await provider.complete(
        ChatCompletionRequest(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
        )
    )

    assert captured_url == "https://openrouter.ai/api/v1/chat/completions"
    assert captured_payload is not None
    parsed_payload = json.loads(captured_payload)
    assert parsed_payload["model"] == "openai/gpt-4o-mini"
    assert result.content == "premium ok"
    assert result.usage is None
    await provider.close()


def test_openai_compatible_provider_omits_none_values_from_payload() -> None:
    settings = Settings(
        premium_provider="openai_compatible",
        premium_base_url="https://openrouter.ai/api/v1",
        premium_api_key="test-key",
        premium_model="openai/gpt-4o-mini",
    )
    provider = OpenAICompatibleProvider(settings)

    payload = provider._build_payload(
        ChatCompletionRequest(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
            stop=None,
            max_tokens=None,
            user=None,
        ),
        stream=False,
    )

    assert "stop" not in payload
    assert "max_tokens" not in payload
    assert "user" not in payload


@pytest.mark.asyncio
async def test_openai_compatible_provider_extracts_usage_from_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "premium ok"}, "finish_reason": "stop"}],
                "model": "openai/gpt-4o-mini",
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                },
            },
        )

    settings = Settings(
        premium_provider="openai_compatible",
        premium_base_url="https://openrouter.ai/api/v1",
        premium_api_key="test-key",
        premium_model="openai/gpt-4o-mini",
    )
    provider = OpenAICompatibleProvider(settings)
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(
        base_url=settings.premium_base_url,
        transport=httpx.MockTransport(handler),
    )

    result = await provider.complete(
        ChatCompletionRequest(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
        )
    )

    assert result.usage is not None
    assert result.usage.prompt_tokens == 11
    assert result.usage.completion_tokens == 7
    assert result.usage.total_tokens == 18
    await provider.close()


def _provider_with_handler(handler) -> OpenAICompatibleProvider:
    settings = Settings(
        premium_provider="openai_compatible",
        premium_base_url="https://openrouter.ai/api/v1",
        premium_api_key="test-key",
        premium_model="openai/gpt-4o-mini",
    )
    provider = OpenAICompatibleProvider(settings)
    provider.client = httpx.AsyncClient(
        base_url=settings.premium_base_url,
        transport=httpx.MockTransport(handler),
    )
    return provider


def _hello_request() -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "hello"}],
    )


@pytest.mark.asyncio
async def test_null_content_is_an_empty_answer() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": None}, "finish_reason": "length"}],
                "model": "openai/gpt-4o-mini",
                "usage": {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16},
            },
        )

    provider = _provider_with_handler(handler)

    result = await provider.complete(_hello_request())

    assert result.content == ""
    assert result.finish_reason == "length"
    assert result.usage is not None
    assert result.usage.total_tokens == 16
    await provider.close()


@pytest.mark.asyncio
async def test_http_error_keeps_upstream_status_and_body() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"error": {"message": "Insufficient credits"}})

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        await provider.complete(_hello_request())

    assert "completion failed: HTTP 402: " in str(exc_info.value)
    assert "Insufficient credits" in str(exc_info.value)
    await provider.close()


@pytest.mark.asyncio
async def test_http_error_body_is_truncated() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="a" * 300 + "b" * 1700)

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        await provider.complete(_hello_request())

    _, body_part = str(exc_info.value).split("HTTP 500: ", 1)
    assert body_part == "a" * 300
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
        return _streamed_response(429, b'{"error": {"message": "Rate limit exceeded"}}')

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        async for _ in provider.stream_complete(_hello_request()):
            pass

    assert "stream failed: HTTP 429: " in str(exc_info.value)
    assert "Rate limit exceeded" in str(exc_info.value)
    await provider.close()


@pytest.mark.asyncio
async def test_stream_redirect_response_is_a_provider_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(
            308,
            b"moved permanently",
            headers={"location": "https://elsewhere.example/api/v1/chat/completions"},
        )

    provider = _provider_with_handler(handler)

    with pytest.raises(ProviderError) as exc_info:
        async for _ in provider.stream_complete(_hello_request()):
            pass

    assert "stream failed: HTTP 308: moved permanently" in str(exc_info.value)
    await provider.close()


@pytest.mark.asyncio
async def test_stream_null_delta_content_is_an_empty_delta() -> None:
    sse_body = (
        b'data: {"choices":[{"delta":{"role":"assistant","content":null},"finish_reason":null}]}\n\n'
        b'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
        b'data: {"choices":[{"delta":{"content":null},"finish_reason":"length"}]}\n\n'
        b"data: [DONE]\n\n"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(200, sse_body, headers={"content-type": "text/event-stream"})

    provider = _provider_with_handler(handler)

    chunks = [chunk async for chunk in provider.stream_complete(_hello_request())]

    assert [chunk.delta for chunk in chunks] == ["", "hi", ""]
    assert chunks[-1].finish_reason == "length"
    await provider.close()


def test_stream_payload_requests_usage() -> None:
    provider = _provider_with_handler(lambda request: None)
    request = _hello_request()

    assert provider._build_payload(request, stream=True)["stream_options"] == {
        "include_usage": True
    }
    assert "stream_options" not in provider._build_payload(request, stream=False)


@pytest.mark.asyncio
async def test_stream_parses_usage_only_chunk() -> None:
    sse_body = (
        b'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
        b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
        b'data: {"choices":[],"usage":{"prompt_tokens":11,"completion_tokens":7,'
        b'"total_tokens":18}}\n\n'
        b"data: [DONE]\n\n"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(200, sse_body, headers={"content-type": "text/event-stream"})

    provider = _provider_with_handler(handler)

    chunks = [chunk async for chunk in provider.stream_complete(_hello_request())]

    assert [chunk.delta for chunk in chunks] == ["hi", "", ""]
    assert chunks[1].finish_reason == "stop"
    assert chunks[-1].finish_reason is None
    assert chunks[-1].usage == CompletionUsage(11, 7, 18)
    await provider.close()


@pytest.mark.asyncio
async def test_stream_parses_usage_on_finish_chunk() -> None:
    sse_body = (
        b'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
        b'data: {"choices":[{"delta":{},"finish_reason":"stop"}],'
        b'"usage":{"prompt_tokens":11,"completion_tokens":7,"total_tokens":18}}\n\n'
        b"data: [DONE]\n\n"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return _streamed_response(200, sse_body, headers={"content-type": "text/event-stream"})

    provider = _provider_with_handler(handler)

    chunks = [chunk async for chunk in provider.stream_complete(_hello_request())]

    assert chunks[-1].finish_reason == "stop"
    assert chunks[-1].usage == CompletionUsage(11, 7, 18)
    assert chunks[0].usage is None
    await provider.close()


def test_payload_does_not_forward_n() -> None:
    provider = _provider_with_handler(lambda request: None)

    payload = provider._build_payload(
        ChatCompletionRequest(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
            n=1,
        ),
        stream=False,
    )

    assert "n" not in payload
