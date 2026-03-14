from nebula.providers.base import CompletionProvider


class ProviderRegistry:
    def __init__(
        self,
        local_provider: CompletionProvider,
        premium_provider: CompletionProvider,
    ) -> None:
        self.local_provider = local_provider
        self.premium_provider = premium_provider

    def get(self, target: str) -> CompletionProvider:
        if target == "local":
            return self.local_provider
        return self.premium_provider

    async def close(self) -> None:
        await self.local_provider.close()
        await self.premium_provider.close()
