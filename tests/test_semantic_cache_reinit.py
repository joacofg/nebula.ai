from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from nebula.core.config import Settings
from nebula.services.semantic_cache_reinit import BackgroundReinitSemanticCacheService
from nebula.services.semantic_cache_service import TIER_RANK, context_hash
from tests.support import FakeClock, LateQdrant, LookupCounts, configured_app

pytestmark = pytest.mark.filterwarnings("ignore:Payload indexes have no effect")

ANY_VECTOR = [0.1, 0.2, 0.3]
EMPTY_CONTEXT = context_hash([])


class FakeEmbeddings:
    async def embed(self, text: str, *, timeout: float | None = None) -> list[float] | None:
        return ANY_VECTOR


class SlowQdrant(LateQdrant):
    """A late Qdrant that, once up, holds every call until `release` is set."""

    def __init__(self) -> None:
        super().__init__()
        self.up = True
        self.release = asyncio.Event()

    def __getattr__(self, name: str):
        call = super().__getattr__(name)

        async def slow(*args, **kwargs):
            if self.up:
                await self.release.wait()
            return await call(*args, **kwargs)

        return slow


async def _started_before_qdrant(
    qdrant: LateQdrant | None = None,
) -> tuple[BackgroundReinitSemanticCacheService, LateQdrant, FakeClock]:
    qdrant, clock = qdrant or LateQdrant(), FakeClock()
    service = BackgroundReinitSemanticCacheService(
        settings=Settings(NEBULA_EMBEDDING_DIMENSIONS=3),
        embeddings_service=FakeEmbeddings(),
        client=qdrant,
        clock=clock,
    )
    up = qdrant.up
    qdrant.up = False
    await service.initialize()  # at gateway startup, Qdrant still down
    qdrant.up = up
    assert not service.enabled
    return service, qdrant, clock


async def _lookup(service: BackgroundReinitSemanticCacheService):
    return await service.lookup(
        "hola",
        tenant_id="acme",
        similarity_threshold=0.9,
        max_entry_age_hours=24,
        context_hash=EMPTY_CONTEXT,
        min_tier_rank=0,
        model=None,
        vector=ANY_VECTOR,
    )


async def _store(service: BackgroundReinitSemanticCacheService, response: str) -> None:
    await service.store(
        response,
        tenant_id="acme",
        vector=ANY_VECTOR,
        context_hash=EMPTY_CONTEXT,
        tier_rank=TIER_RANK["local"],
        model="local-model",
    )


async def test_requests_while_down_start_one_background_initialize() -> None:
    service, qdrant, clock = await _started_before_qdrant()
    qdrant.up = True
    clock.now += 30.0

    counts = LookupCounts()
    results = await asyncio.gather(_lookup(service), _lookup(service), _lookup(service))

    # The requests answered as a disabled cache; none of them ran the retry itself.
    assert results == [None, None, None]
    assert counts.since() == {"disabled": 3}
    await service.settle()
    assert qdrant.initializations == 2  # startup + one background retry
    assert service.enabled

    counts = LookupCounts()
    assert await _lookup(service) is None
    assert counts.since() == {"no_candidate": 1}


async def test_a_request_does_not_wait_for_a_slow_initialize() -> None:
    service, qdrant, clock = await _started_before_qdrant(SlowQdrant())
    clock.now += 30.0

    assert await asyncio.wait_for(_lookup(service), timeout=1.0) is None
    assert not service.enabled

    qdrant.release.set()
    await service.settle()
    assert service.enabled


async def test_background_retries_keep_the_30_second_throttle() -> None:
    service, qdrant, clock = await _started_before_qdrant()

    clock.now += 30.0
    await _lookup(service)  # schedules a retry; Qdrant is still down
    await service.settle()
    clock.now += 15.0
    await _lookup(service)
    await _store(service, "answer")
    await service.settle()
    assert qdrant.initializations == 2

    clock.now += 15.0
    await _store(service, "answer")
    await service.settle()
    assert qdrant.initializations == 3
    assert not service.enabled
    assert service.degraded_reason == "Qdrant is not up yet"


async def test_a_store_while_down_never_raises_and_recovers_the_cache() -> None:
    service, qdrant, clock = await _started_before_qdrant()
    qdrant.up = True
    clock.now += 30.0

    await _store(service, "dropped")  # the cache is still disabled: nothing stored
    await service.settle()
    await _store(service, "answer")

    hit = await _lookup(service)
    assert hit is not None and hit.response == "answer"


async def test_health_schedules_the_retry_and_reports_ready_once_it_is_done() -> None:
    service, qdrant, clock = await _started_before_qdrant()
    qdrant.up = True
    clock.now += 30.0

    assert (await service.health_status())["enabled"] is False
    await service.settle()
    health = await service.health_status()

    assert health["status"] == "ready"
    assert health["enabled"] is True


async def test_close_cancels_a_pending_initialize() -> None:
    qdrant = SlowQdrant()
    service, _, clock = await _started_before_qdrant(qdrant)
    clock.now += 30.0
    await _lookup(service)
    task = service._reinit_task
    assert task is not None and not task.done()

    qdrant.release.set()  # let the client's own close() through
    await service.close()

    assert task.cancelled() or task.done()


def test_the_gateway_uses_the_background_reinit_cache() -> None:
    with configured_app() as app, TestClient(app):
        assert isinstance(app.state.container.cache_service, BackgroundReinitSemanticCacheService)
