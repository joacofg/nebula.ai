from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
from uuid import uuid4

from nebula.core.config import get_settings
from nebula.main import create_app
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionResult, CompletionUsage, ProviderError


@contextmanager
def configured_app(**env_overrides: str) -> Iterator:
    temp_dir = TemporaryDirectory()
    default_overrides = {
        "NEBULA_DATA_STORE_PATH": str(Path(temp_dir.name) / "nebula.db"),
        "NEBULA_SEMANTIC_CACHE_COLLECTION": f"nebula-test-cache-{uuid4().hex}",
    }
    merged_overrides = {**default_overrides, **env_overrides}
    original_values = {key: os.environ.get(key) for key in merged_overrides}
    for key, value in merged_overrides.items():
        os.environ[key] = value
    get_settings.cache_clear()
    app = create_app()
    try:
        yield app
    finally:
        for key, value in original_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()
        temp_dir.cleanup()


def auth_headers(
    api_key: str = "nebula-dev-key",
    tenant_id: str = "default",
) -> dict[str, str]:
    return {
        "X-Nebula-API-Key": api_key,
        "X-Nebula-Tenant-ID": tenant_id,
    }


def admin_headers(admin_api_key: str = "nebula-admin-key") -> dict[str, str]:
    return {"X-Nebula-Admin-Key": admin_api_key}


class FakeCacheService:
    def __init__(self, cached_response: str | None = None) -> None:
        self.cached_response = cached_response
        self.lookup_calls: list[str] = []
        self.stored_entries: list[tuple[str, str, str]] = []
        self.enabled = True

    async def initialize(self) -> None:
        return None

    async def lookup(self, prompt: str) -> str | None:
        self.lookup_calls.append(prompt)
        return self.cached_response

    async def store(self, prompt: str, response: str, model: str) -> None:
        self.stored_entries.append((prompt, response, model))

    async def close(self) -> None:
        return None


class StubProvider:
    def __init__(
        self,
        name: str,
        *,
        completion_result: CompletionResult | None = None,
        completion_error: Exception | None = None,
        stream_chunks: list[CompletionChunk] | None = None,
        stream_error: Exception | None = None,
    ) -> None:
        self.name = name
        self.completion_result = completion_result
        self.completion_error = completion_error
        self.stream_chunks = stream_chunks or []
        self.stream_error = stream_error

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        if self.completion_error is not None:
            raise self.completion_error
        assert self.completion_result is not None
        return self.completion_result

    def stream_complete(self, request: ChatCompletionRequest):
        async def iterator():
            if self.stream_error is not None:
                raise self.stream_error
            for chunk in self.stream_chunks:
                yield chunk

        return iterator()

    async def close(self) -> None:
        return None


def usage(prompt_tokens: int = 8, completion_tokens: int = 4) -> CompletionUsage:
    return CompletionUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


def provider_error(message: str) -> ProviderError:
    return ProviderError(message)
