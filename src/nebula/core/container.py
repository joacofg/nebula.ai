from nebula.core.config import Settings
from nebula.providers.mock_premium import MockPremiumProvider
from nebula.providers.ollama import OllamaProvider
from nebula.providers.openai_compatible import OpenAICompatibleProvider
from nebula.services.chat_service import ChatService
from nebula.services.embeddings_service import OllamaEmbeddingsService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouterService
from nebula.services.semantic_cache_service import SemanticCacheService


class ServiceContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router_service = RouterService(settings)
        self.embeddings_service = OllamaEmbeddingsService(settings)
        self.local_provider = OllamaProvider(settings)
        self.premium_provider = self._build_premium_provider()
        self.provider_registry = ProviderRegistry(
            local_provider=self.local_provider,
            premium_provider=self.premium_provider,
        )
        self.cache_service = SemanticCacheService(
            settings=settings,
            embeddings_service=self.embeddings_service,
        )
        self.chat_service = ChatService(
            settings=settings,
            cache_service=self.cache_service,
            router_service=self.router_service,
            provider_registry=self.provider_registry,
        )

    async def initialize(self) -> None:
        await self.cache_service.initialize()

    async def shutdown(self) -> None:
        await self.provider_registry.close()
        await self.embeddings_service.close()
        await self.cache_service.close()

    def _build_premium_provider(self):
        if self.settings.premium_provider == "openai_compatible":
            return OpenAICompatibleProvider(self.settings)
        return MockPremiumProvider(self.settings)
