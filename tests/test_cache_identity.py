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
    FakeCacheService,
    FixedVectorEmbeddings,
    auth_headers,
    cache_lookups,
    configured_app,
    usage,
    use_fake_cache,
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

    async def post(
        self, messages: list[dict[str, str]], *, model: str = "nebula-auto", stream: bool = False
    ) -> httpx.Response:
        return await self.client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": model, "messages": messages, "stream": stream},
        )

    async def chat(
        self, messages: list[dict[str, str]], *, model: str = "nebula-auto", stream: bool = False
    ) -> httpx.Response:
        response = await self.post(messages, model=model, stream=stream)
        assert response.status_code == 200, response.text
        return response

    def rows_of(self, response: httpx.Response) -> list:
        store = self.container.governance_store
        return store.list_usage_records(request_id=response.headers["X-Request-ID"])

    def set_policy(self, **updates: object) -> None:
        store = self.container.governance_store
        store.upsert_policy("default", store.get_policy("default").model_copy(update=updates))


class _UnavailableEmbeddings(FixedVectorEmbeddings):
    async def embed(self, text: str, *, timeout: float | None = None) -> list[float] | None:
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
    # No guardrail stood in its way.
    assert "spend_guardrail" not in row.route_signals


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


# --- A cached answer costs nothing, so spend guardrails ask the cache first (C9) ---

# Every prompt embeds to the same vector here, so only another conversation context misses.
UNCACHED = [{"role": "system", "content": "Eres X"}, {"role": "user", "content": "hola"}]


async def _cache_a_frontier_answer_then_exhaust_the_budget(
    gateway: _Gateway, *, stream: bool, enforcement: str | None = "deny"
) -> float:
    """Cache "premium answer 1" for HOLA; its cost is all the tenant's hard budget allows."""
    gateway.set_policy(routing_mode_default="premium_only")
    await gateway.chat(HOLA, stream=stream)
    spent = gateway.container.governance_store.tenant_spend_total("default")
    gateway.set_policy(hard_budget_limit_usd=spent, hard_budget_enforcement=enforcement)
    return spent


# No enforcement means deny; a downgrade cannot apply to a premium-only tenant, so it denies too.
@pytest.mark.parametrize("enforcement", ["deny", None, "downgrade"])
@pytest.mark.parametrize("stream", [False, True])
async def test_a_tenant_over_its_hard_budget_still_gets_its_cached_answer(
    stream: bool, enforcement: str | None
) -> None:
    async with _gateway() as gateway:
        spent = await _cache_a_frontier_answer_then_exhaust_the_budget(
            gateway, stream=stream, enforcement=enforcement
        )
        hit = await gateway.post(HOLA, stream=stream)
        (row,) = gateway.rows_of(hit)
        spend_after_hit = gateway.container.governance_store.tenant_spend_total("default")

    assert hit.status_code == 200, hit.text
    assert hit.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(hit)
    assert len(gateway.premium.requests) == 1
    assert row.terminal_status == "cache_hit"
    assert row.estimated_cost == 0.0
    assert spend_after_hit == spent
    # Savings served past a guardrail can be told apart from ordinary ones.
    assert row.route_signals["spend_guardrail"] == "hard_budget"
    # Operators still see the budget the answer was served over, and no denial.
    outcome = hit.headers["X-Nebula-Policy-Outcome"]
    assert "hard_budget=exceeded(limit_usd=" in outcome
    assert f"enforcement={enforcement or 'deny'})" in outcome
    assert "denied=" not in outcome
    assert row.policy_outcome == outcome


# The cached frontier answer cost USD 0.0000036 (8 + 4 provider-reported tokens at gpt-4o-mini's
# prices), or 0.00000255 streamed (1 + 4 tokens estimated from the text); both the spend and
# the limit print rounded to six decimals.
@pytest.mark.parametrize(("stream", "budget_usd"), [(False, "0.000004"), (True, "0.000003")])
async def test_a_tenant_over_its_hard_budget_without_a_cached_answer_is_denied_as_before(
    stream: bool, budget_usd: str
) -> None:
    async with _gateway() as gateway:
        await _cache_a_frontier_answer_then_exhaust_the_budget(gateway, stream=stream)
        denied = await gateway.post(UNCACHED, stream=stream)
        (row,) = gateway.rows_of(denied)

    # The exact 403 the gateway answered before the cache was consulted first.
    detail = (
        "Tenant hard budget limit reached; premium routing is blocked "
        f"(spent_usd={budget_usd}, limit_usd={budget_usd})."
    )
    outcome = (
        "routing_mode=premium_only;"
        f"hard_budget=exceeded(limit_usd={budget_usd},spent_usd={budget_usd},enforcement=deny);"
        f"denied={detail};"
        "outcome_evidence=thin(eligible=0,sufficient=0,degraded=0,gated=0,excluded=1)"
    )
    assert denied.status_code == 403
    assert denied.json() == {
        "error": {"message": detail, "type": "permission_error", "code": "policy_premium_only"},
        "detail": detail,
    }
    nebula_headers = {
        name: value for name, value in denied.headers.items() if name.startswith("x-nebula-")
    }
    assert nebula_headers == {
        "x-nebula-tenant-id": "default",
        "x-nebula-route-target": "premium",
        "x-nebula-route-reason": "policy_premium_only",
        "x-nebula-provider": "policy",
        "x-nebula-route-score": "0.0000",
        "x-nebula-cache-hit": "false",
        "x-nebula-fallback-used": "false",
        "x-nebula-policy-mode": "premium_only",
        "x-nebula-policy-outcome": outcome,
        "x-nebula-route-tier": "denied",
    }
    assert (
        row.terminal_status,
        row.final_route_target,
        row.final_provider,
        row.requested_model,
        row.response_model,
        row.cache_hit,
        row.estimated_cost,
        row.latency_ms,
        row.route_reason,
        row.policy_outcome,
        row.route_signals,
    ) == (
        "policy_denied",
        "denied",
        None,
        "nebula-auto",
        None,
        False,
        None,
        None,
        "policy_premium_only",
        outcome,
        None,
    )
    assert len(gateway.premium.requests) == 1


