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
from tests.support import (
    FixedVectorEmbeddings,
    auth_headers,
    cache_lookups,
    configured_app,
    usage,
)

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


class _UnavailableEmbeddings(FixedVectorEmbeddings):
    async def embed(self, text: str) -> list[float] | None:
        self.calls.append(text)
        return None  # what OllamaEmbeddingsService.embed returns when Ollama fails


@asynccontextmanager
async def _gateway(
    embeddings: FixedVectorEmbeddings | None = None, **env: str
) -> AsyncIterator[_Gateway]:
    with configured_app(
        NEBULA_PREMIUM_PROVIDER="mock", NEBULA_EMBEDDING_DIMENSIONS="3", **env
    ) as app:
        async with app.router.lifespan_context(app):
            container = app.state.container
            settings = container.settings
            local = _NumberedProvider("ollama", settings.local_model)
            premium = _NumberedProvider("premium", settings.premium_model)
            container.provider_registry.local_provider = local
            container.provider_registry.premium_provider = premium
            # The cache and the chat path share one embeddings service, as in the container.
            embeddings = embeddings or FixedVectorEmbeddings()
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


async def test_a_failed_cache_embedding_skips_the_cache_with_the_router_off() -> None:
    embeddings = _UnavailableEmbeddings()
    async with _gateway(embeddings) as gateway:
        before = cache_lookups("embedding_unavailable")
        first = await gateway.chat([{"role": "user", "content": "hola"}])
        counted = cache_lookups("embedding_unavailable") - before
        second = await gateway.chat([{"role": "user", "content": "hola"}])

    # One attempt per request: the cache never retries the embedding on its own...
    assert embeddings.calls == ["hola", "hola"]
    assert counted == 1
    # ...and with no vector nothing was stored, so the provider answers again.
    assert first.headers["X-Nebula-Cache-Hit"] == "false"
    assert second.headers["X-Nebula-Cache-Hit"] == "false"
    assert "ollama answer 2" in _answer(second)


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

    # A frontier answer is not an answer from the model the request names.
    assert other.headers["X-Nebula-Cache-Hit"] == "false"
    assert "premium answer 2" in _answer(other)
    # Asking for the frontier model by name gets its answer, not the other model's.
    assert same.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(same)


async def test_an_explicit_other_model_answer_never_serves_an_auto_request() -> None:
    async with _gateway() as gateway:
        frontier_model = gateway.container.settings.premium_model
        gateway.set_policy(allowed_premium_models=[frontier_model, "other/model"])
        await gateway.chat(HOLA, model="other/model")  # premium answer 1, by a model in no tier
        local = await gateway.chat(HOLA)  # a short prompt routes local
        gateway.set_policy(routing_mode_default="premium_only")
        frontier = await gateway.chat(HOLA)
        again = await gateway.chat(HOLA, model="other/model")

    # Its answer ranks below every tier: not even a local request may take it...
    assert local.headers["X-Nebula-Route-Tier"] == "local"
    assert local.headers["X-Nebula-Cache-Hit"] == "false"
    assert "ollama answer 1" in _answer(local)
    # ...nor a frontier one (which the local answer cannot serve either)...
    assert frontier.headers["X-Nebula-Cache-Hit"] == "false"
    assert "premium answer 2" in _answer(frontier)
    # ...only another request for that same model.
    assert again.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(again)


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


def _hit_rows(gateway: _Gateway) -> list:
    store = gateway.container.governance_store
    return [row for row in store.list_usage_records(tenant_id="default") if row.cache_hit]


@pytest.mark.parametrize("stream", [False, True])
async def test_a_frontier_hit_records_the_cost_it_avoided_without_spending_it(stream: bool) -> None:
    async with _gateway() as gateway:
        gateway.set_policy(routing_mode_default="premium_only")
        await gateway.chat(HOLA, stream=stream)
        store = gateway.container.governance_store
        spend_before_hit = store.tenant_spend_total("default")
        hit = await gateway.chat(HOLA, stream=stream)
        spend_after_hit = store.tenant_spend_total("default")
        (row,) = _hit_rows(gateway)

    assert hit.headers["X-Nebula-Cache-Hit"] == "true"
    # What the frontier model would have charged: the prompt "hola" is 1 token and the answer
    # "premium answer 1" 4, at gpt-4o-mini's USD 0.15 / 0.60 per million tokens.
    assert row.route_signals["cache_avoided_cost_usd"] == pytest.approx(1 * 0.15e-6 + 4 * 0.6e-6)
    # The hit itself costs nothing: spend and the hard budget see no change.
    assert row.estimated_cost == 0.0
    assert spend_before_hit > 0
    assert spend_after_hit == spend_before_hit


@pytest.mark.parametrize("stream", [False, True])
async def test_a_local_hit_avoids_no_cost(stream: bool) -> None:
    # A local model with a catalog price: pricing it would avoid more than 0, so only the
    # local route itself keeps the avoided cost at 0.
    async with _gateway(NEBULA_LOCAL_MODEL="openai/gpt-4o") as gateway:
        await gateway.chat(HOLA, stream=stream)  # a short prompt routes local
        hit = await gateway.chat(HOLA, stream=stream)
        (row,) = _hit_rows(gateway)

    assert hit.headers["X-Nebula-Route-Tier"] == "cache"
    assert row.route_signals["cache_avoided_cost_usd"] == 0.0
    assert row.estimated_cost == 0.0


async def test_the_avoided_cost_is_priced_at_the_model_the_request_would_have_used() -> None:
    async with _gateway() as gateway:
        gateway.set_policy(allowed_premium_models=["openai/gpt-4o", "other/model"])
        await gateway.chat(HOLA, model="openai/gpt-4o")
        await gateway.chat(HOLA, model="openai/gpt-4o")
        await gateway.chat(HOLA, model="other/model")
        await gateway.chat(HOLA, model="other/model")
        hits = {row.requested_model: row for row in _hit_rows(gateway)}

    # An explicit model is priced as itself, not as the configured frontier model.
    assert hits["openai/gpt-4o"].route_signals["cache_avoided_cost_usd"] == pytest.approx(
        1 * 2.5e-6 + 4 * 10.0e-6
    )
    # A model with no price in the catalog avoids 0, never an error or a guess.
    assert hits["other/model"].route_signals["cache_avoided_cost_usd"] == 0.0
