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
    updated_at: float


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._buckets: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, tenant_id: str, *, limit_per_minute: int) -> RateLimitResult:
        if limit_per_minute < 1:
            raise ValueError("A rate limit must allow at least one request per minute.")
        capacity = float(limit_per_minute)
        rate = capacity / 60.0
        async with self._lock:
            now = self._clock()
            bucket = self._buckets.get(tenant_id)
            if bucket is None:
                bucket = self._buckets[tenant_id] = _Bucket(tokens=capacity, updated_at=now)
            elapsed = max(0.0, now - bucket.updated_at)  # a clock going backwards grants nothing
            bucket.tokens = min(capacity, bucket.tokens + elapsed * rate)
            bucket.updated_at = max(bucket.updated_at, now)
            allowed = bucket.tokens >= 1.0
            if allowed:
                bucket.tokens -= 1.0
            retry_after = 0 if allowed else max(1, math.ceil((1.0 - bucket.tokens) / rate))
            reset = math.ceil((capacity - bucket.tokens) / rate) if bucket.tokens < capacity else 0
            return RateLimitResult(
                allowed=allowed,
                limit=limit_per_minute,
                remaining=int(math.floor(bucket.tokens)),
                reset_seconds=max(0, reset),
                retry_after_seconds=retry_after,
            )
