from __future__ import annotations

from nebula.core.config import Settings
from nebula.services.embeddings_service import OllamaEmbeddingsService
from nebula.services.governance_store import GovernanceStore
from nebula.services.premium_provider_health_service import PremiumProviderHealthService
from nebula.services.retention_lifecycle_service import RetentionLifecycleService
from nebula.services.semantic_cache_service import SemanticCacheService


class RuntimeHealthService:
    def __init__(
        self,
        settings: Settings,
        governance_store: GovernanceStore,
        semantic_cache: SemanticCacheService,
        embeddings_service: OllamaEmbeddingsService,
        premium_provider_health: PremiumProviderHealthService,
        retention_lifecycle: RetentionLifecycleService,
    ) -> None:
        self.settings = settings
        self.governance_store = governance_store
        self.semantic_cache = semantic_cache
        self.embeddings_service = embeddings_service
        self.premium_provider_health = premium_provider_health
        self.retention_lifecycle = retention_lifecycle

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
            "premium_provider": await self.premium_provider_health.health_status(),
            "retention_lifecycle": await self.retention_lifecycle.health_status(),
        }

    def _overall_status(self, dependencies: dict[str, dict[str, object]]) -> str:
        has_degradation = False
        for payload in dependencies.values():
            status = str(payload.get("lifecycle_state") or payload.get("status") or "not_ready")
            dependency_class = payload.get("dependency_class")
            serving_effect = payload.get("serving_effect")
            required = bool(payload.get("required", False))

            if self._is_serving_critical_failure(
                status=status,
                dependency_class=dependency_class,
                serving_effect=serving_effect,
                required=required,
            ):
                return "not_ready"
            if status in {"degraded", "recovering"}:
                has_degradation = True

        if has_degradation:
            return "degraded"
        return "ready"

    @staticmethod
    def _is_serving_critical_failure(
        *,
        status: str,
        dependency_class: object,
        serving_effect: object,
        required: bool,
    ) -> bool:
        if status == "ready":
            return False
        if dependency_class == "serving_critical":
            return True
        if serving_effect == "fail_closed":
            return True
        return required
