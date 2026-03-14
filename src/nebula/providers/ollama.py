from __future__ import annotations

import json
from typing import Any

import httpx

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest, ChatMessage
from nebula.providers.base import (
    CompletionChunk,
    CompletionProvider,
    CompletionResult,
    CompletionUsage,
    ProviderError,
)


class OllamaProvider(CompletionProvider):
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=self.settings.ollama_base_url,
            timeout=httpx.Timeout(120.0, connect=5.0),
        )

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        payload = self._build_payload(request, stream=False)
        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama completion failed: {exc}") from exc

        body = response.json()
        return CompletionResult(
            content=body.get("message", {}).get("content", ""),
            model=body.get("model", payload["model"]),
            provider=self.name,
            finish_reason="stop",
            usage=CompletionUsage(
                prompt_tokens=body.get("prompt_eval_count", 0),
                completion_tokens=body.get("eval_count", 0),
                total_tokens=body.get("prompt_eval_count", 0) + body.get("eval_count", 0),
            ),
        )

    def stream_complete(self, request: ChatCompletionRequest):
        payload = self._build_payload(request, stream=True)

        async def iterator():
            try:
                async with self.client.stream("POST", "/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        yield CompletionChunk(
                            delta=chunk.get("message", {}).get("content", ""),
                            model=chunk.get("model", payload["model"]),
                            finish_reason="stop" if chunk.get("done") else None,
                        )
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                raise ProviderError(f"Ollama stream failed: {exc}") from exc

        return iterator()

    async def close(self) -> None:
        await self.client.aclose()

    def _build_payload(self, request: ChatCompletionRequest, stream: bool) -> dict[str, Any]:
        requested_model = request.model if request.model != self.settings.default_model else None
        return {
            "model": requested_model or self.settings.local_model,
            "messages": [self._serialize_message(message) for message in request.messages],
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
            },
        }

    def _serialize_message(self, message: ChatMessage) -> dict[str, str]:
        content = message.content if isinstance(message.content, str) else json.dumps(message.content)
        return {
            "role": message.role,
            "content": content,
        }
