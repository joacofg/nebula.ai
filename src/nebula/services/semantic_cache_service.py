from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic, time
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.models.openai import ChatMessage
from nebula.models.resilience import DependencyHealthReason, build_dependency_health
from nebula.observability.metrics import CACHE_LOOKUPS
from nebula.services.embeddings_service import OllamaEmbeddingsService

logger = logging.getLogger(__name__)

# An answer can serve any request routed to its own tier or a lower one, never a higher one.
TIER_RANK: dict[str, int] = {"local": 0, "economy": 1, "frontier": 2}
# The rank of an answer from a model that is no tier's model (an explicit request for some other
# model): below every tier, so no auto lookup matches it, only an explicit one for that model.
UNTIERED_RANK = -1

# How long a disabled cache waits between attempts to initialize again.
REINITIALIZE_INTERVAL_SECONDS = 30.0

# Every payload field a lookup filters on.
_INDEXED_FIELDS: dict[str, qdrant_models.PayloadSchemaType] = {
    "tenant_id": qdrant_models.PayloadSchemaType.KEYWORD,
    "created_at": qdrant_models.PayloadSchemaType.INTEGER,
    "context_hash": qdrant_models.PayloadSchemaType.KEYWORD,
    "tier_rank": qdrant_models.PayloadSchemaType.INTEGER,
    "model": qdrant_models.PayloadSchemaType.KEYWORD,
}


