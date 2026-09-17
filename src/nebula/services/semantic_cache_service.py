from __future__ import annotations

import logging
from dataclasses import dataclass
from time import time
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.models.resilience import DependencyHealthReason, build_dependency_health
from nebula.observability.metrics import CACHE_LOOKUPS
from nebula.services.embeddings_service import OllamaEmbeddingsService

logger = logging.getLogger(__name__)


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
    ) -> None:
        self.settings = settings
        self.embeddings_service = embeddings_service
        self.client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            check_compatibility=False,
        )
        self.enabled = False
        self.degraded_reason: str | None = None

    async def initialize(self) -> None:
        collection = self.settings.semantic_cache_collection
        try:
            exists = await self.client.collection_exists(collection)
            if not exists:
                await self.client.create_collection(
                    collection_name=collection,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.settings.embedding_dimensions,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
            # Payload indexes make the tenant/freshness filter cheap. Both calls
            # are idempotent on the Qdrant side.
            await self.client.create_payload_index(
                collection_name=collection,
                field_name="tenant_id",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
            )
            await self.client.create_payload_index(
                collection_name=collection,
                field_name="created_at",
                field_schema=qdrant_models.PayloadSchemaType.INTEGER,
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
    ) -> CacheHit | None:
        if not self.enabled:
            CACHE_LOOKUPS.labels("disabled").inc()
            return None

        vector = await self.embeddings_service.embed(prompt)
        if vector is None:
            CACHE_LOOKUPS.labels("embedding_unavailable").inc()
            return None

        now = int(time())
        freshness_cutoff = now - max_entry_age_hours * 3600
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
            ]
        )
        try:
            results = await self.client.query_points(
                collection_name=self.settings.semantic_cache_collection,
                query=vector,
                query_filter=query_filter,
                limit=1,
                score_threshold=similarity_threshold,
                with_payload=True,
            )
        except Exception as exc:
            logger.warning("semantic_cache_lookup_failed: %s", exc)
            CACHE_LOOKUPS.labels("error").inc()
            return None

        points = getattr(results, "points", [])
        if not points:
            CACHE_LOOKUPS.labels("miss").inc()
            return None

        point = points[0]
        payload = point.payload or {}
        response = payload.get("response")
        if not isinstance(response, str):
            CACHE_LOOKUPS.labels("miss").inc()
            return None

        CACHE_LOOKUPS.labels("hit").inc()
        created_at = payload.get("created_at")
        age_seconds = now - int(created_at) if isinstance(created_at, int) else 0
        return CacheHit(
            response=response,
            model=str(payload.get("model") or "unknown"),
            score=float(getattr(point, "score", 0.0) or 0.0),
            age_seconds=max(age_seconds, 0),
        )

    async def store(self, prompt: str, response: str, model: str, *, tenant_id: str) -> None:
        if not self.enabled:
            return

        vector = await self.embeddings_service.embed(prompt)
        if vector is None:
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
                            "prompt": prompt,
                            "response": response,
                            "model": model,
                            "created_at": int(time()),
                        },
                    )
                ],
            )
        except Exception as exc:
            logger.warning("semantic_cache_store_failed: %s", exc)

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
