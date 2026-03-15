from __future__ import annotations

from nebula.core.config import Settings
from nebula.services.embeddings_service import OllamaEmbeddingsService
from nebula.services.governance_store import GovernanceStore
from nebula.services.semantic_cache_service import SemanticCacheService


class RuntimeHealthService:
    def __init__(
        self,
        settings: Settings,
        governance_store: GovernanceStore,
        semantic_cache: SemanticCacheService,
        embeddings_service: OllamaEmbeddingsService,
    ) -> None:
        self.settings = settings
        self.governance_store = governance_store
        self.semantic_cache = semantic_cache
        self.embeddings_service = embeddings_service

    async def readiness(self) -> dict[str, object]:
        dependencies = await self.dependencies()
        status = self._overall_status(dependencies)
        return {
            "status": status,
            "runtime_profile": self.settings.runtime_profile,
            "dependencies": dependencies,
        }

    async def dependencies(self) -> dict[str, dict[str, object]]:
        return {
            "gateway": {
                "status": "ready",
                "required": True,
                "detail": "FastAPI application is running.",
            },
            "governance_store": self.governance_store.health_status(),
            "semantic_cache": await self.semantic_cache.health_status(),
            "local_ollama": await self.embeddings_service.health_status(),
        }

    def _overall_status(self, dependencies: dict[str, dict[str, object]]) -> str:
        required_failures = [
            component
            for component, payload in dependencies.items()
            if payload["required"] and payload["status"] != "ready"
        ]
        if required_failures:
            return "not_ready"
        degraded_optional = [
            component for component, payload in dependencies.items() if payload["status"] == "degraded"
        ]
        if degraded_optional:
            return "degraded"
        return "ready"