def context_hash(messages: list[ChatMessage]) -> str:
    """SHA-256 of every message except the latest user one: the conversation an answer belongs to.

    Roles and contents only, in order. A single user message (no system prompt, no history)
    hashes the empty list.
    """
    latest_user = max(
        (index for index, message in enumerate(messages) if message.role == "user"), default=None
    )
    context = [
        {"role": message.role, "content": message.content}
        for index, message in enumerate(messages)
        if index != latest_user
    ]
    # ASCII-escaped, so any decoded JSON string encodes, a lone surrogate included.
    canonical = json.dumps(context, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


@dataclass(slots=True, frozen=True)
class CacheHit:
    response: str
    model: str
    score: float
    age_seconds: int


class SemanticCacheService:
    def __init__(
        self,
        settings: Settings,
        embeddings_service: OllamaEmbeddingsService,
        client: AsyncQdrantClient | None = None,
        *,
        clock: Callable[[], float] = monotonic,
        embed_timeout: float | None = None,
    ) -> None:
        self.settings = settings
        self.embeddings_service = embeddings_service
        # For the embeddings it computes itself; the gateway bounds them like its own.
        self.embed_timeout = embed_timeout
        # Tests and the offline replay pass an in-memory client; the gateway talks to the server.
        self.client = client or AsyncQdrantClient(
            url=self.settings.qdrant_url,
            check_compatibility=False,
        )
        self.enabled = False
        self.degraded_reason: str | None = None
        self._clock = clock
        self._last_initialize_at: float | None = None

    async def _retry_initialize(self) -> None:
        """A disabled cache (Qdrant was down at startup, say) tries again, at most every 30 s."""
        last = self._last_initialize_at
        if last is not None and self._clock() - last < REINITIALIZE_INTERVAL_SECONDS:
            return
        await self.initialize()
        if self.enabled:
            logger.info("semantic_cache_recovered")

    async def initialize(self) -> None:
        # Stamped before the first await, so concurrent requests start one retry, not several.
        self._last_initialize_at = self._clock()
        collection = self.settings.semantic_cache_collection
        expected_size = self.settings.embedding_dimensions
        try:
            exists = await self.client.collection_exists(collection)
            if exists:
                info = await self.client.get_collection(collection)
                size = getattr(info.config.params.vectors, "size", None)
                if size != expected_size:
                    # Vectors of another embedding model: every lookup and store would fail.
                    reason = (
                        f"Qdrant collection vector size {size} does not match "
                        f"embedding_dimensions {expected_size}."
                    )
                    logger.warning("semantic_cache_disabled: %s", reason)
                    self.enabled = False
                    self.degraded_reason = reason
                    return
            else:
                await self.client.create_collection(
                    collection_name=collection,
                    vectors_config=qdrant_models.VectorParams(
                        size=expected_size,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
            # Payload indexes make every lookup filter cheap; creating one is idempotent.
            for field_name, schema in _INDEXED_FIELDS.items():
                await self.client.create_payload_index(
                    collection_name=collection,
                    field_name=field_name,
                    field_schema=schema,
                )
            # Points written before entries carried a tier (and a context) can never match a
            # lookup again, so they only take space.
            await self.client.delete(
                collection_name=collection,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.IsEmptyCondition(
                                is_empty=qdrant_models.PayloadField(key="tier_rank")
                            )
                        ]
                    )
                ),
            )
            self.enabled = True
            self.degraded_reason = None
        except Exception as exc:
            logger.warning("semantic_cache_disabled: %s", exc)
            self.enabled = False
            self.degraded_reason = str(exc)

    async def lookup(
        self,
        prompt: str,
        *,
        tenant_id: str,
        similarity_threshold: float,
        max_entry_age_hours: int,
        context_hash: str,
        min_tier_rank: int | None,
        model: str | None,
        vector: list[float] | None = None,
    ) -> CacheHit | None:
        """The closest fresh answer of this tenant and conversation that can serve the request.

        Exactly one of `min_tier_rank` (an auto request: answers from that tier up) or `model`
        (an explicit-model request: that model's answers only) is set.
        """
        if (min_tier_rank is None) == (model is None):
            raise ValueError("Set exactly one of min_tier_rank or model.")
        if not self.enabled:
            await self._retry_initialize()
        if not self.enabled:
            CACHE_LOOKUPS.labels("disabled").inc()
            return None

        if vector is None:
            # Only for callers that bring no vector. The gateway's chat path brings one (it
            # embeds the prompt itself and, when that fails, counts `embedding_unavailable`
            # and skips the lookup, so each failure is counted once), except while the cache
            # is disabled: the lookup that re-enables it embeds here, and its store is skipped.
            vector = await self.embeddings_service.embed(prompt, timeout=self.embed_timeout)
            if vector is None:
                CACHE_LOOKUPS.labels("embedding_unavailable").inc()
                return None

        now = int(time())
        freshness_cutoff = now - max_entry_age_hours * 3600
        if model is not None:
            # An explicit-model request wants that model's answer, whatever its tier.
            serves_request = qdrant_models.FieldCondition(
                key="model",
                match=qdrant_models.MatchValue(value=model),
            )
        else:
            # An auto request accepts answers from its chosen tier or a higher one.
            serves_request = qdrant_models.FieldCondition(
                key="tier_rank",
                range=qdrant_models.Range(gte=min_tier_rank),
            )
        query_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="tenant_id",
                    match=qdrant_models.MatchValue(value=tenant_id),
                ),
                qdrant_models.FieldCondition(
                    key="created_at",
                    range=qdrant_models.Range(gte=freshness_cutoff),
                ),
                qdrant_models.FieldCondition(
                    key="context_hash",
                    match=qdrant_models.MatchValue(value=context_hash),
                ),
                serves_request,
            ]
        )
        try:
            # The best candidate, however far: the threshold is applied below, so a miss can
            # tell "nothing passed the filters" from "the closest answer is not close enough".
            results = await self.client.query_points(
                collection_name=self.settings.semantic_cache_collection,
                query=vector,
                query_filter=query_filter,
                limit=1,
                with_payload=True,
            )
        except Exception as exc:
            logger.warning("semantic_cache_lookup_failed: %s", exc)
            CACHE_LOOKUPS.labels("error").inc()
            return None

        points = getattr(results, "points", [])
        if not points:
            CACHE_LOOKUPS.labels("no_candidate").inc()
            return None

        point = points[0]
        score = float(getattr(point, "score", 0.0) or 0.0)
        if score < similarity_threshold:
            CACHE_LOOKUPS.labels("below_threshold").inc()
            return None

        payload = point.payload or {}
        response = payload.get("response")
        if not isinstance(response, str):
            # Every stored entry has a text response; one without is a corrupt point.
            logger.warning("semantic_cache_point_without_response id=%s", getattr(point, "id", None))
            CACHE_LOOKUPS.labels("error").inc()
            return None

        CACHE_LOOKUPS.labels("hit").inc()
        created_at = payload.get("created_at")
        age_seconds = now - int(created_at) if isinstance(created_at, (int, float)) else 0
        return CacheHit(
            response=response,
            model=str(payload.get("model") or "unknown"),
            score=score,
            age_seconds=max(age_seconds, 0),
        )

    async def store(
        self,
        response: str,
        *,
        tenant_id: str,
        vector: list[float] | None,
        context_hash: str,
        tier_rank: int,
        model: str,
    ) -> None:
        """Cache an answer under the request's embedding; the raw prompt is never stored."""
        if not self.enabled:
            await self._retry_initialize()
        if not self.enabled or vector is None:
            return

        try:
            await self.client.upsert(
                collection_name=self.settings.semantic_cache_collection,
                wait=False,
                points=[
                    qdrant_models.PointStruct(
                        id=str(uuid4()),
                        vector=vector,
                        payload={
                            "tenant_id": tenant_id,
                            "context_hash": context_hash,
                            "tier_rank": tier_rank,
                            "model": model,
                            "response": response,
                            "created_at": int(time()),
                        },
                    )
                ],
            )
        except Exception as exc:
            logger.warning("semantic_cache_store_failed: %s", exc)

    async def delete_expired(self, *, tenant_id: str, created_before: int) -> None:
        """Delete the tenant's entries written before `created_before` (epoch seconds).

        Lookups already skip them; this reclaims their space. Raises when Qdrant fails.
        """
        if not self.enabled:
            return
        await self.client.delete(
            collection_name=self.settings.semantic_cache_collection,
            points_selector=qdrant_models.FilterSelector(
                filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="tenant_id",
                            match=qdrant_models.MatchValue(value=tenant_id),
                        ),
                        qdrant_models.FieldCondition(
                            key="created_at",
                            range=qdrant_models.Range(lt=created_before),
                        ),
                    ]
                )
            ),
        )

    async def close(self) -> None:
        await self.client.close()

    async def health_status(self) -> dict[str, object]:
        try:
            exists = await self.client.collection_exists(self.settings.semantic_cache_collection)
        except Exception as exc:
            return build_dependency_health(
                dependency_class="serving_optional",
                lifecycle_state="degraded",
                serving_effect="continuity_limited",
                reason_code=DependencyHealthReason.SEMANTIC_CACHE_UNAVAILABLE,
                detail=f"Qdrant unavailable: {exc}",
                required=False,
                extra={"enabled": self.enabled},
            )
        if exists and not self.enabled:
            # Reachable, but initialization failed or found an unusable collection: no lookup
            # is served until a retry succeeds.
            return build_dependency_health(
                dependency_class="serving_optional",
                lifecycle_state="degraded",
                serving_effect="continuity_limited",
                reason_code=DependencyHealthReason.SEMANTIC_CACHE_UNAVAILABLE,
                detail=self.degraded_reason or "Semantic cache is disabled.",
                required=False,
                extra={"enabled": self.enabled},
            )
        if exists:
            return build_dependency_health(
                dependency_class="serving_optional",
                lifecycle_state="ready",
                serving_effect="continuity_limited",
                reason_code=DependencyHealthReason.SEMANTIC_CACHE_READY,
                detail="Semantic cache collection is reachable.",
                required=False,
                extra={"enabled": self.enabled},
            )
        return build_dependency_health(
            dependency_class="serving_optional",
            lifecycle_state="degraded",
            serving_effect="continuity_limited",
            reason_code=DependencyHealthReason.SEMANTIC_CACHE_COLLECTION_MISSING,
            detail=self.degraded_reason or "Semantic cache collection is missing.",
            required=False,
            extra={"enabled": self.enabled},
        )
