"""Per-tenant requests-per-minute limit: a token bucket held in memory.

The bucket holds up to `limit` tokens and refills at `limit / 60` per second,
so a tenant can burst its whole minute and then proceeds at the steady rate.
State lives in this process: with several gateway processes each keeps its
own buckets and the effective limit multiplies (the supported self-hosted
stack runs one uvicorn process).
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic

# A bucket idle this long has refilled to capacity, so dropping it equals a fresh bucket.
_SWEEP_INTERVAL_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after_seconds: int


@dataclass(slots=True)
class _Bucket:
    tokens: float
    capacity: float
    updated_at: float


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._buckets: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()
        self._last_sweep: float | None = None

    @property
    def bucket_count(self) -> int:
        return len(self._buckets)

    async def acquire(self, tenant_id: str, *, limit_per_minute: int) -> RateLimitResult:
        if limit_per_minute < 1:
            raise ValueError("A rate limit must allow at least one request per minute.")
        capacity = float(limit_per_minute)
        rate = capacity / 60.0
        async with self._lock:
            now = self._clock()
            self._sweep(now)
            bucket = self._buckets.get(tenant_id)
            if bucket is None:
                bucket = self._buckets[tenant_id] = _Bucket(
                    tokens=capacity, capacity=capacity, updated_at=now
                )
            elapsed = max(0.0, now - bucket.updated_at)  # a clock going backwards grants nothing
            # Refill under the limit the bucket was last used with, then apply any change of limit.
            bucket.tokens = min(bucket.capacity, bucket.tokens + elapsed * bucket.capacity / 60.0)
            bucket.updated_at = max(bucket.updated_at, now)
            if capacity > bucket.capacity:
                bucket.tokens += capacity - bucket.capacity  # a raised limit pays out at once
            bucket.tokens = min(capacity, bucket.tokens)
            bucket.capacity = capacity
            allowed = bucket.tokens >= 1.0
            if allowed:
                bucket.tokens -= 1.0
            # ceil(x - 1e-9): 1/(11/60) must round to 6 s, not 7, despite float error.
            retry_after = 0 if allowed else max(1, math.ceil((1.0 - bucket.tokens) / rate - 1e-9))
            # Seconds until the next token (0 when the bucket is full).
            fraction = bucket.tokens - math.floor(bucket.tokens)
            reset = 0 if bucket.tokens >= capacity else math.ceil((1.0 - fraction) / rate - 1e-9)
            return RateLimitResult(
                allowed=allowed,
                limit=limit_per_minute,
                remaining=int(math.floor(bucket.tokens)),
                reset_seconds=max(0, reset),
                retry_after_seconds=retry_after,
            )

    def _sweep(self, now: float) -> None:
        """Drop idle buckets, at most once per interval, so tenants that left do not pile up."""
        if self._last_sweep is None:
            self._last_sweep = now
            return
        if now - self._last_sweep < _SWEEP_INTERVAL_SECONDS:
            return
        self._last_sweep = now
        idle = [
            tenant_id
            for tenant_id, bucket in self._buckets.items()
            if now - bucket.updated_at >= _SWEEP_INTERVAL_SECONDS
        ]
        for tenant_id in idle:
            del self._buckets[tenant_id]
