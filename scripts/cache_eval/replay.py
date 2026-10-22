"""Replay the evaluation sets through the gateway's own semantic cache.

Every lookup and store goes through ``nebula.services.semantic_cache_service.SemanticCacheService``
over an in-memory Qdrant, so the measurement describes the product's matching code (filters,
scoring, tier rule), not a re-implementation of it. One tenant, single-turn requests (the empty
conversation context). Each stored answer is a marker naming the corpus prompt it answers and
the tier that produced it; a hit's marker says whether the hit was correct and which tier's
answer it served.

Lookups ask for the best candidate at a floor threshold of 0.0 and the registered thresholds
are applied here, ``score >= t``: one lookup per query serves the whole grid.
"""

from __future__ import annotations

import json
import random
import warnings
from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.models.openai import ChatMessage
from nebula.services.learned_router import Tier
from nebula.services.semantic_cache_service import TIER_RANK, SemanticCacheService, context_hash

TENANT_ID = "cache-eval"
COLLECTION = "cache-eval"
# The lowest threshold a lookup is asked for: no cosine is below it, so the lookup returns the
# best candidate however far, every registered threshold is applied afterwards to the same
# answer, and "no candidate" while an eligible entry exists can only mean the lookup failed.
FLOOR_THRESHOLD = -1.0
MAX_ENTRY_AGE_HOURS = 24
# The served model per tier, as the corpus captured it (the model field only matters to
# explicit-model lookups, which the replay never makes).
TIER_MODELS: dict[str, str] = {
    "local": "qwen2.5:7b",
    "economy": "anthropic/claude-haiku-4.5",
    "frontier": "openai/gpt-4.1",
}


@dataclass(frozen=True)
class Original:
    """A corpus prompt held by the cache: its id, text, router tier and one vector per model."""

    prompt_id: str
    text: str
    tier: Tier
    vectors: Mapping[str, list[float]]


@dataclass(frozen=True)
class Paraphrase:
    """A rewrite of the original ``prompt_id``, routed on its own vector to its own tier."""

    prompt_id: str
    text: str
    tier: Tier
    vectors: Mapping[str, list[float]]


Query = Original | Paraphrase


@dataclass(frozen=True)
class Candidate:
    """The best cache entry a lookup found: the prompt it answers, its tier and its cosine."""

    prompt_id: str | None
    tier: Tier | None
    score: float | None

    def hit(self, t: float) -> bool:
        return self.score is not None and self.score >= t


class _NoEmbeddings:
    """The replay hands every lookup its vector; an embedding call would be a bug."""

    async def embed(self, text: str, *, timeout: float | None = None) -> list[float] | None:
        raise RuntimeError("The cache replay passes every vector; nothing may be embedded.")


def marker(prompt_id: str, tier: str) -> str:
    """The stored "answer": which prompt it answers and which tier produced it."""
    return json.dumps({"prompt_id": prompt_id, "tier": tier}, sort_keys=True)


def request_context(text: str) -> str:
    """The gateway's context key of a single-turn request (no system prompt, no history)."""
    return context_hash([ChatMessage(role="user", content=text)])


async def new_cache(
    *, dimensions: int, client: AsyncQdrantClient | None = None
) -> SemanticCacheService:
    """An empty, initialized gateway cache over an in-memory Qdrant (or the given client)."""
    settings = Settings(
        _env_file=None,
        embedding_dimensions=dimensions,
        semantic_cache_collection=COLLECTION,
    )
    cache = SemanticCacheService(
        settings, _NoEmbeddings(), client=client or AsyncQdrantClient(location=":memory:")
    )
    with warnings.catch_warnings():
        # Local Qdrant says on every index that payload indexes have no effect there.
        warnings.filterwarnings("ignore", message="Payload indexes have no effect")
        await cache.initialize()
    if not cache.enabled:
        raise RuntimeError(f"The in-memory cache did not initialize: {cache.degraded_reason}")
    return cache


async def store(cache: SemanticCacheService, query: Query, *, tier: str, model_key: str) -> None:
    """Cache ``tier``'s answer to ``query`` under the query's vector, as the gateway does."""
    await cache.store(
        marker(query.prompt_id, tier),
        tenant_id=TENANT_ID,
        vector=query.vectors[model_key],
        context_hash=request_context(query.text),
        tier_rank=TIER_RANK[tier],
        model=TIER_MODELS[tier],
    )


