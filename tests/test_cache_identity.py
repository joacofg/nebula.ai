"""Cache entry identity through the gateway: a real SemanticCacheService over in-memory Qdrant."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
import pytest
from qdrant_client import AsyncQdrantClient

from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionResult, ProviderError
from nebula.services.semantic_cache_service import SemanticCacheService
from tests.support import FixedVectorEmbeddings, auth_headers, configured_app, usage

# Payload indexes are a no-op in local Qdrant, and the client says so on every index.
pytestmark = pytest.mark.filterwarnings("ignore:Payload indexes have no effect")


class _NumberedProvider:
    """Answers "<name> answer <n>", so a test can tell which call produced a response."""

    def __init__(self, name: str, model: str) -> None:
        self.name = name
        self.model = model
        self.requests: list[ChatCompletionRequest] = []
        self.fail = False

    def _next_answer(self, request: ChatCompletionRequest) -> str:
        self.requests.append(request)
        return f"{self.name} answer {len(self.requests)}"

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        answer = self._next_answer(request)
        if self.fail:
            raise ProviderError(f"{self.name} is down")
        return CompletionResult(content=answer, model=self.model, provider=self.name, usage=usage())

    def stream_complete(self, request: ChatCompletionRequest):
        answer = self._next_answer(request)

        async def iterator():
            if self.fail:
                raise ProviderError(f"{self.name} is down")
            yield CompletionChunk(delta=answer, model=self.model)
            yield CompletionChunk(delta="", model=self.model, finish_reason="stop")

        return iterator()

    async def close(self) -> None:
        return None


@dataclass
class _Gateway:
    client: httpx.AsyncClient
    container: object
    local: _NumberedProvider
    premium: _NumberedProvider
    # Every prompt embeds to the same vector, so only the payload filters tell entries apart.
    embeddings: FixedVectorEmbeddings

    async def chat(
        self, messages: list[dict[str, str]], *, model: str = "nebula-auto", stream: bool = False
    ) -> httpx.Response:
        response = await self.client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": model, "messages": messages, "stream": stream},
        )
        assert response.status_code == 200, response.text
        return response

    def set_policy(self, **updates: object) -> None:
        store = self.container.governance_store
        store.upsert_policy("default", store.get_policy("default").model_copy(update=updates))


@asynccontextmanager
async def _gateway() -> AsyncIterator[_Gateway]:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock", NEBULA_EMBEDDING_DIMENSIONS="3") as app:
        async with app.router.lifespan_context(app):
            container = app.state.container
            settings = container.settings
            local = _NumberedProvider("ollama", settings.local_model)
            premium = _NumberedProvider("premium", settings.premium_model)
            container.provider_registry.local_provider = local
            container.provider_registry.premium_provider = premium
            embeddings = FixedVectorEmbeddings()
            cache = SemanticCacheService(
                settings=settings,
                embeddings_service=embeddings,
                client=AsyncQdrantClient(location=":memory:"),
            )
            try:
                await cache.initialize()
                assert cache.enabled
                container.cache_service = cache
                container.chat_service.cache_service = cache
                container.chat_service.embeddings_service = embeddings
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
                    yield _Gateway(client, container, local, premium, embeddings)
            finally:
                await cache.close()


def _answer(response: httpx.Response) -> str:
    if response.headers["content-type"].startswith("text/event-stream"):
        return response.text
    return response.json()["choices"][0]["message"]["content"]


@pytest.mark.parametrize("stream", [False, True])
async def test_two_conversations_same_last_message_do_not_share_answers(stream: bool) -> None:
    with_system = [{"role": "system", "content": "Eres X"}, {"role": "user", "content": "hola"}]
    without_system = [{"role": "user", "content": "hola"}]
    async with _gateway() as gateway:
        first = await gateway.chat(with_system, stream=stream)
        other = await gateway.chat(without_system, stream=stream)
        repeat = await gateway.chat(with_system, stream=stream)

    assert "ollama answer 1" in _answer(first)
    # Same last user message, different context: the first answer must not leak across.
    assert other.headers["X-Nebula-Cache-Hit"] == "false"
    assert "ollama answer 2" in _answer(other)
    # The same conversation again does reuse its own answer.
    assert repeat.headers["X-Nebula-Cache-Hit"] == "true"
    assert "ollama answer 1" in _answer(repeat)


async def test_chat_embeds_once_per_request_with_router_off() -> None:
    async with _gateway() as gateway:
        miss = await gateway.chat([{"role": "user", "content": "hola"}])
        calls_for_the_miss = list(gateway.embeddings.calls)
        hit = await gateway.chat([{"role": "user", "content": "hola"}])

    assert miss.headers["X-Nebula-Cache-Hit"] == "false"
    # One embedding serves both the lookup and the store of the missed request...
    assert calls_for_the_miss == ["hola"]
    # ...and that store really happened: the next request hits it.
    assert hit.headers["X-Nebula-Cache-Hit"] == "true"
    assert gateway.embeddings.calls == ["hola", "hola"]


HOLA = [{"role": "user", "content": "hola"}]


@pytest.mark.parametrize("stream", [False, True])
async def test_frontier_routed_request_never_gets_a_local_answer(stream: bool) -> None:
    async with _gateway() as gateway:
        local = await gateway.chat(HOLA, stream=stream)  # a short prompt routes local
        gateway.set_policy(routing_mode_default="premium_only")
        frontier = await gateway.chat(HOLA, stream=stream)
        frontier_again = await gateway.chat(HOLA, stream=stream)

    assert local.headers["X-Nebula-Route-Tier"] == "local"
    assert frontier.headers["X-Nebula-Cache-Hit"] == "false"
    assert "premium answer 1" in _answer(frontier)
    # The frontier answer it stored serves the next frontier request.
    assert frontier_again.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(frontier_again)


async def test_explicit_model_request_gets_only_that_models_answer() -> None:
    async with _gateway() as gateway:
        frontier_model = gateway.container.settings.premium_model
        gateway.set_policy(
            routing_mode_default="premium_only",
            allowed_premium_models=[frontier_model, "other/model"],
        )
        await gateway.chat(HOLA)  # premium answer 1, by the frontier model
        other = await gateway.chat(HOLA, model="other/model")
        same = await gateway.chat(HOLA, model=frontier_model)

    # Both are frontier-tier requests, but an explicit model is not a tier.
    assert other.headers["X-Nebula-Cache-Hit"] == "false"
    assert "premium answer 2" in _answer(other)
    assert same.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(same)


@pytest.mark.parametrize("stream", [False, True])
async def test_a_fallback_answer_is_stored_under_the_tier_that_served_it(stream: bool) -> None:
    async with _gateway() as gateway:
        gateway.local.fail = True
        fallback = await gateway.chat(HOLA, stream=stream)
        gateway.set_policy(routing_mode_default="premium_only")
        frontier = await gateway.chat(HOLA, stream=stream)

    assert fallback.headers["X-Nebula-Fallback-Used"] == "true"
    assert fallback.headers["X-Nebula-Route-Tier"] == "frontier"
    # Routed local, served by frontier: good enough for a frontier request.
    assert frontier.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(frontier)
