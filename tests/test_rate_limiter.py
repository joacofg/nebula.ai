from __future__ import annotations

import pytest

from nebula.services.rate_limiter import RateLimiter


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_burst_up_to_the_limit_then_deny_with_retry_after() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    results = [await limiter.acquire("t", limit_per_minute=3) for _ in range(4)]

    assert [r.allowed for r in results] == [True, True, True, False]
    assert [r.remaining for r in results[:3]] == [2, 1, 0]
    assert results[3].retry_after_seconds == 20  # one token every 60/3 s
    assert results[0].limit == 3


async def test_tokens_refill_with_time_and_never_exceed_capacity() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    for _ in range(3):
        await limiter.acquire("t", limit_per_minute=3)
    clock.now += 20
    assert (await limiter.acquire("t", limit_per_minute=3)).allowed is True
    clock.now += 3600
    after_idle = await limiter.acquire("t", limit_per_minute=3)
    assert after_idle.remaining == 2


async def test_tenants_are_isolated() -> None:
    limiter = RateLimiter(clock=Clock())
    await limiter.acquire("a", limit_per_minute=1)
    assert (await limiter.acquire("a", limit_per_minute=1)).allowed is False
    assert (await limiter.acquire("b", limit_per_minute=1)).allowed is True


async def test_lowering_the_limit_takes_effect_at_once() -> None:
    limiter = RateLimiter(clock=Clock())
    await limiter.acquire("t", limit_per_minute=100)
    # 99 tokens left are capped to the new capacity of 1: one more, then denied.
    assert (await limiter.acquire("t", limit_per_minute=1)).allowed is True
    assert (await limiter.acquire("t", limit_per_minute=1)).allowed is False


async def test_a_clock_going_backwards_grants_nothing() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    await limiter.acquire("t", limit_per_minute=1)
    clock.now -= 500
    assert (await limiter.acquire("t", limit_per_minute=1)).allowed is False


async def test_reset_is_the_time_until_the_next_token() -> None:
    limiter = RateLimiter(clock=Clock())
    first = await limiter.acquire("t", limit_per_minute=60)
    assert first.reset_seconds == 1


def test_limit_must_be_positive() -> None:
    import asyncio

    with pytest.raises(ValueError):
        asyncio.run(RateLimiter().acquire("t", limit_per_minute=0))


async def test_reset_counts_to_the_next_token_not_to_a_full_bucket() -> None:
    limiter = RateLimiter(clock=Clock())
    for _ in range(2):
        drained = await limiter.acquire("t", limit_per_minute=2)
    assert drained.reset_seconds == 30


@pytest.mark.parametrize("limit", [11, 21, 22, 42])
async def test_float_error_does_not_add_a_second(limit: int) -> None:
    limiter = RateLimiter(clock=Clock())
    for _ in range(limit):
        await limiter.acquire("t", limit_per_minute=limit)
    denied = await limiter.acquire("t", limit_per_minute=limit)
    assert denied.retry_after_seconds == -(-60 // limit)  # ceil(60 / limit)


async def test_raising_the_limit_grants_tokens_now() -> None:
    limiter = RateLimiter(clock=Clock())
    for _ in range(2):
        await limiter.acquire("t", limit_per_minute=2)
    raised = await limiter.acquire("t", limit_per_minute=5)
    # The three extra tokens arrive at once instead of trickling in over the next minute.
    assert raised.allowed is True
    assert raised.remaining == 2


async def test_idle_buckets_are_swept() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    await limiter.acquire("t1", limit_per_minute=5)
    clock.now += 61
    await limiter.acquire("t2", limit_per_minute=5)
    assert limiter.bucket_count == 1


async def test_a_recently_used_bucket_survives_the_sweep() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    await limiter.acquire("idle", limit_per_minute=1)  # starts the sweep interval
    clock.now += 55
    await limiter.acquire("busy", limit_per_minute=1)  # drains its only token
    clock.now += 6  # 61 s into the interval: a sweep is due, but "busy" was used 6 s ago
    denied = await limiter.acquire("busy", limit_per_minute=1)
    assert denied.allowed is False
    assert limiter.bucket_count == 1  # only "idle" went
