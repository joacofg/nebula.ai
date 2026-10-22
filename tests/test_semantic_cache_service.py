from __future__ import annotations

from time import time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.models.openai import ChatMessage
from nebula.services.semantic_cache_service import (
    TIER_RANK,
    UNTIERED_RANK,
    CacheHit,
    SemanticCacheService,
    context_hash,
)

# Payload indexes are a no-op in local Qdrant, and the client says so on every index.
pytestmark = pytest.mark.filterwarnings("ignore:Payload indexes have no effect")


class FakeEmbeddings:
    async def embed(self, text: str) -> list[float] | None:
        return [0.1, 0.2, 0.3]


class RecordingQdrant:
    def __init__(self, points: list[object] | None = None) -> None:
        self.query_kwargs: list[dict] = []
        self.upserts: list[dict] = []
        self.indexed_fields: list[str] = []
        self.points = points or []

    async def collection_exists(self, name: str) -> bool:
        return True

    async def create_payload_index(self, **kwargs) -> None:
        self.indexed_fields.append(kwargs["field_name"])

    async def delete(self, **kwargs) -> None:
        return None

    async def query_points(self, **kwargs):
        self.query_kwargs.append(kwargs)
        return SimpleNamespace(points=self.points)

    async def upsert(self, **kwargs) -> None:
        self.upserts.append(kwargs)

    async def close(self) -> None:
        return None


def _service(
    client: RecordingQdrant, embeddings: FakeEmbeddings | None = None
) -> SemanticCacheService:
    service = SemanticCacheService(
        settings=Settings(), embeddings_service=embeddings or FakeEmbeddings(), client=client
    )
    service.enabled = True
    return service


# The identity filters of an auto request; these tests are about everything around them.
AUTO_REQUEST = {"context_hash": "ctx", "min_tier_rank": 0, "model": None}


def _must_conditions(kwargs: dict) -> dict[str, qdrant_models.FieldCondition]:
    query_filter = kwargs["query_filter"]
    assert isinstance(query_filter, qdrant_models.Filter)
    return {condition.key: condition for condition in query_filter.must}


@pytest.mark.asyncio
async def test_lookup_filters_by_tenant_and_freshness_and_uses_tenant_threshold() -> None:
    client = RecordingQdrant()
    service = _service(client)

    before = int(time())
    result = await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.93, max_entry_age_hours=2, **AUTO_REQUEST
    )

    assert result is None
    kwargs = client.query_kwargs[0]
    assert kwargs["score_threshold"] == 0.93
    conditions = _must_conditions(kwargs)
    assert conditions["tenant_id"].match.value == "acme"
    cutoff = conditions["created_at"].range.gte
    assert before - 2 * 3600 - 2 <= cutoff <= before - 2 * 3600 + 2


@pytest.mark.asyncio
async def test_lookup_returns_hit_with_score_and_age() -> None:
    created_at = int(time()) - 90
    point = SimpleNamespace(
        score=0.97,
        payload={"response": "cached", "model": "llama3.2:3b", "created_at": created_at, "tenant_id": "acme"},
    )
    service = _service(RecordingQdrant(points=[point]))

    hit = await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.9, max_entry_age_hours=24, **AUTO_REQUEST
    )

    assert isinstance(hit, CacheHit)
    assert hit.response == "cached"
    assert hit.model == "llama3.2:3b"
    assert hit.score == pytest.approx(0.97)
    assert 88 <= hit.age_seconds <= 92


@pytest.mark.asyncio
async def test_lookup_computes_age_for_a_float_created_at() -> None:
    created_at = float(int(time()) - 90)
    point = SimpleNamespace(
        score=0.97,
        payload={"response": "cached", "model": "llama3.2:3b", "created_at": created_at, "tenant_id": "acme"},
    )
    service = _service(RecordingQdrant(points=[point]))

    hit = await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.9, max_entry_age_hours=24, **AUTO_REQUEST
    )

    assert isinstance(hit, CacheHit)
    assert 88 <= hit.age_seconds <= 92


class CountingEmbeddings(FakeEmbeddings):
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def embed(self, text: str) -> list[float] | None:
        self.calls.append(text)
        return await super().embed(text)


