import asyncio

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionProvider, CompletionResult


class MockPremiumProvider(CompletionProvider):
    name = "mock-premium"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        prompt = self._extract_prompt(request)
        content = (
            "Mock premium response. Configura NEBULA_PREMIUM_PROVIDER=openai_compatible "
            f"para conectar un proveedor real. prompt={prompt}"
        )
        return CompletionResult(
            content=content,
            model=self.settings.premium_model,
            provider=self.name,
        )

    def stream_complete(self, request: ChatCompletionRequest):
        prompt = self._extract_prompt(request)
        text = (
            "Mock premium streaming response. Configura NEBULA_PREMIUM_PROVIDER="
            f"openai_compatible para usar OpenAI u OpenRouter. prompt={prompt}"
        )

        async def iterator():
            for token in text.split():
                yield CompletionChunk(delta=f"{token} ", model=self.settings.premium_model)
                await asyncio.sleep(0)
            yield CompletionChunk(
                delta="",
                model=self.settings.premium_model,
                finish_reason="stop",
            )

        return iterator()

    async def close(self) -> None:
        return None

    def _extract_prompt(self, request: ChatCompletionRequest) -> str:
        for message in reversed(request.messages):
            if message.role == "user":
                if isinstance(message.content, str):
                    return message.content
                return str(message.content)
        return ""
