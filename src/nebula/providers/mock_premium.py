import asyncio

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import (
    CompletionChunk,
    CompletionProvider,
    CompletionResult,
    CompletionUsage,
)


def _approximate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class MockPremiumProvider(CompletionProvider):
    name = "mock-premium"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        prompt = self._extract_prompt(request)
        content = (
            "Mock premium response. Set NEBULA_PREMIUM_PROVIDER=openai_compatible "
            f"to connect a real provider. prompt={prompt}"
        )
        return CompletionResult(
            content=content,
            model=self.settings.premium_model,
            provider=self.name,
        )

    def stream_complete(self, request: ChatCompletionRequest):
        prompt = self._extract_prompt(request)
        text = (
            "Mock premium streaming response. Set NEBULA_PREMIUM_PROVIDER="
            f"openai_compatible to use OpenAI or OpenRouter. prompt={prompt}"
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
            # Like a real provider with include_usage: the counts arrive after the finish.
            prompt_tokens = _approximate_tokens(prompt)
            completion_tokens = _approximate_tokens(text)
            yield CompletionChunk(
                delta="",
                model=self.settings.premium_model,
                usage=CompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                ),
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
