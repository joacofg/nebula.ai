from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from collections.abc import Callable
from typing import Iterator
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from nebula.core.config import get_settings
from nebula.core.container import ServiceContainer
from nebula.main import create_app
from nebula.models.resilience import build_dependency_health
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionChunk, CompletionResult, CompletionUsage, ProviderError
from nebula.services.semantic_cache_service import CacheHit


def _drop_cache_collection(name: str) -> None:
    """Remove a test's Qdrant collection, if Qdrant is even there.

    Tests must pass on a machine with no Qdrant running, so a failure here is
    swallowed on purpose — the collection cannot exist if the connection does
    not.
    """
    try:
        from qdrant_client import QdrantClient

        # check_compatibility=False: this client only issues a DELETE, and the
        # client/server version skew is a pre-existing property of the dev
        # environment. Warning about it once per test buries the output.
        client = QdrantClient(
            url=get_settings().qdrant_url, timeout=2, check_compatibility=False
        )
        try:
            client.delete_collection(collection_name=name)
        finally:
            client.close()
    except Exception:  # noqa: BLE001 - no Qdrant, nothing to clean
        pass


@contextmanager
def configured_app(
    _collection_reaper: Callable[[str], None] = _drop_cache_collection,
    **env_overrides: str,
) -> Iterator:
    temp_dir = TemporaryDirectory()
    database_path = Path(temp_dir.name) / "nebula.db"
    default_overrides = {
        "NEBULA_DATA_STORE_PATH": str(database_path),
        "NEBULA_DATABASE_URL": f"sqlite+pysqlite:///{database_path}",
        "NEBULA_SEMANTIC_CACHE_COLLECTION": f"nebula-test-cache-{uuid4().hex}",
    }
    merged_overrides = {**default_overrides, **env_overrides}
    original_values = {key: os.environ.get(key) for key in merged_overrides}
    for key, value in merged_overrides.items():
        os.environ[key] = value
    get_settings.cache_clear()
    _run_migrations(os.environ["NEBULA_DATABASE_URL"])
    app = create_app()
    try:
        yield app
    finally:
        # Drop the collection before restoring the environment: the reaper
        # reads qdrant_url out of settings, and settings are about to be
        # rebuilt from the outer environment.
        _collection_reaper(os.environ["NEBULA_SEMANTIC_CACHE_COLLECTION"])
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
    def __init__(
        self,
        cached_response: str | None = None,
        *,
        health_status_payload: dict[str, object] | None = None,
        lookup_error: Exception | None = None,
        store_error: Exception | None = None,
    ) -> None:
        self.cached_response = cached_response
        # (tenant_id, prompt, similarity_threshold, max_entry_age_hours); identity filters ignored.
        self.lookup_calls: list[tuple[str, str, float, int]] = []
        # (tenant_id, response, model, tier_rank)
        self.stored_entries: list[tuple[str, str, str, int]] = []
        self.enabled = True
        self.lookup_error = lookup_error
        self.store_error = store_error
        self.health_status_payload = health_status_payload or build_dependency_health(
            dependency_class="serving_optional",
            lifecycle_state="ready",
            serving_effect="continuity_limited",
            reason_code="semantic_cache_ready",
            detail="Semantic cache collection is reachable.",
            required=False,
            extra={"enabled": True},
        )

    async def initialize(self) -> None:
        return None

    async def lookup(
        self,
        prompt: str,
        *,
        tenant_id: str,
        similarity_threshold: float,
        max_entry_age_hours: int,
        context_hash: str,
        min_tier_rank: int | None,
        model: str | None,
        vector: list[float] | None = None,
    ) -> CacheHit | None:
        self.lookup_calls.append((tenant_id, prompt, similarity_threshold, max_entry_age_hours))
        if self.lookup_error is not None:
            raise self.lookup_error
        if self.cached_response is None:
            return None
        return CacheHit(response=self.cached_response, model="nebula-cache", score=1.0, age_seconds=0)

    async def store(
        self,
        response: str,
        *,
        tenant_id: str,
        vector: list[float] | None,
        context_hash: str,
        tier_rank: int,
        model: str,
    ) -> None:
        if self.store_error is not None:
            raise self.store_error
        self.stored_entries.append((tenant_id, response, model, tier_rank))

    async def close(self) -> None:
        return None

    async def health_status(self) -> dict[str, object]:
        return self.health_status_payload


class FixedVectorEmbeddings:
    """Embeds every text to the same vector, recording each call; never leaves the process."""

    def __init__(self, vector: list[float] | None = None) -> None:
        self.vector = vector or [1.0, 0.0, 0.0]
        self.calls: list[str] = []

    async def embed(self, text: str) -> list[float] | None:
        self.calls.append(text)
        return list(self.vector)

    async def close(self) -> None:
        return None


def use_fake_cache(
    container: ServiceContainer, cache: FakeCacheService | None = None
) -> FakeCacheService:
    """Serve the chat path from a fake cache, with embeddings that never reach Ollama.

    The chat path embeds each cache-enabled request itself (once, for lookup and store), so
    swapping in a fake cache alone would still send every prompt to the real embeddings service.
    """
    cache = cache if cache is not None else FakeCacheService()
    container.cache_service = cache
    container.chat_service.cache_service = cache
    container.chat_service.embeddings_service = FixedVectorEmbeddings()
    return cache


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
        # Every request this provider was asked to serve, streaming or not.
        self.requests: list[ChatCompletionRequest] = []

    async def complete(self, request: ChatCompletionRequest) -> CompletionResult:
        self.requests.append(request)
        if self.completion_error is not None:
            raise self.completion_error
        assert self.completion_result is not None
        return self.completion_result

    def stream_complete(self, request: ChatCompletionRequest):
        self.requests.append(request)

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


class StubEmbeddingsResult:
    def __init__(self, *, model: str, vectors: list[list[float]]) -> None:
        self.model = model
        self.data = [
            type("EmbeddingVector", (), {"index": index, "embedding": vector})
            for index, vector in enumerate(vectors)
        ]


class StubEmbeddingsService:
    def __init__(self, *, result: StubEmbeddingsResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def create_embeddings(self, *, model: str, input: str | list[str]):
        self.calls.append({"model": model, "input": input})
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result

    async def close(self) -> None:
        return None


@contextmanager
def fallback_client(
    **policy_updates: object,
) -> Iterator[tuple[TestClient, ServiceContainer, StubProvider]]:
    """A gateway whose local provider is down and whose premium provider records its calls."""
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            container: ServiceContainer = app.state.container
            settings = container.settings
            local = StubProvider(
                "ollama",
                completion_error=provider_error("ollama down"),
                stream_error=provider_error("ollama down"),
            )
            premium = StubProvider(
                "mock-premium",
                completion_result=CompletionResult(
                    content="premium answer",
                    model=settings.premium_model,
                    provider="mock-premium",
                    usage=usage(),
                ),
                stream_chunks=[
                    CompletionChunk(delta="premium answer", model=settings.premium_model),
                    CompletionChunk(delta="", model=settings.premium_model, finish_reason="stop"),
                ],
            )
            container.local_provider = local
            container.provider_registry.local_provider = local
            container.premium_provider = premium
            container.provider_registry.premium_provider = premium
            use_fake_cache(container)
            if policy_updates:
                store = container.governance_store
                store.upsert_policy(
                    "default", store.get_policy("default").model_copy(update=policy_updates)
                )
            yield client, container, premium


def _run_migrations(database_url: str) -> None:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
