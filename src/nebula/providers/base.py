from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol

import httpx

from nebula.models.openai import ChatCompletionRequest

_ERROR_BODY_LIMIT = 300


class ProviderError(Exception):
    """Raised when a downstream provider fails."""


def describe_http_error(exc: httpx.HTTPError) -> str:
    """Keep the upstream status and the start of its body, which httpx drops from its message.

    For a streamed response the caller must `aread()` the body before describing the error.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:_ERROR_BODY_LIMIT]}"
    return str(exc)


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
    # Token counts the provider reported: on the finish chunk or on a usage-only chunk (empty
    # delta, no finish_reason) that follows it.
    usage: CompletionUsage | None = None


class CompletionProvider(Protocol):
    name: str

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        ...

    def stream_complete(self, request: ChatCompletionRequest) -> AsyncIterator[CompletionChunk]:
        ...

    async def close(self) -> None:
        ...
