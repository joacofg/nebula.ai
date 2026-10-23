import logging
from pathlib import Path

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings, same_embedding_model
from nebula.db.session import create_session_factory
from nebula.providers.mock_premium import MockPremiumProvider
from nebula.providers.ollama import OllamaProvider
from nebula.providers.openai_compatible import OpenAICompatibleProvider
from nebula.services.auth_service import AuthService
from nebula.services.chat_service import ChatService
from nebula.services.embeddings_service import (
    REQUEST_PATH_EMBED_TIMEOUT_SECONDS,
    OllamaEmbeddingsService,
)
from nebula.services.governance_store import GovernanceStore
from nebula.services.learned_router import LearnedRouterModel
from nebula.services.policy_service import PolicyService
from nebula.services.policy_simulation_service import PolicySimulationService
from nebula.services.premium_provider_health_service import PremiumProviderHealthService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.recommendation_service import RecommendationService
from nebula.services.retention_lifecycle_service import RetentionLifecycleService
from nebula.services.router_service import RouterService
from nebula.services.runtime_health_service import RuntimeHealthService
from nebula.services.semantic_cache_service import SemanticCacheService
from nebula.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ServiceContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        pricing_path = Path(__file__).resolve().parents[3] / "benchmarks" / "pricing.json"
        self.pricing_catalog = PricingCatalog.from_path(pricing_path)
        self.rate_limiter = RateLimiter()
        self.governance_store = GovernanceStore(
            settings=settings,
            session_factory=create_session_factory(settings),
        )
        self.auth_service = AuthService(settings, self.governance_store)
        self.policy_service = PolicyService(
            settings=settings,
            store=self.governance_store,
            pricing=self.pricing_catalog,
        )
        self.router_service = RouterService(settings, learned=self._load_learned_router())
        self.policy_simulation_service = PolicySimulationService(
            governance_store=self.governance_store,
            router_service=self.router_service,
            policy_service=self.policy_service,
        )
        self.embeddings_service = OllamaEmbeddingsService(settings)
        self.local_provider = OllamaProvider(settings)
        self.premium_provider = self._build_premium_provider()
        self.premium_provider_health_service = PremiumProviderHealthService(settings)
        self.provider_registry = ProviderRegistry(
            local_provider=self.local_provider,
            premium_provider=self.premium_provider,
        )
        self.cache_service = SemanticCacheService(
            settings=settings,
            embeddings_service=self.embeddings_service,
            embed_timeout=REQUEST_PATH_EMBED_TIMEOUT_SECONDS,
        )
        self.recommendation_service = RecommendationService(
            governance_store=self.governance_store,
            semantic_cache_service=self.cache_service,
        )
        self.retention_lifecycle_service = RetentionLifecycleService(
            enabled=settings.retention_cleanup_enabled,
            interval_seconds=settings.retention_cleanup_interval_seconds,
            governance_store=self.governance_store,
            semantic_cache=self.cache_service,
        )
        self.runtime_health_service = RuntimeHealthService(
            settings=settings,
            governance_store=self.governance_store,
            semantic_cache=self.cache_service,
            embeddings_service=self.embeddings_service,
            premium_provider_health=self.premium_provider_health_service,
            retention_lifecycle=self.retention_lifecycle_service,
        )
        self.chat_service = ChatService(
            settings=settings,
            cache_service=self.cache_service,
            router_service=self.router_service,
            provider_registry=self.provider_registry,
            governance_store=self.governance_store,
            policy_service=self.policy_service,
            embeddings_service=self.embeddings_service,
        )

    async def initialize(self) -> None:
        self.governance_store.initialize()
        await self.cache_service.initialize()

    async def shutdown(self) -> None:
        await self.retention_lifecycle_service.stop()
        await self.provider_registry.close()
        await self.premium_provider_health_service.close()
        await self.embeddings_service.close()
        await self.cache_service.close()
        self.governance_store.close()

    def _load_learned_router(self) -> LearnedRouterModel | None:
        if not self.settings.learned_router_enabled:
            return None
        # Enabled but missing or invalid is a deployment error: fail at startup, not per request.
        learned = LearnedRouterModel.from_file(self.settings.learned_router_path)
        if not same_embedding_model(learned.embedding_model, self.settings.embedding_model):
            # Trained on another model's vectors, it would score this model's as noise. The
            # gateway still serves, with heuristic routing, so the error is logged, not raised.
            logger.error(
                "learned_router_disabled: artifact %s was trained on embedding model %r, "
                "but NEBULA_EMBEDDING_MODEL is %r; routing falls back to the heuristic",
                self.settings.learned_router_path,
                learned.embedding_model,
                self.settings.embedding_model,
            )
            return None
        return learned

    def _build_premium_provider(self):
        if self.settings.premium_provider == "openai_compatible":
            return OpenAICompatibleProvider(self.settings)
        return MockPremiumProvider(self.settings)
