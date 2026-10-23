"""The gateway's semantic cache: a disabled cache re-initializes in the background.

`SemanticCacheService` retries a disabled cache inline, at most every 30 s, so the request that
triggers the retry waits for several Qdrant round trips. The gateway uses this subclass instead:
the retry runs as one background task and the triggering request answers as a disabled cache.
A health check made while the retry runs still reports the last attempt's state.

The base class keeps its inline retry because the pre-registered cache measurement
(`benchmarks/cache/v1`) pins its source by hash and replays with it. This subclass overrides the
base's private `_retry_initialize` and reads `_last_initialize_at` and `_clock`; that same hash
pin (`tests/test_cache_eval.py`) fails if the base ever changes them.
"""

from __future__ import annotations

import asyncio

from nebula.services.semantic_cache_service import (
    REINITIALIZE_INTERVAL_SECONDS,
    SemanticCacheService,
    logger,
)


class BackgroundReinitSemanticCacheService(SemanticCacheService):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._reinit_task: asyncio.Task[None] | None = None

    async def _retry_initialize(self) -> None:
        """Start one background retry when the throttle allows it; never wait for it."""
        if self._reinit_task is not None and not self._reinit_task.done():
            return
        last = self._last_initialize_at
        if last is not None and self._clock() - last < REINITIALIZE_INTERVAL_SECONDS:
            return
        # A retry cancelled before it runs still counts against the throttle.
        self._last_initialize_at = self._clock()
        self._reinit_task = asyncio.create_task(self._reinitialize())

    async def _reinitialize(self) -> None:
        try:
            await self.initialize()
        except Exception:
            # initialize() records Qdrant failures itself; anything else must not die unseen.
            logger.exception("semantic_cache_reinitialize_failed")
            return
        if self.enabled:
            logger.info("semantic_cache_recovered")

    async def settle(self) -> None:
        """For tests: wait until a background retry in flight, if any, has finished."""
        if self._reinit_task is not None:
            await asyncio.wait({self._reinit_task})

    async def close(self) -> None:
        task = self._reinit_task
        if task is not None and not task.done():
            task.cancel()
            # wait(), not await task: a cancellation of close() itself still propagates.
            await asyncio.wait({task})
        await super().close()
