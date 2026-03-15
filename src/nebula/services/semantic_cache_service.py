from __future__ import annotations

import logging
from time import time
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.observability.metrics import CACHE_LOOKUPS
from nebula.services.embeddings_service import OllamaEmbeddingsService

logger = logging.getLogger(__name__)


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
        try:
            exists = await self.client.collection_exists(self.settings.semantic_cache_collection)
            if not exists:
                await self.client.create_collection(
                    collection_name=self.settings.semantic_cache_collection,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.settings.embedding_dimensions,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
            self.enabled = True
            self.degraded_reason = None
        except Exception as exc:
            logger.warning("semantic_cache_disabled: %s", exc)
            self.enabled = False
            self.degraded_reason = str(exc)

    async def lookup(self, prompt: str) -> str | None:
        if not self.enabled:
            CACHE_LOOKUPS.labels("disabled").inc()
            return None

        vector = await self.embeddings_service.embed(prompt)
        if vector is None:
            CACHE_LOOKUPS.labels("embedding_unavailable").inc()
            return None

        try:
            results = await self.client.query_points(
                collection_name=self.settings.semantic_cache_collection,
                query=vector,
                limit=1,
                score_threshold=self.settings.semantic_cache_threshold,
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

        CACHE_LOOKUPS.labels("hit").inc()
        payload = points[0].payload or {}
        return payload.get("response")

    async def store(self, prompt: str, response: str, model: str) -> None:
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
            return {
                "status": "degraded",
                "required": False,
                "detail": f"Qdrant unavailable: {exc}",
                "enabled": self.enabled,
            }
        if exists:
            return {
                "status": "ready",
                "required": False,
                "detail": "Semantic cache collection is reachable.",
                "enabled": self.enabled,
            }
        return {
            "status": "degraded",
            "required": False,
            "detail": self.degraded_reason or "Semantic cache collection is missing.",
            "enabled": self.enabled,
        }
