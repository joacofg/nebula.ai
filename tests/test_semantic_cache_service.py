from __future__ import annotations

from time import time
from types import SimpleNamespace

import pytest
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.services.semantic_cache_service import CacheHit, SemanticCacheService


class FakeEmbeddings:
    async def embed(self, text: str) -> list[float] | None:
        return [0.1, 0.2, 0.3]


class RecordingQdrant:
    def __init__(self, points: list[object] | None = None) -> None:
        self.query_kwargs: list[dict] = []
        self.upserts: list[dict] = []
        self.points = points or []

    async def collection_exists(self, name: str) -> bool:
        return True

    async def create_payload_index(self, **kwargs) -> None:
        return None

    async def query_points(self, **kwargs):
        self.query_kwargs.append(kwargs)
        return SimpleNamespace(points=self.points)

    async def upsert(self, **kwargs) -> None:
        self.upserts.append(kwargs)

    async def close(self) -> None:
        return None


def _service(client: RecordingQdrant) -> SemanticCacheService:
    service = SemanticCacheService(settings=Settings(), embeddings_service=FakeEmbeddings())
    service.client = client
    service.enabled = True
    return service


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
        "hello", tenant_id="acme", similarity_threshold=0.93, max_entry_age_hours=2
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

    hit = await service.lookup("hello", tenant_id="acme", similarity_threshold=0.9, max_entry_age_hours=24)

    assert isinstance(hit, CacheHit)
    assert hit.response == "cached"
    assert hit.model == "llama3.2:3b"
    assert hit.score == pytest.approx(0.97)
    assert 88 <= hit.age_seconds <= 92


@pytest.mark.asyncio
async def test_store_writes_tenant_id_into_payload() -> None:
    client = RecordingQdrant()
    service = _service(client)

    await service.store("hello", "world", "llama3.2:3b", tenant_id="acme")

    payload = client.upserts[0]["points"][0].payload
    assert payload["tenant_id"] == "acme"
    assert payload["prompt"] == "hello"
    assert payload["response"] == "world"
    assert isinstance(payload["created_at"], int)
