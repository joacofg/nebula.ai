from pathlib import Path

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.db.session import create_session_factory
from nebula.providers.mock_premium import MockPremiumProvider
from nebula.providers.ollama import OllamaProvider
from nebula.providers.openai_compatible import OpenAICompatibleProvider
from nebula.services.auth_service import AuthService
from nebula.services.chat_service import ChatService
from nebula.services.embeddings_service import OllamaEmbeddingsService
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyService
from nebula.services.premium_provider_health_service import PremiumProviderHealthService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouterService
from nebula.services.runtime_health_service import RuntimeHealthService
from nebula.services.semantic_cache_service import SemanticCacheService


class ServiceContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        pricing_path = Path(__file__).resolve().parents[3] / "benchmarks" / "pricing.json"
        self.pricing_catalog = PricingCatalog.from_path(pricing_path)
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
        self.router_service = RouterService(settings)
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
        )
        self.runtime_health_service = RuntimeHealthService(
            settings=settings,
            governance_store=self.governance_store,
            semantic_cache=self.cache_service,
            embeddings_service=self.embeddings_service,
            premium_provider_health=self.premium_provider_health_service,
        )
        self.chat_service = ChatService(
            settings=settings,
            cache_service=self.cache_service,
            router_service=self.router_service,
            provider_registry=self.provider_registry,
            governance_store=self.governance_store,
            policy_service=self.policy_service,
        )

    async def initialize(self) -> None:
        self.governance_store.initialize()
        await self.cache_service.initialize()

    async def shutdown(self) -> None:
        await self.provider_registry.close()
        await self.premium_provider_health_service.close()
        await self.embeddings_service.close()
        await self.cache_service.close()
        self.governance_store.close()

    def _build_premium_provider(self):
        if self.settings.premium_provider == "openai_compatible":
            return OpenAICompatibleProvider(self.settings)
        return MockPremiumProvider(self.settings)