async def point_count(cache: SemanticCacheService, *, min_tier_rank: int | None = None) -> int:
    """How many entries the collection holds (from ``min_tier_rank`` up, when given)."""
    count_filter = None
    if min_tier_rank is not None:
        count_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="tier_rank", range=qdrant_models.Range(gte=min_tier_rank)
                )
            ]
        )
    result = await cache.client.count(
        collection_name=COLLECTION, count_filter=count_filter, exact=True
    )
    return result.count


async def _eligible_counts(cache: SemanticCacheService) -> dict[int, int]:
    """Entries a lookup with each tier's rank may match (every entry shares tenant and context)."""
    return {rank: await point_count(cache, min_tier_rank=rank) for rank in TIER_RANK.values()}


async def build_cache(
    originals: Sequence[Original], *, model_key: str, client: AsyncQdrantClient | None = None
) -> SemanticCacheService:
    """The gateway cache holding every original's answer at its router tier, in input order.

    The gateway's store only logs a failure, so the collection is counted afterwards: a cache
    missing any original raises instead of quietly turning hits into misses.
    """
    if not originals:
        raise ValueError("build_cache needs at least one original; use new_cache for an empty one.")
    cache = await new_cache(dimensions=len(originals[0].vectors[model_key]), client=client)
    for original in originals:
        await store(cache, original, tier=original.tier, model_key=model_key)
    stored = await point_count(cache)
    if stored != len(originals):
        raise RuntimeError(
            f"The cache stored {stored} of {len(originals)} originals: a store failed."
        )
    return cache


async def lookup(
    cache: SemanticCacheService,
    query: Query,
    *,
    model_key: str,
    min_tier_rank: int,
    expect_candidate: bool,
) -> Candidate:
    """The gateway's lookup for ``query`` at the floor threshold: its best candidate.

    The gateway turns a failed query into a miss. With the floor below every cosine, a lookup
    that finds nothing although ``expect_candidate`` (an eligible entry exists) has failed, and
    raises.
    """
    found = await cache.lookup(
        query.text,
        tenant_id=TENANT_ID,
        similarity_threshold=FLOOR_THRESHOLD,
        max_entry_age_hours=MAX_ENTRY_AGE_HOURS,
        context_hash=request_context(query.text),
        min_tier_rank=min_tier_rank,
        model=None,
        vector=query.vectors[model_key],
    )
    if found is None:
        if expect_candidate:
            raise RuntimeError(
                f"The cache lookup for {query.prompt_id} found nothing although an eligible entry "
                "exists: the lookup failed (see the semantic_cache_lookup_failed log)."
            )
        return Candidate(None, None, None)
    answer = json.loads(found.response)
    return Candidate(answer["prompt_id"], answer["tier"], found.score)


def _min_rank(query: Query, tier_rule: bool) -> int:
    # Rule off: every entry (rank 0, 1 or 2) is eligible, so matching is on similarity alone.
    return TIER_RANK[query.tier] if tier_rule else 0


async def best_candidates(
    cache: SemanticCacheService,
    queries: Sequence[Query],
    *,
    model_key: str,
    tier_rule: bool = False,
) -> list[Candidate]:
    eligible = await _eligible_counts(cache)
    out = []
    for q in queries:
        rank = _min_rank(q, tier_rule)
        out.append(
            await lookup(
                cache,
                q,
                model_key=model_key,
                min_tier_rank=rank,
                expect_candidate=eligible[rank] > 0,
            )
        )
    return out


async def _point_ids(cache: SemanticCacheService) -> dict[str, list[str]]:
    """Point ids by stored marker."""
    ids: dict[str, list[str]] = {}
    offset = None
    while True:
        points, offset = await cache.client.scroll(
            collection_name=COLLECTION, limit=1000, offset=offset, with_payload=True
        )
        for point in points:
            ids.setdefault(str(point.payload["response"]), []).append(str(point.id))
        if offset is None:
            return ids


