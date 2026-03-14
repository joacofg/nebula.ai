from __future__ import annotations

import httpx
import pytest

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
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
