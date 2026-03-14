from __future__ import annotations

import json

import httpx
import pytest

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
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
