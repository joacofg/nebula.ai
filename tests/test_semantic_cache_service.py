from __future__ import annotations

import logging
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
from tests.support import FakeClock, LateQdrant, cache_lookups

# Payload indexes are a no-op in local Qdrant, and the client says so on every index.
pytestmark = pytest.mark.filterwarnings("ignore:Payload indexes have no effect")


class FakeEmbeddings:
    async def embed(self, text: str, *, timeout: float | None = None) -> list[float] | None:
        return [0.1, 0.2, 0.3]


class RecordingQdrant:
    def __init__(self, points: list[object] | None = None) -> None:
        self.query_kwargs: list[dict] = []
        self.upserts: list[dict] = []
        self.indexed_fields: list[str] = []
        self.points = points or []

    async def collection_exists(self, name: str) -> bool:
        return True

    async def get_collection(self, name: str):
        vectors = qdrant_models.VectorParams(
            size=Settings().embedding_dimensions, distance=qdrant_models.Distance.COSINE
        )
        return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(vectors=vectors)))

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
async def test_lookup_filters_by_tenant_and_freshness() -> None:
    client = RecordingQdrant()
    service = _service(client)

    before = int(time())
    result = await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.93, max_entry_age_hours=2, **AUTO_REQUEST
    )

    assert result is None
    conditions = _must_conditions(client.query_kwargs[0])
    assert conditions["tenant_id"].match.value == "acme"
    cutoff = conditions["created_at"].range.gte
    assert before - 2 * 3600 - 2 <= cutoff <= before - 2 * 3600 + 2


@pytest.mark.parametrize(("score", "is_hit"), [(0.9299, False), (0.93, True), (0.97, True)])
async def test_the_tenant_threshold_applies_to_the_best_candidate(score: float, is_hit: bool) -> None:
    point = SimpleNamespace(
        score=score,
        payload={"response": "cached", "model": "m", "created_at": int(time()), "tenant_id": "acme"},
    )
    service = _service(RecordingQdrant(points=[point]))

    hit = await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.93, max_entry_age_hours=2, **AUTO_REQUEST
    )

    # A hit at threshold t: the best candidate's cosine is at least t.
    assert (hit is not None) is is_hit


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
        self.timeouts: list[float | None] = []

    async def embed(self, text: str, *, timeout: float | None = None) -> list[float] | None:
        self.calls.append(text)
        self.timeouts.append(timeout)
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
    # Offline callers (the replay) keep the embeddings client's own timeout.
    assert embeddings.timeouts == [None]


async def test_the_gateway_cache_bounds_its_own_embedding() -> None:
    # The gateway's chat path brings no vector to the first lookup after a recovery.
    embeddings = CountingEmbeddings()
    service = SemanticCacheService(
        settings=Settings(), embeddings_service=embeddings, client=RecordingQdrant(), embed_timeout=5.0
    )
    service.enabled = True

    await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.9, max_entry_age_hours=24, **AUTO_REQUEST
    )

    assert embeddings.timeouts == [5.0]


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
    vector: list[float] | None = ANY_VECTOR,
) -> CacheHit | None:
    return await service.lookup(
        "hola",
        tenant_id="acme",
        similarity_threshold=0.9,
        max_entry_age_hours=24,
        context_hash=context,
        min_tier_rank=min_tier_rank,
        model=model,
        vector=vector,
    )


class _LookupCounts:
    """How many lookups ended in each result since this was created."""

    RESULTS = ("hit", "no_candidate", "below_threshold", "disabled", "embedding_unavailable", "error")

    def __init__(self) -> None:
        self._before = {result: cache_lookups(result) for result in self.RESULTS}

    def since(self) -> dict[str, float]:
        counts = {result: cache_lookups(result) - self._before[result] for result in self.RESULTS}
        return {result: count for result, count in counts.items() if count}


async def test_lookup_tells_no_candidate_from_a_candidate_below_the_threshold() -> None:
    service = await _in_memory_service()
    await _store(service, "frontier answer", tier="frontier")  # filed under [1, 0, 0]

    counts = _LookupCounts()
    # Another conversation: nothing passes the filters at all.
    assert await _lookup(service, context="other context", min_tier_rank=0) is None
    assert counts.since() == {"no_candidate": 1}

    counts = _LookupCounts()
    # The same conversation, but the closest answer is only 0.6 similar (threshold 0.9).
    assert await _lookup(service, min_tier_rank=0, vector=[0.6, 0.8, 0.0]) is None
    assert counts.since() == {"below_threshold": 1}

    counts = _LookupCounts()
    hit = await _lookup(service, min_tier_rank=0)
    assert hit is not None and hit.response == "frontier answer"
    assert counts.since() == {"hit": 1}


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


async def _cache_over_a_3_dim_collection(**settings: object) -> SemanticCacheService:
    """A cache whose existing collection holds 3-dim vectors (as `_in_memory_service` makes)."""
    existing = await _in_memory_service()
    return SemanticCacheService(
        settings=Settings(**settings),
        embeddings_service=FakeEmbeddings(),
        client=existing.client,
    )


async def test_a_collection_of_another_vector_size_leaves_the_cache_disabled() -> None:
    # The default embedding_dimensions is 768: an embedding model swap left the old collection.
    service = await _cache_over_a_3_dim_collection()

    await service.initialize()

    assert not service.enabled
    assert service.degraded_reason == (
        "Qdrant collection vector size 3 does not match embedding_dimensions 768."
    )