async def leave_one_out_candidates(
    cache: SemanticCacheService,
    originals: Sequence[Original],
    *,
    model_key: str,
    tier_rule: bool = False,
) -> list[Candidate]:
    """Each original's best candidate among the other originals.

    Its own entry is taken out of the collection for its lookup and put back unchanged (same
    id, vector and payload) right after, so the cache ends as it started.
    """
    ids = await _point_ids(cache)
    eligible = await _eligible_counts(cache)
    total = await point_count(cache)
    out: list[Candidate] = []
    for original in originals:
        own = ids[marker(original.prompt_id, original.tier)]
        saved = await cache.client.retrieve(
            collection_name=COLLECTION, ids=own, with_payload=True, with_vectors=True
        )
        await cache.client.delete(
            collection_name=COLLECTION,
            points_selector=qdrant_models.PointIdsList(points=own),
        )
        rank = _min_rank(original, tier_rule)
        others = eligible[rank] - (len(own) if TIER_RANK[original.tier] >= rank else 0)
        try:
            out.append(
                await lookup(
                    cache,
                    original,
                    model_key=model_key,
                    min_tier_rank=rank,
                    expect_candidate=others > 0,
                )
            )
        finally:
            await cache.client.upsert(
                collection_name=COLLECTION,
                points=[
                    qdrant_models.PointStruct(id=p.id, vector=p.vector, payload=p.payload)
                    for p in saved
                ],
            )
    if await point_count(cache) != total:
        raise RuntimeError("Leave-one-out did not put every original back in the cache.")
    return out


@dataclass(frozen=True)
class ReplayCandidates:
    """Everything the paraphrase replay needs for any threshold: per paraphrase, its best
    candidate with the tier rule as asked and without it (to count tier blocks); per
    original, its leave-one-out candidate."""

    paraphrases: list[Paraphrase]
    paraphrase_best: list[Candidate]
    paraphrase_best_rule_off: list[Candidate]
    loo_best: list[Candidate]


async def replay_candidates(
    cache: SemanticCacheService,
    paraphrases: Sequence[Paraphrase],
    originals: Sequence[Original],
    *,
    model_key: str,
    tier_rule: bool = False,
) -> ReplayCandidates:
    rule_off = await best_candidates(cache, paraphrases, model_key=model_key)
    rule_as_asked = (
        await best_candidates(cache, paraphrases, model_key=model_key, tier_rule=True)
        if tier_rule
        else rule_off
    )
    loo = await leave_one_out_candidates(cache, originals, model_key=model_key, tier_rule=tier_rule)
    return ReplayCandidates(list(paraphrases), rule_as_asked, rule_off, loo)


def replay_metrics(candidates: ReplayCandidates, *, t: float) -> dict:
    """Set (c) at threshold t: a correct hit is a paraphrase whose best candidate is its own
    original; every other hit, any leave-one-out hit included, is a false hit.
    Precision = correct / hits; recall = correct / paraphrases."""
    correct = paraphrase_hits = tier_blocked = 0
    for query, best, rule_off in zip(
        candidates.paraphrases,
        candidates.paraphrase_best,
        candidates.paraphrase_best_rule_off,
        strict=True,
    ):
        if best.hit(t):
            paraphrase_hits += 1
            correct += best.prompt_id == query.prompt_id
        own_without_rule = rule_off.hit(t) and rule_off.prompt_id == query.prompt_id
        own_with_rule = best.hit(t) and best.prompt_id == query.prompt_id
        tier_blocked += own_without_rule and not own_with_rule
    loo_hits = sum(1 for best in candidates.loo_best if best.hit(t))
    hits = paraphrase_hits + loo_hits
    n = len(candidates.paraphrases)
    return {
        "t": t,
        "hits": hits,
        "paraphrase_hits": paraphrase_hits,
        "loo_hits": loo_hits,
        "correct_hits": correct,
        "false_hits": hits - correct,
        "tier_blocked": tier_blocked,
        "precision": correct / hits if hits else None,
        "recall": correct / n if n else None,
    }


