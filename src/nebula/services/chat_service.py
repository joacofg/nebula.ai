from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter, time
from typing import Any, AsyncIterator, Literal, NoReturn
from uuid import uuid4

from fastapi import HTTPException, status
from starlette.concurrency import run_in_threadpool

from nebula.core.config import Settings
from nebula.models.governance import TerminalStatus, UsageLedgerRecord
from nebula.models.openai import (
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    ChatCompletionStreamDelta,
    ChatCompletionUsage,
    FinishReason,
    normalize_finish_reason,
)
from nebula.observability.metrics import (
    CACHE_LOOKUPS,
    COMPLETION_COUNT,
    FALLBACK_COUNT,
    PROVIDER_LATENCY,
    ROUTE_DECISION_COUNT,
)
from nebula.providers.base import CompletionProvider, CompletionUsage, ProviderError
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.embeddings_service import (
    REQUEST_PATH_EMBED_TIMEOUT_SECONDS,
    OllamaEmbeddingsService,
)
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyResolution, PolicyService, SpendDenial
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouteDecision, RouteTarget, RouterService
from nebula.services.semantic_cache_service import (
    TIER_RANK,
    UNTIERED_RANK,
    CacheHit,
    SemanticCacheService,
    context_hash,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class _CacheKey:
    """A request's cache identity, computed once and shared by its lookup and its store."""

    tenant_id: str
    context_hash: str
    # None when the cache is disabled (it answers nothing), or when this service has no
    # embeddings service (the cache then embeds its lookups itself and cannot store).
    vector: list[float] | None
    # Exactly one is set: an auto request takes answers from its chosen tier up, an
    # explicit-model request only that model's answers.
    min_tier_rank: int | None
    model: str | None


@dataclass(slots=True, frozen=True)
class _CacheWrite:
    """Where a served answer is cached: the request's key, and the tier and model that served it."""

    key: _CacheKey
    tier_rank: int
    model: str


@dataclass(slots=True)
class _StreamUsage:
    """The usage a provider reported for one stream.

    The ledger wrapper owns it and hands it down to `_stream_provider`, which fills it when the
    provider's usage chunk arrives. It stays None for providers that report none.
    """

    usage: CompletionUsage | None = None


@dataclass(slots=True)
class CompletionMetadata:
    tenant_id: str
    route_target: Literal["local", "premium", "cache", "denied"]
    route_reason: str
    provider: str
    cache_hit: bool
    fallback_used: bool
    policy_mode: str
    policy_outcome: str
    route_signals: dict[str, Any] | None = None
    route_score: float = 0.0
    # local / economy / frontier / cache / denied: which tier actually served the request.
    route_tier: str = "frontier"


@dataclass(slots=True)
class CompletionResponseEnvelope:
    response: ChatCompletionResponse
    metadata: CompletionMetadata


@dataclass(slots=True)
class StreamingCompletionEnvelope:
    stream: AsyncIterator[bytes]
    metadata: CompletionMetadata


class ChatService:
    def __init__(
        self,
        settings: Settings,
        cache_service: SemanticCacheService,
        router_service: RouterService,
        provider_registry: ProviderRegistry,
        governance_store: GovernanceStore,
        policy_service: PolicyService,
        embeddings_service: OllamaEmbeddingsService | None = None,
    ) -> None:
        self.settings = settings
        self.cache_service = cache_service
        self.router_service = router_service
        self.provider_registry = provider_registry
        self.governance_store = governance_store
        self.policy_service = policy_service
        self.embeddings_service = embeddings_service

    async def create_completion_with_metadata(
        self,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None = None,
    ) -> CompletionResponseEnvelope:
        started_at = perf_counter()
        latest_user_prompt = self._extract_latest_user_prompt(request)
        routing_embedding = await self._embed_for_routing(latest_user_prompt)
        policy_resolution = await self._resolve_policy(
            request=request,
            prompt=latest_user_prompt,
            tenant_context=tenant_context,
            request_id=request_id,
            prompt_embedding=routing_embedding,
        )

        cache_key = await self._cache_key(
            request=request,
            prompt=latest_user_prompt,
            tenant_id=tenant_context.tenant.id,
            routing_embedding=routing_embedding,
            policy_resolution=policy_resolution,
            request_id=request_id,
            stream=False,
        )
        cache_hit = await self._lookup_cache(
            key=cache_key,
            prompt=latest_user_prompt,
            policy_resolution=policy_resolution,
            request_id=request_id,
            stream=False,
        )
        if cache_hit is not None:
            cached_response = cache_hit.response
            usage = self.policy_service.estimate_usage(request, cached_response)
            metadata = self._metadata(
                tenant_id=tenant_context.tenant.id,
                route_target="cache",
                route_reason="cache_hit",
                provider="cache",
                cache_hit=cache_hit,
                fallback_used=False,
                policy_resolution=policy_resolution,
                avoided_cost_usd=self._cache_avoided_cost(request, policy_resolution, usage),
            )
            response = self._build_response(content=cached_response, model="nebula-cache", usage=usage)
            await self._record_usage(
                request_id=request_id,
                tenant_id=tenant_context.tenant.id,
                request=request,
                metadata=metadata,
                response_model=response.model,
                usage=usage,
                latency_ms=(perf_counter() - started_at) * 1000,
                terminal_status="cache_hit",
            )
            COMPLETION_COUNT.labels("cache", "ok", "false").inc()
            return CompletionResponseEnvelope(response=response, metadata=metadata)
        if policy_resolution.spend_denial is not None:
            # A cached answer would have cost nothing; with none, the guardrail denies.
            await self._deny_spend(
                request=request,
                tenant_id=tenant_context.tenant.id,
                request_id=request_id,
                denial=policy_resolution.spend_denial,
            )

        route_decision = policy_resolution.route_decision
        ROUTE_DECISION_COUNT.labels(route_decision.target, route_decision.reason, "false").inc()
        logger.info(
            "route_selected request_id=%s tenant_id=%s stream=false target=%s reason=%s policy=%s",
            request_id,
            tenant_context.tenant.id,
            route_decision.target,
            route_decision.reason,
            policy_resolution.policy_outcome,
        )
        provider = self.provider_registry.get(route_decision.target)
        try:
            result = await self._complete_with_provider(
                provider,
                self._provider_request(request, route_decision.model),
                request_id,
                tenant_context.tenant.id,
            )
            COMPLETION_COUNT.labels(provider.name, "ok", "false").inc()
            metadata = self._metadata(
                tenant_id=tenant_context.tenant.id,
                route_target=route_decision.target,
                route_reason=route_decision.reason,
                provider=provider.name,
                cache_hit=False,
                fallback_used=False,
                policy_resolution=policy_resolution,
            )
            served_model = self._served_model(request, route_decision)
            terminal_status = "completed"
        except ProviderError as exc:
            logger.warning(
                "provider_failed request_id=%s tenant_id=%s provider=%s error=%s",
                request_id,
                tenant_context.tenant.id,
                provider.name,
                exc,
            )
            fallback_model = await self._fallback_model_or_fail(
                request=request,
                request_id=request_id,
                tenant_id=tenant_context.tenant.id,
                resolution=policy_resolution,
                provider_name=provider.name,
                started_at=started_at,
                cause=exc,
                stream=False,
            )

            fallback_provider = self.provider_registry.get("premium")
            FALLBACK_COUNT.labels("local_provider_error").inc()
            logger.info(
                "fallback_selected request_id=%s tenant_id=%s stream=false provider=%s",
                request_id,
                tenant_context.tenant.id,
                fallback_provider.name,
            )
            try:
                result = await self._complete_with_provider(
                    fallback_provider,
                    self._provider_request(request, fallback_model),
                    request_id,
                    tenant_context.tenant.id,
                )
            except ProviderError as fallback_exc:
                await self._fail_fallback(
                    request=request,
                    request_id=request_id,
                    tenant_id=tenant_context.tenant.id,
                    resolution=policy_resolution,
                    provider_name=fallback_provider.name,
                    started_at=started_at,
                    cause=fallback_exc,
                    stream=False,
                )
            COMPLETION_COUNT.labels(fallback_provider.name, "fallback", "false").inc()
            metadata = self._metadata(
                tenant_id=tenant_context.tenant.id,
                route_target="premium",
                route_reason="local_provider_error_fallback",
                provider=fallback_provider.name,
                cache_hit=False,
                fallback_used=True,
                policy_resolution=policy_resolution,
            )
            served_model = fallback_model
            terminal_status = "fallback_completed"

        usage = self._resolved_usage(request, result.content, result.usage)
        await self._store_in_cache(self._cache_write(cache_key, served_model), result.content)
        response = self._build_response(
            content=result.content,
            model=result.model,
            usage=usage,
            finish_reason=result.finish_reason,
        )
        await self._record_usage(
            request_id=request_id,
            tenant_id=tenant_context.tenant.id,
            request=request,
            metadata=metadata,
            response_model=result.model,
            usage=usage,
            latency_ms=(perf_counter() - started_at) * 1000,
            terminal_status=terminal_status,
        )
        return CompletionResponseEnvelope(response=response, metadata=metadata)

    async def stream_completion_with_metadata(
        self,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None = None,
    ) -> StreamingCompletionEnvelope:
        started_at = perf_counter()
        latest_user_prompt = self._extract_latest_user_prompt(request)
        routing_embedding = await self._embed_for_routing(latest_user_prompt)
        policy_resolution = await self._resolve_policy(
            request=request,
            prompt=latest_user_prompt,
            tenant_context=tenant_context,
            request_id=request_id,
            prompt_embedding=routing_embedding,
        )
        response_id = f"chatcmpl-{uuid4().hex}"
        created = int(time())

        cache_key = await self._cache_key(
            request=request,
            prompt=latest_user_prompt,
            tenant_id=tenant_context.tenant.id,
            routing_embedding=routing_embedding,
            policy_resolution=policy_resolution,
            request_id=request_id,
            stream=True,
        )
        cache_hit = await self._lookup_cache(
            key=cache_key,
            prompt=latest_user_prompt,
            policy_resolution=policy_resolution,
            request_id=request_id,
            stream=True,
        )
        if cache_hit is not None:
            cached_response = cache_hit.response
            usage = self.policy_service.estimate_usage(request, cached_response)
            COMPLETION_COUNT.labels("cache", "ok", "true").inc()
            metadata = self._metadata(
                tenant_id=tenant_context.tenant.id,
                route_target="cache",
                route_reason="cache_hit",
                provider="cache",
                cache_hit=cache_hit,
                fallback_used=False,
                policy_resolution=policy_resolution,
                avoided_cost_usd=self._cache_avoided_cost(request, policy_resolution, usage),
            )
            wrapped_stream = self._wrap_stream_with_ledger(
                stream=self._stream_text(cached_response, response_id, created, "nebula-cache"),
                request=request,
                metadata=metadata,
                request_id=request_id,
                started_at=started_at,
            )
            return StreamingCompletionEnvelope(stream=wrapped_stream, metadata=metadata)
        if policy_resolution.spend_denial is not None:
            await self._deny_spend(
                request=request,
                tenant_id=tenant_context.tenant.id,
                request_id=request_id,
                denial=policy_resolution.spend_denial,
            )

        route_decision = policy_resolution.route_decision
        ROUTE_DECISION_COUNT.labels(route_decision.target, route_decision.reason, "true").inc()
        logger.info(
            "route_selected request_id=%s tenant_id=%s stream=true target=%s reason=%s policy=%s",
            request_id,
            tenant_context.tenant.id,
            route_decision.target,
            route_decision.reason,
            policy_resolution.policy_outcome,
        )
        provider = self.provider_registry.get(route_decision.target)
        stream_usage = _StreamUsage()
        stream, metadata = await self._prepare_stream_provider(
            provider=provider,
            request=request,
            response_id=response_id,
            created=created,
            request_id=request_id,
            tenant_id=tenant_context.tenant.id,
            policy_resolution=policy_resolution,
            started_at=started_at,
            cache_key=cache_key,
            stream_usage=stream_usage,
        )

        wrapped_stream = self._wrap_stream_with_ledger(
            stream=stream,
            request=request,
            metadata=metadata,
            request_id=request_id,
            started_at=started_at,
            stream_usage=stream_usage,
        )
        return StreamingCompletionEnvelope(stream=wrapped_stream, metadata=metadata)

    def _extract_latest_user_prompt(self, request: ChatCompletionRequest) -> str:
        for message in reversed(request.messages):
            if message.role == "user":
                if isinstance(message.content, str):
                    return message.content
                return str(message.content)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one user message is required.",
        )

    def _build_response(
        self,
        content: str,
        model: str,
        usage: CompletionUsage | None,
        finish_reason: str | None = None,
    ) -> ChatCompletionResponse:
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid4().hex}",
            created=int(time()),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionResponseMessage(content=content),
                    finish_reason=normalize_finish_reason(finish_reason),
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
        )

    async def _cache_key(
        self,
        *,
        request: ChatCompletionRequest,
        prompt: str,
        tenant_id: str,
        routing_embedding: list[float] | None,
        policy_resolution: PolicyResolution,
        request_id: str | None,
        stream: bool,
    ) -> _CacheKey | None:
        """This request's cache identity, or None when the request skips the cache altogether."""
        if not policy_resolution.cache_enabled:
            logger.info("cache_bypassed request_id=%s stream=%s reason=policy_disabled", request_id, stream)
            return None
        vector: list[float] | None = None
        # A disabled cache answers nothing, so it needs no vector.
        if self.embeddings_service is not None and self.cache_service.enabled:
            learned = self.router_service.learned
            if learned is not None and learned.prefix == "none":
                # Routing already embedded the bare prompt; if that failed, a retry would too.
                vector = routing_embedding
            else:
                vector = await self._embed(prompt, purpose="cache")
            if vector is None:
                # Asking the cache anyway would only make it embed the prompt again.
                CACHE_LOOKUPS.labels("embedding_unavailable").inc()
                logger.info(
                    "cache_bypassed request_id=%s stream=%s reason=embedding_unavailable",
                    request_id,
                    stream,
                )
                return None
        route_decision = policy_resolution.route_decision
        if request.model != self.settings.default_model:
            # An explicit model (routed `explicit_local_model` / `explicit_premium_model`) asks
            # for that model's answer, not for a tier's.
            min_tier_rank, model = None, self._served_model(request, route_decision)
        else:
            chosen_tier = self._route_tier(
                route_target=route_decision.target,
                fallback_used=False,
                signals=route_decision.signals,
                policy_resolution=policy_resolution,
            )
            min_tier_rank, model = TIER_RANK[chosen_tier], None
        return _CacheKey(
            tenant_id=tenant_id,
            context_hash=context_hash(request.messages),
            vector=vector,
            min_tier_rank=min_tier_rank,
            model=model,
        )

    def _cache_write(self, key: _CacheKey | None, served_model: str) -> _CacheWrite | None:
        if key is None:
            return None
        # Ranked by the model that actually served, so a fallback answer is filed under the
        # fallback model's tier.
        return _CacheWrite(key=key, tier_rank=self._tier_rank_of(served_model), model=served_model)

    def _tier_rank_of(self, model: str) -> int:
        """The tier a model's answers can serve: only the configured tier models have one."""
        ranks = {self.settings.local_model: TIER_RANK["local"]}
        if self.settings.economy_model:
            ranks[self.settings.economy_model] = TIER_RANK["economy"]
        # Last, so a frontier model also configured as the economy model keeps frontier rank.
        ranks[self.settings.premium_model] = TIER_RANK["frontier"]
        return ranks.get(model, UNTIERED_RANK)

    async def _store_in_cache(self, write: _CacheWrite | None, response: str) -> None:
        if write is None:
            return
        await self.cache_service.store(
            response,
            tenant_id=write.key.tenant_id,
            vector=write.key.vector,
            context_hash=write.key.context_hash,
            tier_rank=write.tier_rank,
            model=write.model,
        )

    async def _lookup_cache(
        self,
        *,
        key: _CacheKey | None,
        prompt: str,
        policy_resolution: PolicyResolution,
        request_id: str | None,
        stream: bool,
    ) -> CacheHit | None:
        if key is None:
            return None
        try:
            hit = await self.cache_service.lookup(
                prompt,
                tenant_id=key.tenant_id,
                similarity_threshold=policy_resolution.cache_similarity_threshold,
                max_entry_age_hours=policy_resolution.cache_max_entry_age_hours,
                context_hash=key.context_hash,
                min_tier_rank=key.min_tier_rank,
                model=key.model,
                vector=key.vector,
            )
        except Exception as exc:  # noqa: BLE001 - the cache is optional: a failure is a miss
            # Never a 500: the request is served (or spend-denied with its usual 403) without it.
            CACHE_LOOKUPS.labels("error").inc()
            logger.warning(
                "cache_lookup_failed request_id=%s stream=%s error=%s",
                request_id,
                str(stream).lower(),
                exc,
            )
            return None
        if hit is not None:
            logger.info(
                "cache_hit request_id=%s stream=%s prompt_chars=%s score=%.4f age_seconds=%s",
                request_id,
                str(stream).lower(),
                len(prompt),
                hit.score,
                hit.age_seconds,
            )
        else:
            logger.info(
                "cache_miss request_id=%s stream=%s prompt_chars=%s",
                request_id,
                str(stream).lower(),
                len(prompt),
            )
        return hit

    async def _stream_provider(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        response_id: str,
        created: int,
        request_id: str | None,
        tenant_id: str,
        cache_write: _CacheWrite | None,
        stream_usage: _StreamUsage,
    ):
        content_parts: list[str] = []
        started_at = perf_counter()
        finished = False

        try:
            provider_chunks = provider.stream_complete(request)
            async for chunk in provider_chunks:
                if chunk.usage is not None:
                    stream_usage.usage = chunk.usage

                if finished:
                    # Keep reading only for the usage chunk the provider sends after the
                    # finish, and stop at it: an upstream that holds the connection open
                    # must not delay [DONE] or the ledger row.
                    if stream_usage.usage is not None:
                        break
                    continue

                if chunk.delta:
                    content_parts.append(chunk.delta)
                    yield self._sse(
                        ChatCompletionChunk(
                            id=response_id,
                            created=created,
                            model=chunk.model,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionStreamDelta(content=chunk.delta),
                                )
                            ],
                        )
                    )

                if chunk.finish_reason:
                    await self._store_in_cache(cache_write, "".join(content_parts))
                    COMPLETION_COUNT.labels(provider.name, "ok", "true").inc()
                    PROVIDER_LATENCY.labels(provider.name, "stream", "ok").observe(
                        perf_counter() - started_at
                    )
                    logger.info(
                        "provider_completed request_id=%s tenant_id=%s provider=%s mode=stream latency_ms=%.2f",
                        request_id,
                        tenant_id,
                        provider.name,
                        (perf_counter() - started_at) * 1000,
                    )
                    yield self._sse(
                        ChatCompletionChunk(
                            id=response_id,
                            created=created,
                            model=chunk.model,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionStreamDelta(),
                                    finish_reason=normalize_finish_reason(chunk.finish_reason),
                                )
                            ],
                        )
                    )
                    # Only now is a failure the provider's, not ours: the store and metrics
                    # above must still fail the stream as they did before the usage chunk.
                    finished = True
                    if stream_usage.usage is not None:
                        break
            if finished:
                # Release the upstream connection when we stopped before its iterator ended.
                aclose = getattr(provider_chunks, "aclose", None)
                if aclose is not None:
                    await aclose()
        except Exception as exc:
            if finished:
                # The answer is complete and already counted as ok: losing the connection
                # while waiting for the usage chunk costs only the exact token counts.
                logger.warning(
                    "stream_failed_after_finish request_id=%s tenant_id=%s provider=%s error=%s",
                    request_id,
                    tenant_id,
                    provider.name,
                    exc,
                )
            else:
                COMPLETION_COUNT.labels(provider.name, "error", "true").inc()
                PROVIDER_LATENCY.labels(provider.name, "stream", "error").observe(
                    perf_counter() - started_at
                )
                if isinstance(exc, ProviderError):
                    raise
                raise ProviderError(f"Streaming failed for {provider.name}: {exc}") from exc

        if finished:
            yield b"data: [DONE]\n\n"
            return

        logger.warning(
            "stream_terminated_without_finish request_id=%s tenant_id=%s provider=%s",
            request_id,
            tenant_id,
            provider.name,
        )
        PROVIDER_LATENCY.labels(provider.name, "stream", "incomplete").observe(
            perf_counter() - started_at
        )
        yield b"data: [DONE]\n\n"

    async def _stream_text(self, text: str, response_id: str, created: int, model: str):
        yield self._assistant_role_chunk(response_id=response_id, created=created, model=model)
        async for event in self._stream_text_body(text, response_id, created, model):
            yield event

    async def _stream_text_body(self, text: str, response_id: str, created: int, model: str):
        chunk_size = 24
        for start in range(0, len(text), chunk_size):
            delta = text[start : start + chunk_size]
            yield self._content_chunk(response_id=response_id, created=created, model=model, delta=delta)

        yield self._finish_chunk(
            response_id=response_id,
            created=created,
            model=model,
            finish_reason="stop",
        )
        yield b"data: [DONE]\n\n"

    async def _prepare_stream_provider(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        response_id: str,
        created: int,
        request_id: str | None,
        tenant_id: str,
        policy_resolution: PolicyResolution,
        started_at: float,
        cache_key: _CacheKey | None,
        stream_usage: _StreamUsage,
    ) -> tuple[AsyncIterator[bytes], CompletionMetadata]:
        route_decision = policy_resolution.route_decision
        metadata = self._metadata(
            tenant_id=tenant_id,
            route_target=route_decision.target,
            route_reason=route_decision.reason,
            provider=provider.name,
            cache_hit=False,
            fallback_used=False,
            policy_resolution=policy_resolution,
        )
        try:
            stream = await self._prefetched_stream(
                provider=provider,
                request=self._provider_request(request, route_decision.model),
                response_id=response_id,
                created=created,
                request_id=request_id,
                tenant_id=tenant_id,
                cache_write=self._cache_write(
                    cache_key, self._served_model(request, route_decision)
                ),
                stream_usage=stream_usage,
            )
            return stream, metadata
        except ProviderError as exc:
            fallback_model = await self._fallback_model_or_fail(
                request=request,
                request_id=request_id,
                tenant_id=tenant_id,
                resolution=policy_resolution,
                provider_name=provider.name,
                started_at=started_at,
                cause=exc,
                stream=True,
            )

            logger.warning("stream_fallback request_id=%s tenant_id=%s error=%s", request_id, tenant_id, exc)
            FALLBACK_COUNT.labels("local_provider_error").inc()
            fallback_provider = self.provider_registry.get("premium")
            logger.info(
                "fallback_selected request_id=%s tenant_id=%s stream=true provider=%s",
                request_id,
                tenant_id,
                fallback_provider.name,
            )
            fallback_metadata = self._metadata(
                tenant_id=tenant_id,
                route_target="premium",
                route_reason="local_provider_error_fallback",
                provider=fallback_provider.name,
                cache_hit=False,
                fallback_used=True,
                policy_resolution=policy_resolution,
            )
            # The failed attempt may have reported usage before it died; it is not this stream's.
            stream_usage.usage = None
            try:
                fallback_stream = await self._prefetched_stream(
                    provider=fallback_provider,
                    request=self._provider_request(request, fallback_model),
                    response_id=response_id,
                    created=created,
                    request_id=request_id,
                    tenant_id=tenant_id,
                    cache_write=self._cache_write(cache_key, fallback_model),
                    stream_usage=stream_usage,
                )
            except ProviderError as fallback_exc:
                await self._fail_fallback(
                    request=request,
                    request_id=request_id,
                    tenant_id=tenant_id,
                    resolution=policy_resolution,
                    provider_name=fallback_provider.name,
                    started_at=started_at,
                    cause=fallback_exc,
                    stream=True,
                )

            return fallback_stream, fallback_metadata

    async def _prefetched_stream(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        response_id: str,
        created: int,
        request_id: str | None,
        tenant_id: str,
        cache_write: _CacheWrite | None,
        stream_usage: _StreamUsage,
    ) -> AsyncIterator[bytes]:
        provider_stream = self._stream_provider(
            provider=provider,
            request=request,
            response_id=response_id,
            created=created,
            request_id=request_id,
            tenant_id=tenant_id,
            cache_write=cache_write,
            stream_usage=stream_usage,
        )

        try:
            first_event = await provider_stream.__anext__()
        except StopAsyncIteration:

            async def empty_stream():
                yield self._assistant_role_chunk(
                    response_id=response_id,
                    created=created,
                    model=request.model,
                )
                yield b"data: [DONE]\n\n"

            return empty_stream()
        except ProviderError:
            raise

        async def iterator():
            yield self._assistant_role_chunk(
                response_id=response_id,
                created=created,
                model=self._extract_model_from_sse(first_event) or request.model,
            )
            yield first_event
            async for event in provider_stream:
                yield event

        return iterator()

    def _assistant_role_chunk(self, response_id: str, created: int, model: str) -> bytes:
        return self._sse(
            ChatCompletionChunk(
                id=response_id,
                created=created,
                model=model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionStreamDelta(role="assistant"),
                    )
                ],
            )
        )

    def _content_chunk(self, response_id: str, created: int, model: str, delta: str) -> bytes:
        return self._sse(
            ChatCompletionChunk(
                id=response_id,
                created=created,
                model=model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionStreamDelta(content=delta),
                    )
                ],
            )
        )

    def _finish_chunk(
        self, response_id: str, created: int, model: str, finish_reason: FinishReason
    ) -> bytes:
        return self._sse(
            ChatCompletionChunk(
                id=response_id,
                created=created,
                model=model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionStreamDelta(),
                        finish_reason=finish_reason,
                    )
                ],
            )
        )

    def _sse(self, chunk: ChatCompletionChunk) -> bytes:
        return f"data: {json.dumps(chunk.model_dump(mode='json'))}\n\n".encode("utf-8")

    async def _complete_with_provider(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        request_id: str | None,
        tenant_id: str,
    ):
        started_at = perf_counter()
        try:
            result = await provider.complete(request)
        except ProviderError:
            PROVIDER_LATENCY.labels(provider.name, "completion", "error").observe(
                perf_counter() - started_at
            )
            raise
        except Exception as exc:
            PROVIDER_LATENCY.labels(provider.name, "completion", "error").observe(
                perf_counter() - started_at
            )
            raise ProviderError(f"Completion failed for {provider.name}: {exc}") from exc

        PROVIDER_LATENCY.labels(provider.name, "completion", "ok").observe(
            perf_counter() - started_at
        )
        logger.info(
            "provider_completed request_id=%s tenant_id=%s provider=%s mode=completion latency_ms=%.2f",
            request_id,
            tenant_id,
            provider.name,
            (perf_counter() - started_at) * 1000,
        )
        return result

    async def _resolve_policy(
        self,
        *,
        request: ChatCompletionRequest,
        prompt: str,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None,
        prompt_embedding: list[float] | None = None,
    ) -> PolicyResolution:
        try:
            return await self.policy_service.resolve(
                prompt=prompt,
                request=request,
                tenant_context=tenant_context,
                router_service=self.router_service,
                prompt_embedding=prompt_embedding,
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                headers = exc.headers or {}
                await self._record_policy_denial(
                    request=request,
                    tenant_id=tenant_context.tenant.id,
                    request_id=request_id,
                    route_reason=headers.get("X-Nebula-Route-Reason"),
                    policy_outcome=headers.get("X-Nebula-Policy-Outcome", exc.detail),
                )
            raise

    async def _deny_spend(
        self,
        *,
        request: ChatCompletionRequest,
        tenant_id: str,
        request_id: str | None,
        denial: SpendDenial,
    ) -> NoReturn:
        """After a cache miss, the 403 the spend guardrail held back and its policy_denied row."""
        await self._record_policy_denial(
            request=request,
            tenant_id=tenant_id,
            request_id=request_id,
            route_reason=denial.route_reason,
            policy_outcome=denial.policy_outcome,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=denial.detail,
            headers=denial.headers,
        )

    async def _record_policy_denial(
        self,
        *,
        request: ChatCompletionRequest,
        tenant_id: str,
        request_id: str | None,
        route_reason: str | None,
        policy_outcome: str | None,
    ) -> None:
        record = UsageLedgerRecord(
            request_id=request_id or f"req-{uuid4().hex}",
            tenant_id=tenant_id,
            requested_model=request.model,
            final_route_target="denied",
            final_provider=None,
            fallback_used=False,
            cache_hit=False,
            response_model=None,
            estimated_cost=None,
            latency_ms=None,
            timestamp=datetime.now(UTC),
            terminal_status="policy_denied",
            route_reason=route_reason,
            policy_outcome=policy_outcome,
            route_signals=None,
        )
        await run_in_threadpool(self.governance_store.record_usage, record)

    async def _embed_for_routing(self, prompt: str) -> list[float] | None:
        """Embed the prompt once for the learned router; None when it is off or embedding fails."""
        learned = self.router_service.learned
        if learned is None or self.embeddings_service is None:
            return None
        text = prompt if learned.prefix == "none" else f"{learned.prefix}: {prompt}"
        return await self._embed(text, purpose="routing")

    async def _embed(
        self, text: str, *, purpose: Literal["routing", "cache"]
    ) -> list[float] | None:
        assert self.embeddings_service is not None
        try:
            # A slow Ollama must not hold the request: past the timeout it goes on without.
            return await self.embeddings_service.embed(
                text, timeout=REQUEST_PATH_EMBED_TIMEOUT_SECONDS
            )
        except Exception as exc:  # noqa: BLE001 - heuristic routing, no cache: both degrade
            logger.warning("%s_embedding_failed error=%s", purpose, exc)
            return None

    def _served_model(self, request: ChatCompletionRequest, route_decision: RouteDecision) -> str:
        """The model the routed provider is asked for (what `_provider_request` sends it)."""
        model = self._provider_request(request, route_decision.model).model
        if model != self.settings.default_model:
            return model
        # The auto alias: each provider serves its configured model.
        if route_decision.target == "local":
            return self.settings.local_model
        return self.settings.premium_model

    def _provider_request(
        self, request: ChatCompletionRequest, decision_model: str | None
    ) -> ChatCompletionRequest:
        # Providers serve request.model unless it is the auto alias; the tier model rides there.
        if decision_model is None:
            return request
        return request.model_copy(update={"model": decision_model})

    def _fallback_model(self, policy_resolution: PolicyResolution) -> str:
        """Economy when configured and the tenant allows it; otherwise the frontier model.

        Always explicit: the request's own model may be the local model id, which the premium
        provider must never receive.
        """
        economy = self.settings.economy_model
        allowed = policy_resolution.allowed_premium_models
        if economy and (not allowed or economy in allowed):
            return economy
        return self.settings.premium_model

    def _route_tier(
        self,
        *,
        route_target: str,
        fallback_used: bool,
        signals: dict[str, Any],
        policy_resolution: PolicyResolution,
    ) -> str:
        if route_target in {"local", "cache", "denied"}:
            return route_target
        if fallback_used:
            fallback_model = self._fallback_model(policy_resolution)
            return "economy" if fallback_model == self.settings.economy_model else "frontier"
        tier = signals.get("tier")
        if tier in {"economy", "frontier"}:
            return tier
        model = policy_resolution.route_decision.model
        return "economy" if model and model == self.settings.economy_model else "frontier"

    def _cache_avoided_cost(
        self,
        request: ChatCompletionRequest,
        policy_resolution: PolicyResolution,
        usage: CompletionUsage,
    ) -> float:
        """What the request would have cost on its chosen route, had the cache not answered it.

        Recorded as a route signal on the hit row; the row's `estimated_cost` stays 0, so spend
        and the hard budget are untouched. Under `metadata_minimization_level=strict` the store
        drops route signals, and such a hit counts as 0 avoided in the recommendations.
        """
        route_decision = policy_resolution.route_decision
        if route_decision.target == "local":
            return 0.0
        # None: the model has no price in the catalog, and a guess would invent savings.
        cost = self.policy_service.estimate_cost(self._served_model(request, route_decision), usage)
        return cost or 0.0

    def _resolved_usage(
        self,
        request: ChatCompletionRequest,
        response_content: str,
        usage: CompletionUsage | None,
    ) -> CompletionUsage:
        return usage or self.policy_service.estimate_usage(request, response_content)

    async def _record_usage(
        self,
        *,
        request_id: str | None,
        tenant_id: str,
        request: ChatCompletionRequest,
        metadata: CompletionMetadata,
        response_model: str | None,
        usage: CompletionUsage | None,
        latency_ms: float | None,
        terminal_status: TerminalStatus,
    ) -> None:
        """Write one ledger row off the event loop (same keywords as `_write_usage`)."""
        await run_in_threadpool(
            self._write_usage,
            request_id=request_id,
            tenant_id=tenant_id,
            request=request,
            metadata=metadata,
            response_model=response_model,
            usage=usage,
            latency_ms=latency_ms,
            terminal_status=terminal_status,
        )

    def _write_usage(
        self,
        *,
        request_id: str | None,
        tenant_id: str,
        request: ChatCompletionRequest,
        metadata: CompletionMetadata,
        response_model: str | None,
        usage: CompletionUsage | None,
        latency_ms: float | None,
        terminal_status: TerminalStatus,
    ) -> None:
        # Synchronous on purpose. Every non-stream caller reaches it through `_record_usage`
        # (off the loop). The stream's `finally` calls it directly: that block runs while the
        # generator is closing after a client disconnect or cancellation, where awaiting can be
        # cut short before the row exists, and a lost row undercounts the hard budget (B5). The
        # price is one SQLite insert of a few milliseconds on the loop per stream (spec B17).
        estimated_cost = 0.0
        if metadata.route_target == "premium":
            effective_model = response_model or request.model
            estimated_cost = self.policy_service.estimate_cost(effective_model, usage)
        self.governance_store.record_usage(
            UsageLedgerRecord(
                request_id=request_id or f"req-{uuid4().hex}",
                tenant_id=tenant_id,
                requested_model=request.model,
                final_route_target=metadata.route_target,
                final_provider=metadata.provider,
                fallback_used=metadata.fallback_used,
                cache_hit=metadata.cache_hit,
                response_model=response_model,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                estimated_cost=estimated_cost,
                latency_ms=round(latency_ms, 2) if latency_ms is not None else None,
                timestamp=datetime.now(UTC),
                terminal_status=terminal_status,
                route_reason=metadata.route_reason,
                policy_outcome=metadata.policy_outcome,
                route_signals=metadata.route_signals,
                message_type="chat",
            )
        )

    def _metadata(
        self,
        *,
        tenant_id: str,
        route_target: Literal["local", "premium", "cache", "denied"],
        route_reason: str,
        provider: str,
        cache_hit: bool | CacheHit,
        fallback_used: bool,
        policy_resolution: PolicyResolution,
        avoided_cost_usd: float | None = None,
    ) -> CompletionMetadata:
        signals: dict[str, Any] = dict(policy_resolution.route_decision.signals or {})
        if isinstance(cache_hit, CacheHit):
            signals["cache_similarity_score"] = round(cache_hit.score, 4)
            signals["cache_entry_age_seconds"] = cache_hit.age_seconds
            signals["cache_entry_model"] = cache_hit.model
            if policy_resolution.spend_denial is not None:
                # Served past a spend guardrail: savings that only the cache made possible.
                signals["spend_guardrail"] = policy_resolution.spend_denial.guardrail
        if avoided_cost_usd is not None:
            signals["cache_avoided_cost_usd"] = avoided_cost_usd
        return CompletionMetadata(
            tenant_id=tenant_id,
            route_target=route_target,
            route_reason=route_reason,
            provider=provider,
            cache_hit=bool(cache_hit),
            fallback_used=fallback_used,
            policy_mode=policy_resolution.policy_mode,
            policy_outcome=policy_resolution.policy_outcome,
            route_signals=signals or None,
            route_score=policy_resolution.route_decision.score,
            route_tier=self._route_tier(
                route_target=route_target,
                fallback_used=fallback_used,
                signals=signals,
                policy_resolution=policy_resolution,
            ),
        )

    async def _fail_provider(
        self,
        *,
        request: ChatCompletionRequest,
        request_id: str | None,
        tenant_id: str,
        resolution: PolicyResolution,
        route_target: RouteTarget,
        route_reason: str,
        provider_name: str,
        fallback_used: bool,
        detail: str,
        started_at: float,
        cause: Exception,
    ) -> NoReturn:
        """Record the provider_error row and raise the 502; shared by both serving paths."""
        await self._record_usage(
            request_id=request_id,
            tenant_id=tenant_id,
            request=request,
            metadata=self._metadata(
                tenant_id=tenant_id,
                route_target=route_target,
                route_reason=route_reason,
                provider=provider_name,
                cache_hit=False,
                fallback_used=fallback_used,
                policy_resolution=resolution,
            ),
            response_model=None,
            usage=None,
            latency_ms=(perf_counter() - started_at) * 1000,
            terminal_status="provider_error",
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            headers=self._error_headers(
                tenant_id=tenant_id,
                route_target=route_target,
                route_reason=route_reason,
                provider=provider_name,
                fallback_used=fallback_used,
                policy_resolution=resolution,
            ),
        ) from cause

    async def _fallback_model_or_fail(
        self,
        *,
        request: ChatCompletionRequest,
        request_id: str | None,
        tenant_id: str,
        resolution: PolicyResolution,
        provider_name: str,
        started_at: float,
        cause: ProviderError,
        stream: bool,
    ) -> str:
        """After the routed provider failed: the premium model to fall back to, or the 502.

        Only a local failure falls back, and only when the tenant would allow that premium request.
        """
        route_decision = resolution.route_decision
        route_reason = route_decision.reason
        detail = str(cause)
        if route_decision.target == "local":
            fallback_model = self._fallback_model(resolution)
            block_reason = self.policy_service.premium_fallback_block_reason(
                request, resolution, fallback_model
            )
            if block_reason is None:
                return fallback_model
            route_reason = "local_provider_error_fallback_blocked"
            detail = block_reason
        if not stream:
            # A streaming provider counts its own errors inside the stream.
            COMPLETION_COUNT.labels(provider_name, "error", "false").inc()
        await self._fail_provider(
            request=request,
            request_id=request_id,
            tenant_id=tenant_id,
            resolution=resolution,
            route_target=route_decision.target,
            route_reason=route_reason,
            provider_name=provider_name,
            fallback_used=False,
            detail=detail,
            started_at=started_at,
            cause=cause,
        )

    async def _fail_fallback(
        self,
        *,
        request: ChatCompletionRequest,
        request_id: str | None,
        tenant_id: str,
        resolution: PolicyResolution,
        provider_name: str,
        started_at: float,
        cause: ProviderError,
        stream: bool,
    ) -> NoReturn:
        """The premium fallback failed too: the 502 and its row are the fallback's, not local's."""
        if not stream:
            # A streaming provider counts its own errors inside the stream.
            COMPLETION_COUNT.labels(provider_name, "error", "false").inc()
        await self._fail_provider(
            request=request,
            request_id=request_id,
            tenant_id=tenant_id,
            resolution=resolution,
            route_target="premium",
            route_reason="local_provider_error_fallback",
            provider_name=provider_name,
            fallback_used=True,
            detail=str(cause),
            started_at=started_at,
            cause=cause,
        )

    def _error_headers(
        self,
        *,
        tenant_id: str,
        route_target: str,
        route_reason: str,
        provider: str,
        fallback_used: bool,
        policy_resolution: PolicyResolution,
    ) -> dict[str, str]:
        headers = {
            "X-Nebula-Tenant-ID": tenant_id,
            "X-Nebula-Route-Target": route_target,
            "X-Nebula-Route-Reason": route_reason,
            "X-Nebula-Provider": provider,
            "X-Nebula-Route-Score": f"{policy_resolution.route_decision.score:.4f}",
            "X-Nebula-Cache-Hit": "false",
            "X-Nebula-Fallback-Used": str(fallback_used).lower(),
            "X-Nebula-Policy-Mode": policy_resolution.policy_mode,
            "X-Nebula-Policy-Outcome": policy_resolution.policy_outcome,
            "X-Nebula-Route-Tier": self._route_tier(
                route_target=route_target,
                fallback_used=fallback_used,
                signals=policy_resolution.route_decision.signals,
                policy_resolution=policy_resolution,
            ),
        }
        route_mode = policy_resolution.route_decision.signals.get("route_mode")
        if route_mode is not None:
            headers["X-Nebula-Route-Mode"] = str(route_mode)
        return headers

    def _extract_model_from_sse(self, payload: bytes) -> str | None:
        decoded = self._decode_sse(payload)
        return decoded.get("model") if decoded else None

    def _extract_delta_from_sse(self, payload: bytes) -> str | None:
        decoded = self._decode_sse(payload)
        if not decoded:
            return None
        choices = decoded.get("choices", [])
        if not choices:
            return None
        return choices[0].get("delta", {}).get("content")

    def _decode_sse(self, payload: bytes) -> dict[str, object] | None:
        prefix = b"data: "
        if not payload.startswith(prefix):
            return None
        body = payload[len(prefix) :].strip()
        if body == b"[DONE]":
            return None
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError:
            return None
        return decoded

    def _wrap_stream_with_ledger(
        self,
        *,
        stream: AsyncIterator[bytes],
        request: ChatCompletionRequest,
        metadata: CompletionMetadata,
        request_id: str | None,
        started_at: float,
        stream_usage: _StreamUsage | None = None,
    ) -> AsyncIterator[bytes]:
        async def iterator():
            content_parts: list[str] = []
            response_model: str | None = None
            # Any exit that is not a normal end or a provider failure (GeneratorExit when the
            # generator is closed, CancelledError when the serving task is cancelled) means the
            # client went away mid-stream.
            terminal_status: TerminalStatus = "client_disconnected"
            try:
                async for event in stream:
                    model = self._extract_model_from_sse(event)
                    if model:
                        response_model = model
                    delta = self._extract_delta_from_sse(event)
                    if delta:
                        content_parts.append(delta)
                    yield event
                terminal_status = (
                    "cache_hit"
                    if metadata.cache_hit
                    else "fallback_completed"
                    if metadata.fallback_used
                    else "completed"
                )
            except Exception:
                terminal_status = "provider_error"
                raise
            finally:
                # Exactly one row per stream, whichever way it ended. This is the one governance
                # store call that stays synchronous on the event loop (spec B17): awaiting here
                # (e.g. run_in_threadpool) can be cut short when the generator is closed after
                # a client disconnect or the task is cancelled, and a lost row would undercount
                # the hard budget (B5). The cost is one SQLite insert of a few milliseconds.
                self._write_usage(
                    request_id=request_id,
                    tenant_id=metadata.tenant_id,
                    request=request,
                    metadata=metadata,
                    response_model=response_model,
                    usage=(
                        None
                        if terminal_status == "provider_error"
                        else self._resolved_usage(
                            request,
                            "".join(content_parts),
                            stream_usage.usage if stream_usage else None,
                        )
                    ),
                    latency_ms=(perf_counter() - started_at) * 1000,
                    terminal_status=terminal_status,
                )

        return iterator()
