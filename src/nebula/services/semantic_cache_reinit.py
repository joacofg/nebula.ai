"""The gateway's semantic cache: a disabled cache re-initializes in the background.

`SemanticCacheService` retries a disabled cache inline, at most every 30 s, so the request that
triggers the retry waits for several Qdrant round trips. The gateway uses this subclass instead:
the retry runs as one background task and the triggering request answers as a disabled cache.
The base class keeps its inline retry because the pre-registered cache measurement
(`benchmarks/cache/v1`) pins its source by hash and replays with it.
"""

from __future__ import annotations

import asyncio
import contextlib

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
        # Stamped here, not only in initialize(), so the throttle holds before the task first runs.
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
        """Wait for a background retry in flight, if any."""
        if self._reinit_task is not None:
            await self._reinit_task

    async def close(self) -> None:
        task = self._reinit_task
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await super().close()
