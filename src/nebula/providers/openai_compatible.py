from __future__ import annotations

import json
from typing import Any

import httpx

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import (
    CompletionChunk,
    CompletionProvider,
    CompletionResult,
    CompletionUsage,
    ProviderError,
)


class OpenAICompatibleProvider(CompletionProvider):
    name = "openai-compatible"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=self.settings.premium_base_url or "https://api.openai.com/v1",
            timeout=httpx.Timeout(120.0, connect=10.0),
        )

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        response = await self._post(request, stream=False)
        body = response.json()
        return CompletionResult(
            content=body["choices"][0]["message"]["content"],
            model=body.get("model", self.settings.premium_model),
            provider=self.name,
            finish_reason=body["choices"][0].get("finish_reason", "stop"),
            usage=self._extract_usage(body.get("usage")),
        )

    def stream_complete(self, request: ChatCompletionRequest):
        async def iterator():
            try:
                async with self.client.stream(
                    "POST",
                    "chat/completions",
                    json=self._build_payload(request, stream=True),
                    headers=self._headers(),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line.removeprefix("data: ").strip()
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        choice = chunk["choices"][0]
                        delta = choice.get("delta", {}).get("content", "")
                        yield CompletionChunk(
                            delta=delta,
                            model=chunk.get("model", self.settings.premium_model),
                            finish_reason=choice.get("finish_reason"),
                        )
            except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
                raise ProviderError(f"OpenAI-compatible stream failed: {exc}") from exc

        return iterator()

    async def close(self) -> None:
        await self.client.aclose()

    async def _post(self, request: ChatCompletionRequest, stream: bool) -> httpx.Response:
        try:
            response = await self.client.post(
                "chat/completions",
                json=self._build_payload(request, stream=stream),
                headers=self._headers(),
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAI-compatible completion failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.premium_api_key:
            headers["Authorization"] = f"Bearer {self.settings.premium_api_key}"
        return headers

    def _build_payload(self, request: ChatCompletionRequest, stream: bool) -> dict[str, Any]:
        requested_model = request.model if request.model != self.settings.default_model else None
        payload = {
            "model": requested_model or self.settings.premium_model,
            "messages": [message.model_dump(mode="json") for message in request.messages],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n": request.n,
            "stream": stream,
            "stop": request.stop,
            "max_tokens": request.max_tokens,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
            "user": request.user,
        }
        return {key: value for key, value in payload.items() if value is not None}

    def _extract_usage(self, usage: dict[str, Any] | None) -> CompletionUsage | None:
        if not usage:
            return None

        return CompletionUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