@pytest.mark.asyncio
async def test_lookup_and_store_reuse_a_precomputed_vector() -> None:
    client = RecordingQdrant()
    embeddings = CountingEmbeddings()
    service = _service(client, embeddings)

    await service.lookup(
        "hello",
        tenant_id="acme",
        similarity_threshold=0.9,
        max_entry_age_hours=24,
        **AUTO_REQUEST,
        vector=[0.7, 0.8, 0.9],
    )
    await service.store(
        "world",
        tenant_id="acme",
        vector=[0.7, 0.8, 0.9],
        context_hash="ctx",
        tier_rank=TIER_RANK["local"],
        model="llama3.2:3b",
    )

    assert embeddings.calls == []
    assert client.query_kwargs[0]["query"] == [0.7, 0.8, 0.9]
    assert client.upserts[0]["points"][0].vector == [0.7, 0.8, 0.9]


@pytest.mark.asyncio
async def test_lookup_without_a_vector_still_embeds() -> None:
    client = RecordingQdrant()
    embeddings = CountingEmbeddings()
    service = _service(client, embeddings)

    await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.9, max_entry_age_hours=24, **AUTO_REQUEST
    )

    assert embeddings.calls == ["hello"]
    assert client.query_kwargs[0]["query"] == [0.1, 0.2, 0.3]


# --- Entry identity, against a real (in-memory) Qdrant -------------------------------------

ANY_VECTOR = [1.0, 0.0, 0.0]
EMPTY_CONTEXT = context_hash([ChatMessage(role="user", content="hola")])
# SHA-256 of the canonical empty list, "[]".
EMPTY_LIST_SHA256 = "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"


def test_context_hash_leaves_out_only_the_latest_user_message() -> None:
    def user(text: str) -> ChatMessage:
        return ChatMessage(role="user", content=text)

    # A single turn has no context.
    assert context_hash([user("hola")]) == EMPTY_LIST_SHA256
    # So two different first questions share a context; only their embeddings tell them apart.
    assert context_hash([user("hola")]) == context_hash([user("buenas")])
    # Earlier turns are context.
    earlier = [user("hola"), ChatMessage(role="assistant", content="¡Hola!")]
    follow_up = context_hash([*earlier, user("¿qué tal?")])
    assert follow_up != context_hash([user("¿qué tal?")])
    assert follow_up == context_hash([*earlier, user("¿cómo va?")])


def test_context_hash_accepts_a_lone_surrogate() -> None:
    # JSON allows "\ud800" in a request body; it decodes to a string UTF-8 cannot encode.
    messages = [
        ChatMessage(role="system", content="\ud800"),
        ChatMessage(role="user", content="hola"),
    ]

    digest = context_hash(messages)

    assert len(digest) == 64
    assert digest != EMPTY_LIST_SHA256


async def _in_memory_service() -> SemanticCacheService:
    service = SemanticCacheService(
        settings=Settings(NEBULA_EMBEDDING_DIMENSIONS=3),
        embeddings_service=FakeEmbeddings(),
        client=AsyncQdrantClient(location=":memory:"),
    )
    await service.initialize()
    assert service.enabled
    return service


async def _stored_payloads(service: SemanticCacheService) -> list[dict]:
    points, _ = await service.client.scroll(
        collection_name=service.settings.semantic_cache_collection, limit=100, with_payload=True
    )
    return [point.payload for point in points]


async def test_store_payload_has_no_raw_prompt() -> None:
    service = await _in_memory_service()

    await service.store(
        "world",
        tenant_id="acme",
        vector=ANY_VECTOR,
        context_hash=EMPTY_CONTEXT,
        tier_rank=TIER_RANK["economy"],
        model="economy-model",
    )

    [payload] = await _stored_payloads(service)
    assert set(payload) == {
        "tenant_id",
        "context_hash",
        "tier_rank",
        "model",
        "response",
        "created_at",
    }
    assert payload["tenant_id"] == "acme"
    assert payload["context_hash"] == EMPTY_CONTEXT
    assert payload["tier_rank"] == 1
    assert payload["model"] == "economy-model"
    assert payload["response"] == "world"
    assert isinstance(payload["created_at"], int)


async def _store(
    service: SemanticCacheService, response: str, *, tier: str, context: str = EMPTY_CONTEXT
) -> None:
    """Cache `response` as served on `tier` by the model "<tier>-model"."""
    await service.store(
        response,
        tenant_id="acme",
        vector=ANY_VECTOR,
        context_hash=context,
        tier_rank=TIER_RANK[tier],
        model=f"{tier}-model",
    )