async def paraphrase_replay(
    cache: SemanticCacheService,
    paraphrases: Sequence[Paraphrase],
    originals: Sequence[Original],
    *,
    t: float,
    model_key: str,
    tier_rule: bool = False,
) -> dict:
    """Set (c) at one threshold (see ``replay_metrics``); the verdict runs it with the rule off."""
    candidates = await replay_candidates(
        cache, paraphrases, originals, model_key=model_key, tier_rule=tier_rule
    )
    return replay_metrics(candidates, t=t)


# --- Savings over a trace with repeats ------------------------------------------------------

SEED = 20261022
TRACE_LENGTH = 1000


@dataclass(frozen=True)
class Request:
    """One request of a trace: a new corpus prompt (``fresh``), the same text again
    (``exact``), or the valid paraphrase of an earlier prompt (``paraphrase``)."""

    kind: Literal["fresh", "exact", "paraphrase"]
    prompt_id: str


def trace(
    original_ids: Sequence[str],
    paraphrased_ids: Collection[str],
    *,
    rate: float,
    n: int = TRACE_LENGTH,
    seed: int = SEED,
) -> list[Request]:
    """``n`` requests of which exactly ``round(rate * n)`` are repeats of a prompt already asked
    earlier in the trace, half of them exact and half paraphrases (the extra one, if odd, exact).

    Each position is a repeat with probability ``rate``: the repeat positions are the first
    ``round(rate * n)`` of a seeded permutation of the positions, alternately exact and
    paraphrase, so the repeats of a lower rate are among those of a higher one and the rate
    on the axis is the rate in the trace (drawing each request independently gave 61 repeats
    instead of 37 at r = 0.037 with this seed). New prompts come in a seeded shuffle of the
    sorted ids, each at most once, so a trace without repeats sends every prompt exactly once
    when ``n`` equals their number. A repeat picks uniformly among the prompts asked so far
    (for a paraphrase, among those with a valid paraphrase); a repeat that comes before any
    prompt it could repeat is moved to the next position where one exists.
    """
    rng = random.Random(seed)
    fresh_order = sorted(original_ids)
    rng.shuffle(fresh_order)
    positions = rng.sample(range(n), n)
    picks = [rng.random() for _ in range(n)]
    kind_at: dict[int, str] = {
        position: "exact" if j % 2 == 0 else "paraphrase"
        for j, position in enumerate(positions[: round(rate * n)])
    }
    asked: list[str] = []
    asked_paraphrased: list[str] = []
    owed: list[str] = []  # repeats that came too early, served at the next possible position
    requests: list[Request] = []
    for i in range(n):
        if i in kind_at:
            owed.append(kind_at[i])
        pools = {"exact": asked, "paraphrase": asked_paraphrased}
        ready = next((kind for kind in owed if pools[kind]), None)
        if ready is not None:
            owed.remove(ready)
            pool = pools[ready]
            requests.append(Request(ready, pool[int(picks[i] * len(pool))]))
            continue
        if len(asked) == len(fresh_order):
            raise ValueError(f"A trace of {n} requests needs more than {len(fresh_order)} prompts.")
        prompt_id = fresh_order[len(asked)]
        asked.append(prompt_id)
        if prompt_id in paraphrased_ids:
            asked_paraphrased.append(prompt_id)
        requests.append(Request("fresh", prompt_id))
    return requests


@dataclass(frozen=True)
class Prices:
    """Per corpus prompt and tier: what serving it costs (USD) and whether that tier's answer
    can replace the frontier answer (1.0 or 0.0; the frontier is the reference)."""

    cost: Mapping[str, Mapping[str, float]]
    quality: Mapping[str, Mapping[str, float]]


