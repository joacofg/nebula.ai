from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from nebula.models.openai import ChatCompletionRequest


class ProviderError(Exception):
    """Raised when a downstream provider fails."""


@dataclass(slots=True)
class CompletionUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class CompletionResult:
    content: str
    model: str
    provider: str
    finish_reason: str = "stop"
    usage: CompletionUsage | None = None


@dataclass(slots=True)
class CompletionChunk:
    delta: str
    model: str
    finish_reason: str | None = None


class CompletionProvider(Protocol):
    name: str

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        ...

    def stream_complete(self, request: ChatCompletionRequest) -> AsyncIterator[CompletionChunk]:
        ...

    async def close(self) -> None:
        ...