async def _lookup(
    service: SemanticCacheService,
    *,
    context: str = EMPTY_CONTEXT,
    min_tier_rank: int | None = None,
    model: str | None = None,
) -> CacheHit | None:
    return await service.lookup(
        "hola",
        tenant_id="acme",
        similarity_threshold=0.9,
        max_entry_age_hours=24,
        context_hash=context,
        min_tier_rank=min_tier_rank,
        model=model,
        vector=ANY_VECTOR,
    )


async def test_lookup_requires_same_context_hash() -> None:
    with_system = context_hash(
        [ChatMessage(role="system", content="Eres X"), ChatMessage(role="user", content="hola")]
    )
    without_system = context_hash([ChatMessage(role="user", content="hola")])
    service = await _in_memory_service()
    await _store(service, "answer for X", tier="frontier", context=with_system)

    assert await _lookup(service, context=without_system, min_tier_rank=0) is None
    hit = await _lookup(service, context=with_system, min_tier_rank=0)
    assert hit is not None and hit.response == "answer for X"


async def test_frontier_request_never_gets_lower_tier_answer() -> None:
    lower_tiers = await _in_memory_service()
    await _store(lower_tiers, "local answer", tier="local")
    await _store(lower_tiers, "economy answer", tier="economy")
    assert await _lookup(lower_tiers, min_tier_rank=TIER_RANK["frontier"]) is None

    # The other direction is fine: an economy-routed request may receive a frontier answer.
    frontier = await _in_memory_service()
    await _store(frontier, "frontier answer", tier="frontier")
    hit = await _lookup(frontier, min_tier_rank=TIER_RANK["economy"])
    assert hit is not None and hit.response == "frontier answer"


async def test_explicit_model_matches_only_same_model() -> None:
    service = await _in_memory_service()
    await _store(service, "frontier answer", tier="frontier")

    # No tier rule: a frontier answer still does not serve a request for another model.
    assert await _lookup(service, model="local-model") is None
    hit = await _lookup(service, model="frontier-model")
    assert hit is not None and hit.response == "frontier answer"


@pytest.mark.parametrize(
    "scope", [{"min_tier_rank": None, "model": None}, {"min_tier_rank": 0, "model": "local-model"}]
)
async def test_lookup_needs_exactly_one_of_a_tier_or_a_model(scope: dict) -> None:
    # Neither would match every tier; both would leave the rule ambiguous.
    service = _service(RecordingQdrant())

    with pytest.raises(ValueError):
        await _lookup(service, **scope)


async def test_initialize_purges_points_without_tier_rank() -> None:
    service = await _in_memory_service()
    await _store(service, "current answer", tier="local")
    # A model outside the tiers has a rank too (below them all); it is not a legacy point.
    await service.store(
        "other model answer",
        tenant_id="acme",
        vector=ANY_VECTOR,
        context_hash=EMPTY_CONTEXT,
        tier_rank=UNTIERED_RANK,
        model="other/model",
    )
    # A point written before entries had an identity: raw prompt, no context, no tier.
    await service.client.upsert(
        collection_name=service.settings.semantic_cache_collection,
        points=[
            qdrant_models.PointStruct(
                id=str(uuid4()),
                vector=ANY_VECTOR,
                payload={
                    "tenant_id": "acme",
                    "prompt": "hola",
                    "response": "legacy answer",
                    "model": "local-model",
                    "created_at": int(time()),
                },
            )
        ],
    )

    await service.initialize()  # the next gateway start

    assert service.enabled
    remaining = [payload["response"] for payload in await _stored_payloads(service)]
    assert sorted(remaining) == ["current answer", "other model answer"]


async def test_initialize_indexes_every_field_a_lookup_filters_on() -> None:
    # Local Qdrant ignores payload indexes, so this is checked at the client boundary.
    client = RecordingQdrant()
    service = SemanticCacheService(
        settings=Settings(), embeddings_service=FakeEmbeddings(), client=client
    )

    await service.initialize()

    indexed = sorted(client.indexed_fields)
    assert indexed == ["context_hash", "created_at", "model", "tenant_id", "tier_rank"]