@pytest.mark.parametrize("stream", [False, True])
async def test_a_request_over_the_per_request_cap_still_gets_its_cached_answer(
    stream: bool,
) -> None:
    async with _gateway() as gateway:
        gateway.set_policy(routing_mode_default="premium_only")
        await gateway.chat(HOLA, stream=stream)
        gateway.set_policy(max_premium_cost_per_request=1e-9)
        hit = await gateway.post(HOLA, stream=stream)
        miss = await gateway.post(UNCACHED, stream=stream)
        (hit_row,) = gateway.rows_of(hit)
        (miss_row,) = gateway.rows_of(miss)

    assert hit.status_code == 200, hit.text
    assert hit.headers["X-Nebula-Cache-Hit"] == "true"
    assert "premium answer 1" in _answer(hit)
    assert hit_row.terminal_status == "cache_hit"
    assert "denied=" not in hit_row.policy_outcome
    assert hit_row.route_signals["spend_guardrail"] == "per_request_cap"
    # With nothing cached the cap denies, as before.
    assert miss.status_code == 403
    assert miss.json()["detail"] == "Request exceeds the tenant premium spend guardrail."
    assert miss_row.terminal_status == "policy_denied"
    assert len(gateway.premium.requests) == 1


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize(
    ("policy", "model", "detail"),
    [
        (
            {"routing_mode_default": "local_only"},
            "openai/gpt-4o",
            "Tenant policy does not allow explicit premium routing.",
        ),
        (
            {"allowed_premium_models": ["openai/gpt-4o"]},
            "other/model",
            "Premium model 'other/model' is not allowed for this tenant.",
        ),
    ],
    ids=["routing_mode", "allowlist"],
)
async def test_denials_other_than_spend_happen_before_the_cache(
    stream: bool, policy: dict[str, object], model: str, detail: str
) -> None:
    async with _gateway() as gateway:
        cache = use_fake_cache(gateway.container, FakeCacheService("cached answer"))
        gateway.set_policy(**policy)
        denied = await gateway.post(HOLA, model=model, stream=stream)
        (row,) = gateway.rows_of(denied)

    assert denied.status_code == 403
    assert denied.json()["detail"] == detail
    assert row.terminal_status == "policy_denied"
    # A cache that would have answered is never asked.
    assert cache.lookup_calls == []


def _turn_the_tenant_cache_off(gateway: _Gateway) -> None:
    gateway.set_policy(semantic_cache_enabled=False)


def _take_embeddings_down(gateway: _Gateway) -> None:
    gateway.container.chat_service.embeddings_service = _UnavailableEmbeddings()


def _make_the_cache_lookup_raise(gateway: _Gateway) -> None:
    use_fake_cache(
        gateway.container, FakeCacheService("cached", lookup_error=RuntimeError("qdrant exploded"))
    )


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize(
    "cache_cannot_answer",
    [_turn_the_tenant_cache_off, _take_embeddings_down, _make_the_cache_lookup_raise],
    ids=["tenant_cache_off", "embeddings_down", "lookup_raises"],
)
async def test_a_spend_denial_the_cache_cannot_answer_is_the_usual_403(
    stream: bool, cache_cannot_answer
) -> None:
    async with _gateway() as gateway:
        await _cache_a_frontier_answer_then_exhaust_the_budget(gateway, stream=stream)
        cache_cannot_answer(gateway)
        # HOLA's answer is cached, but this time the cache cannot hand it out.
        denied = await gateway.post(HOLA, stream=stream)
        (row,) = gateway.rows_of(denied)

    assert denied.status_code == 403
    assert denied.json()["detail"].startswith(
        "Tenant hard budget limit reached; premium routing is blocked"
    )
    assert denied.headers["X-Nebula-Route-Reason"] == "policy_premium_only"
    assert denied.headers["X-Nebula-Route-Tier"] == "denied"
    assert "denied=Tenant hard budget limit reached" in denied.headers["X-Nebula-Policy-Outcome"]
    assert (row.terminal_status, row.final_route_target, row.route_signals) == (
        "policy_denied",
        "denied",
        None,
    )
    assert row.policy_outcome == denied.headers["X-Nebula-Policy-Outcome"]
    assert len(gateway.premium.requests) == 1


async def test_a_deferred_spend_403_carries_the_rate_limit_headers() -> None:
    async with _gateway() as gateway:
        await _cache_a_frontier_answer_then_exhaust_the_budget(gateway, stream=False)
        gateway.set_policy(rate_limit_requests_per_minute=60)
        denied = await gateway.post(UNCACHED)

    # Raised after the cache lookup, from inside the handler, it still reports the tenant's
    # remaining requests like any other response.
    assert denied.status_code == 403
    assert denied.headers["X-RateLimit-Limit"] == "60"
    assert denied.headers["X-RateLimit-Remaining"] == "59"
    assert "X-RateLimit-Reset" in denied.headers