async def test_health_is_degraded_while_disabled_even_if_the_collection_exists() -> None:
    service = await _cache_over_a_3_dim_collection()
    await service.initialize()

    health = await service.health_status()

    assert health["status"] == "degraded"
    assert health["enabled"] is False
    assert health["detail"] == (
        "Qdrant collection vector size 3 does not match embedding_dimensions 768."
    )


# --- A late Qdrant: the gateway started first ----------------------------------------------


async def _cache_started_before_qdrant() -> tuple[SemanticCacheService, LateQdrant, FakeClock]:
    qdrant, clock = LateQdrant(), FakeClock()
    service = SemanticCacheService(
        settings=Settings(NEBULA_EMBEDDING_DIMENSIONS=3),
        embeddings_service=FakeEmbeddings(),
        client=qdrant,
        clock=clock,
    )
    await service.initialize()  # at gateway startup
    assert not service.enabled
    return service, qdrant, clock


async def test_a_lookup_retries_initialization_once_30_seconds_have_passed() -> None:
    service, qdrant, clock = await _cache_started_before_qdrant()
    qdrant.up = True

    clock.now += 29.0
    counts = _LookupCounts()
    assert await _lookup(service, min_tier_rank=0) is None
    # Too soon to retry: still disabled, without asking Qdrant.
    assert counts.since() == {"disabled": 1}
    assert qdrant.initializations == 1

    clock.now += 1.0
    counts = _LookupCounts()
    assert await _lookup(service, min_tier_rank=0) is None
    # Retried, recovered, and the lookup itself ran against the empty collection.
    assert service.enabled
    assert service.degraded_reason is None
    assert counts.since() == {"no_candidate": 1}
    assert qdrant.initializations == 2


async def test_a_store_retries_initialization_too() -> None:
    service, qdrant, clock = await _cache_started_before_qdrant()
    qdrant.up = True
    clock.now += 30.0

    await _store(service, "answer", tier="local")

    hit = await _lookup(service, min_tier_rank=0)
    assert hit is not None and hit.response == "answer"


async def test_failed_retries_are_at_least_30_seconds_apart() -> None:
    service, qdrant, clock = await _cache_started_before_qdrant()

    clock.now += 30.0
    await _lookup(service, min_tier_rank=0)  # retries; Qdrant is still down
    clock.now += 15.0
    await _lookup(service, min_tier_rank=0)
    await _store(service, "answer", tier="local")
    assert qdrant.initializations == 2

    clock.now += 15.0
    await _store(service, "answer", tier="local")
    assert qdrant.initializations == 3
    assert not service.enabled
    assert service.degraded_reason == "Qdrant is not up yet"


async def test_health_picks_up_a_late_qdrant_without_any_lookup() -> None:
    service, qdrant, clock = await _cache_started_before_qdrant()
    assert (await service.health_status())["status"] == "degraded"

    qdrant.up = True
    clock.now += 30.0
    health = await service.health_status()

    # Health retried on its own: no request had to come first.
    assert health["status"] == "ready"
    assert health["enabled"] is True
    assert service.enabled


async def test_health_retries_at_most_every_30_seconds() -> None:
    service, qdrant, clock = await _cache_started_before_qdrant()
    clock.now += 30.0
    assert (await service.health_status())["status"] == "degraded"  # retried; still down

    qdrant.up = True
    clock.now += 29.0
    health = await service.health_status()
    # Qdrant answers, but the last attempt was 29 s ago: the cache stays disabled until 30 s.
    assert health["status"] == "degraded"
    assert health["enabled"] is False

    clock.now += 1.0
    assert (await service.health_status())["status"] == "ready"


async def test_a_cache_that_stays_down_warns_once_per_reason(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="nebula.services.semantic_cache_service")
    service, qdrant, clock = await _cache_started_before_qdrant()
    for _ in range(2):
        clock.now += 30.0
        await _lookup(service, min_tier_rank=0)  # retries, and fails the same way
    qdrant.down_reason = "Connection refused"
    clock.now += 30.0
    await _lookup(service, min_tier_rank=0)
    qdrant.up = True
    clock.now += 30.0
    await _lookup(service, min_tier_rank=0)

    logged = [
        (record.levelname, record.getMessage())
        for record in caplog.records
        if record.name == "nebula.services.semantic_cache_service"
    ]
    assert logged == [
        ("WARNING", "semantic_cache_disabled: Qdrant is not up yet"),
        ("DEBUG", "semantic_cache_disabled: Qdrant is not up yet"),
        ("DEBUG", "semantic_cache_disabled: Qdrant is not up yet"),
        ("WARNING", "semantic_cache_disabled: Connection refused"),
        ("INFO", "semantic_cache_recovered"),
    ]


async def test_initialize_indexes_every_field_a_lookup_filters_on() -> None:
    # Local Qdrant ignores payload indexes, so this is checked at the client boundary.
    client = RecordingQdrant()
    service = SemanticCacheService(
        settings=Settings(), embeddings_service=FakeEmbeddings(), client=client
    )

    await service.initialize()

    indexed = sorted(client.indexed_fields)
    assert indexed == ["context_hash", "created_at", "model", "tenant_id", "tier_rank"]
