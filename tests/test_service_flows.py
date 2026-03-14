from __future__ import annotations

import pytest

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionResult, ProviderError
from nebula.services.chat_service import ChatService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouterService


class FakeCacheService:
    def __init__(self, cached_response: str | None = None) -> None:
        self.cached_response = cached_response
        self.lookup_calls: list[str] = []
        self.stored_entries: list[tuple[str, str, str]] = []

    async def lookup(self, prompt: str) -> str | None:
        self.lookup_calls.append(prompt)
        return self.cached_response

    async def store(self, prompt: str, response: str, model: str) -> None:
        self.stored_entries.append((prompt, response, model))


class FakeProvider:
    def __init__(
        self,
        name: str,
        *,
        completion_result: CompletionResult | None = None,
        completion_error: Exception | None = None,
        stream_chunks: list[CompletionChunk] | None = None,
        stream_error: Exception | None = None,
    ) -> None:
        self.name = name
        self.completion_result = completion_result
        self.completion_error = completion_error
        self.stream_chunks = stream_chunks or []
        self.stream_error = stream_error
        self.complete_calls = 0
        self.stream_calls = 0

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        self.complete_calls += 1
        if self.completion_error is not None:
            raise self.completion_error
        assert self.completion_result is not None
        return self.completion_result

    def stream_complete(self, request: ChatCompletionRequest):
        self.stream_calls += 1

        async def iterator():
            if self.stream_error is not None:
                raise self.stream_error
            for chunk in self.stream_chunks:
                yield chunk

        return iterator()

    async def close(self) -> None:
        return None


def build_service(
    *,
    cache_service: FakeCacheService | None = None,
    local_provider: FakeProvider | None = None,
    premium_provider: FakeProvider | None = None,
    settings: Settings | None = None,
) -> tuple[ChatService, FakeCacheService, FakeProvider, FakeProvider]:
    active_settings = settings or Settings()
    active_cache = cache_service or FakeCacheService()
    active_local = local_provider or FakeProvider(
        "ollama",
        completion_result=CompletionResult(
            content="local response",
            model=active_settings.local_model,
            provider="ollama",
        ),
    )
    active_premium = premium_provider or FakeProvider(
        "openai-compatible",
        completion_result=CompletionResult(
            content="premium response",
            model=active_settings.premium_model,
            provider="openai-compatible",
        ),
    )
    service = ChatService(
        settings=active_settings,
        cache_service=active_cache,
        router_service=RouterService(active_settings),
        provider_registry=ProviderRegistry(
            local_provider=active_local,
            premium_provider=active_premium,
        ),
    )
    return service, active_cache, active_local, active_premium


@pytest.mark.asyncio
async def test_create_completion_routes_complex_prompts_to_premium_provider() -> None:
    service, cache_service, local_provider, premium_provider = build_service()
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "Please review this architecture tradeoff."}],
    )

    response = await service.create_completion(request, request_id="req-premium")

    assert response.model == service.settings.premium_model
    assert response.choices[0].message.content == "premium response"
    assert local_provider.complete_calls == 0
    assert premium_provider.complete_calls == 1
    assert cache_service.stored_entries == [
        (
            "Please review this architecture tradeoff.",
            "premium response",
            service.settings.premium_model,
        )
    ]


@pytest.mark.asyncio
async def test_create_completion_falls_back_to_premium_when_local_provider_fails() -> None:
    settings = Settings()
    local_provider = FakeProvider(
        "ollama",
        completion_error=ProviderError("local provider offline"),
    )
    premium_provider = FakeProvider(
        "openai-compatible",
        completion_result=CompletionResult(
            content="fallback response",
            model=settings.premium_model,
            provider="openai-compatible",
        ),
    )
    service, cache_service, active_local, active_premium = build_service(
        local_provider=local_provider,
        premium_provider=premium_provider,
        settings=settings,
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "hello"}],
    )

    response = await service.create_completion(request, request_id="req-fallback")

    assert response.model == settings.premium_model
    assert response.choices[0].message.content == "fallback response"
    assert active_local.complete_calls == 1
    assert active_premium.complete_calls == 1
    assert cache_service.stored_entries == [("hello", "fallback response", settings.premium_model)]


@pytest.mark.asyncio
async def test_create_completion_returns_cached_response_without_calling_providers() -> None:
    cache_service = FakeCacheService(cached_response="cached response")
    service, _, local_provider, premium_provider = build_service(cache_service=cache_service)
    request = ChatCompletionRequest(
        model="nebula-auto",
        messages=[{"role": "user", "content": "hello cache"}],
    )

    response = await service.create_completion(request, request_id="req-cache")

    assert response.model == "nebula-cache"
    assert response.choices[0].message.content == "cached response"
    assert local_provider.complete_calls == 0
    assert premium_provider.complete_calls == 0


@pytest.mark.asyncio
async def test_stream_completion_falls_back_to_premium_provider() -> None:
    settings = Settings()
    local_provider = FakeProvider(
        "ollama",
        stream_error=ProviderError("local stream failed"),
    )
    premium_provider = FakeProvider(
        "openai-compatible",
        stream_chunks=[
            CompletionChunk(delta="premium ", model=settings.premium_model),
            CompletionChunk(delta="stream", model=settings.premium_model),
            CompletionChunk(delta="", model=settings.premium_model, finish_reason="stop"),
        ],
    )
    service, cache_service, active_local, active_premium = build_service(
        local_provider=local_provider,
        premium_provider=premium_provider,
        settings=settings,
    )
    request = ChatCompletionRequest(
        model="nebula-auto",
        stream=True,
        messages=[{"role": "user", "content": "short"}],
    )

    events = [event async for event in service.stream_completion(request, request_id="req-stream")]
    payload = b"".join(events)

    assert active_local.stream_calls == 1
    assert active_premium.stream_calls == 1
    assert f'"model": "{settings.premium_model}"'.encode() in payload
    assert b"premium " in payload
    assert b"stream" in payload
    assert payload.endswith(b"data: [DONE]\n\n")
    assert cache_service.stored_entries == [("short", "premium stream", settings.premium_model)]