async def simulate(
    requests: Sequence[Request],
    originals: Sequence[Original],
    paraphrases: Sequence[Paraphrase],
    prices: Prices,
    *,
    model_key: str,
    t: float,
    client: AsyncQdrantClient | None = None,
) -> dict:
    """Serve ``requests`` in order through an initially empty gateway cache, tier rule on.

    Each request is looked up with its own tier's rank. A hit at ``t`` costs 0; a correct hit
    (the entry answers the same prompt) keeps the quality of the entry's tier for that prompt,
    a false hit is worth 0. A miss is served at the request's tier, at that tier's cost and
    quality, and stored. A paraphrase costs what its original costs on the same tier. A tier
    block is a request whose own prompt's answer would have been a hit without the tier rule.
    A lookup that finds nothing while an eligible entry was stored, or a cache that ends with
    fewer entries than misses stored, raises: the gateway's cache would hide either failure.
    """
    by_id = {o.prompt_id: o for o in originals}
    paraphrase_of = {p.prompt_id: p for p in paraphrases}
    dimensions = len(next(iter(by_id.values())).vectors[model_key])
    cache = await new_cache(dimensions=dimensions, client=client)
    stored_ranks: dict[str, list[int]] = {}
    stored_by_rank = Counter()
    totals = Counter()
    for request in requests:
        query = (
            paraphrase_of[request.prompt_id]
            if request.kind == "paraphrase"
            else by_id[request.prompt_id]
        )
        pid, tier = request.prompt_id, query.tier
        rank = TIER_RANK[tier]
        totals["router_cost"] += prices.cost[pid][tier]
        totals["router_quality"] += prices.quality[pid][tier]
        totals["frontier_cost"] += prices.cost[pid]["frontier"]
        totals[request.kind] += 1

        eligible = sum(n for stored_rank, n in stored_by_rank.items() if stored_rank >= rank)
        best = await lookup(
            cache, query, model_key=model_key, min_tier_rank=rank, expect_candidate=eligible > 0
        )
        correct = best.hit(t) and best.prompt_id == pid
        if not correct and any(r < rank for r in stored_ranks.get(pid, [])):
            without_rule = await lookup(
                cache, query, model_key=model_key, min_tier_rank=0, expect_candidate=True
            )
            totals["tier_blocked"] += without_rule.hit(t) and without_rule.prompt_id == pid
        if best.hit(t):
            totals["hits"] += 1
            if correct:
                totals["correct_hits"] += 1
                totals["quality"] += prices.quality[pid][best.tier]
            else:
                totals["false_hits"] += 1
        else:
            totals["cost"] += prices.cost[pid][tier]
            totals["quality"] += prices.quality[pid][tier]
            await store(cache, query, tier=tier, model_key=model_key)
            stored_ranks.setdefault(pid, []).append(rank)
            stored_by_rank[rank] += 1

    stored = await point_count(cache)
    if stored != stored_by_rank.total():
        raise RuntimeError(
            f"The cache holds {stored} entries after {stored_by_rank.total()} stored misses: "
            "a store failed."
        )
    n = len(requests)
    per_1000 = 1000 / n
    return {
        "t": t,
        "requests": n,
        "fresh": totals["fresh"],
        "repeats_exact": totals["exact"],
        "repeats_paraphrase": totals["paraphrase"],
        "hits": totals["hits"],
        "correct_hits": totals["correct_hits"],
        "false_hits": totals["false_hits"],
        "tier_blocked": totals["tier_blocked"],
        "hit_rate": totals["hits"] / n,
        "false_hit_rate": totals["false_hits"] / n,
        "cost_per_1000": totals["cost"] * per_1000,
        "router_only_cost_per_1000": totals["router_cost"] * per_1000,
        "frontier_cost_per_1000": totals["frontier_cost"] * per_1000,
        "saving_vs_frontier": 1 - totals["cost"] / totals["frontier_cost"],
        "extra_saving_vs_router": (
            1 - totals["cost"] / totals["router_cost"] if totals["router_cost"] else 0.0
        ),
        "quality": totals["quality"] / n,
        "router_only_quality": totals["router_quality"] / n,
    }


async def savings_curve(
    originals: Sequence[Original],
    paraphrases: Sequence[Paraphrase],
    prices: Prices,
    *,
    model_key: str,
    rates: Sequence[float],
    t: float,
    seed: int = SEED,
    n: int = TRACE_LENGTH,
) -> list[dict]:
    """One simulated trace per repetition rate (see ``trace`` and ``simulate``)."""
    ids = [o.prompt_id for o in originals]
    paraphrased = {p.prompt_id for p in paraphrases}
    rows = []
    for rate in rates:
        requests = trace(ids, paraphrased, rate=rate, n=n, seed=seed)
        row = await simulate(requests, originals, paraphrases, prices, model_key=model_key, t=t)
        rows.append({"r": rate, **row})
    return rows
