from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter, time
from typing import AsyncIterator, Literal
from uuid import uuid4

from fastapi import HTTPException, status

from nebula.core.config import Settings
from nebula.models.governance import UsageLedgerRecord
from nebula.models.openai import (
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    ChatCompletionStreamDelta,
    ChatCompletionUsage,
)
from nebula.observability.metrics import (
    COMPLETION_COUNT,
    FALLBACK_COUNT,
    PROVIDER_LATENCY,
    ROUTE_DECISION_COUNT,
)
from nebula.providers.base import CompletionProvider, CompletionUsage, ProviderError
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyResolution, PolicyService
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouterService
from nebula.services.semantic_cache_service import SemanticCacheService

logger = logging.getLogger(__name__)


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
    ) -> None:
        self.settings = settings
        self.cache_service = cache_service
        self.router_service = router_service
        self.provider_registry = provider_registry
        self.governance_store = governance_store
        self.policy_service = policy_service

    async def create_completion(
        self,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None = None,
    ) -> ChatCompletionResponse:
        envelope = await self.create_completion_with_metadata(
            request,
            tenant_context=tenant_context,
            request_id=request_id,
        )
        return envelope.response

    async def create_completion_with_metadata(
        self,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None = None,
    ) -> CompletionResponseEnvelope:
        started_at = perf_counter()
        latest_user_prompt = self._extract_latest_user_prompt(request)
        policy_resolution = await self._resolve_policy(
            request=request,
            prompt=latest_user_prompt,
            tenant_context=tenant_context,
            request_id=request_id,
        )

        cached_response = await self._lookup_cache(
            prompt=latest_user_prompt,
            cache_enabled=policy_resolution.cache_enabled,
            request_id=request_id,
            stream=False,
        )
        if cached_response is not None:
            usage = self.policy_service.estimate_usage(request, cached_response)
            metadata = self._metadata(
                tenant_id=tenant_context.tenant.id,
                route_target="cache",
                route_reason="cache_hit",
                provider="cache",
                cache_hit=True,
                fallback_used=False,
                policy_resolution=policy_resolution,
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
            result = await self._complete_with_provider(provider, request, request_id, tenant_context.tenant.id)
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
            terminal_status = "completed"
        except ProviderError as exc:
            logger.warning(
                "provider_failed request_id=%s tenant_id=%s provider=%s error=%s",
                request_id,
                tenant_context.tenant.id,
                provider.name,
                exc,
            )
            if route_decision.target != "local" or not policy_resolution.fallback_enabled:
                error_detail = str(exc)
                error_headers: dict[str, str] | None = None
                error_route_reason = route_decision.reason
                if route_decision.target == "local" and not policy_resolution.fallback_enabled:
                    error_detail = "Local provider failed and tenant policy disabled premium fallback."
                    error_route_reason = "local_provider_error_fallback_blocked"
                    error_headers = self._error_headers(
                        tenant_id=tenant_context.tenant.id,
                        route_target="local",
                        route_reason=error_route_reason,
                        provider=provider.name,
                        fallback_used=False,
                        policy_resolution=policy_resolution,
                    )
                COMPLETION_COUNT.labels(provider.name, "error", "false").inc()
                await self._record_usage(
                    request_id=request_id,
                    tenant_id=tenant_context.tenant.id,
                    request=request,
                    metadata=self._metadata(
                        tenant_id=tenant_context.tenant.id,
                        route_target=route_decision.target,
                        route_reason=error_route_reason,
                        provider=provider.name,
                        cache_hit=False,
                        fallback_used=False,
                        policy_resolution=policy_resolution,
                    ),
                    response_model=None,
                    usage=None,
                    latency_ms=(perf_counter() - started_at) * 1000,
                    terminal_status="provider_error",
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=error_detail,
                    headers=error_headers,
                ) from exc

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
                    request,
                    request_id,
                    tenant_context.tenant.id,
                )
            except ProviderError as fallback_exc:
                COMPLETION_COUNT.labels(fallback_provider.name, "error", "false").inc()
                await self._record_usage(
                    request_id=request_id,
                    tenant_id=tenant_context.tenant.id,
                    request=request,
                    metadata=self._metadata(
                        tenant_id=tenant_context.tenant.id,
                        route_target="premium",
                        route_reason="local_provider_error_fallback",
                        provider=fallback_provider.name,
                        cache_hit=False,
                        fallback_used=True,
                        policy_resolution=policy_resolution,
                    ),
                    response_model=None,
                    usage=None,
                    latency_ms=(perf_counter() - started_at) * 1000,
                    terminal_status="provider_error",
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(fallback_exc),
                ) from fallback_exc
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
            terminal_status = "fallback_completed"

        usage = self._resolved_usage(request, result.content, result.usage)
        if policy_resolution.cache_enabled:
            await self.cache_service.store(latest_user_prompt, result.content, result.model)
        response = self._build_response(content=result.content, model=result.model, usage=usage)
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

    async def stream_completion(
        self,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None = None,
    ):
        envelope = await self.stream_completion_with_metadata(
            request,
            tenant_context=tenant_context,
            request_id=request_id,
        )
        async for event in envelope.stream:
            yield event

    async def stream_completion_with_metadata(
        self,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        request_id: str | None = None,
    ) -> StreamingCompletionEnvelope:
        started_at = perf_counter()
        latest_user_prompt = self._extract_latest_user_prompt(request)
        policy_resolution = await self._resolve_policy(
            request=request,
            prompt=latest_user_prompt,
            tenant_context=tenant_context,
            request_id=request_id,
        )
        response_id = f"chatcmpl-{uuid4().hex}"
        created = int(time())

        cached_response = await self._lookup_cache(
            prompt=latest_user_prompt,
            cache_enabled=policy_resolution.cache_enabled,
            request_id=request_id,
            stream=True,
        )
        if cached_response is not None:
            COMPLETION_COUNT.labels("cache", "ok", "true").inc()
            metadata = self._metadata(
                tenant_id=tenant_context.tenant.id,
                route_target="cache",
                route_reason="cache_hit",
                provider="cache",
                cache_hit=True,
                fallback_used=False,
                policy_resolution=policy_resolution,
            )
            wrapped_stream = self._wrap_stream_with_ledger(
                stream=self._stream_text(cached_response, response_id, created, "nebula-cache"),
                request=request,
                metadata=metadata,
                request_id=request_id,
                started_at=started_at,
            )
            return StreamingCompletionEnvelope(stream=wrapped_stream, metadata=metadata)

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
        try:
            stream, metadata = await self._prepare_stream_provider(
                provider=provider,
                request=request,
                prompt=latest_user_prompt,
                response_id=response_id,
                created=created,
                request_id=request_id,
                tenant_id=tenant_context.tenant.id,
                policy_resolution=policy_resolution,
                cache_enabled=policy_resolution.cache_enabled,
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_502_BAD_GATEWAY:
                await self._record_usage(
                    request_id=request_id,
                    tenant_id=tenant_context.tenant.id,
                    request=request,
                    metadata=self._metadata(
                        tenant_id=tenant_context.tenant.id,
                        route_target=route_decision.target,
                        route_reason=route_decision.reason,
                        provider=provider.name,
                        cache_hit=False,
                        fallback_used=False,
                        policy_resolution=policy_resolution,
                    ),
                    response_model=None,
                    usage=None,
                    latency_ms=(perf_counter() - started_at) * 1000,
                    terminal_status="provider_error",
                )
            raise

        wrapped_stream = self._wrap_stream_with_ledger(
            stream=stream,
            request=request,
            metadata=metadata,
            request_id=request_id,
            started_at=started_at,
        )
        return StreamingCompletionEnvelope(stream=wrapped_stream, metadata=metadata)

    def _extract_latest_user_prompt(self, request: ChatCompletionRequest) -> str:
        for message in reversed(request.messages):
            if message.role == "user":
                if isinstance(message.content, str):
                    return message.content
                return str(message.content)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one user message is required.",
        )

    def _build_response(
        self,
        content: str,
        model: str,
        usage: CompletionUsage | None,
    ) -> ChatCompletionResponse:
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid4().hex}",
            created=int(time()),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionResponseMessage(content=content),
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
        )

    async def _lookup_cache(
        self,
        *,
        prompt: str,
        cache_enabled: bool,
        request_id: str | None,
        stream: bool,
    ) -> str | None:
        if not cache_enabled:
            logger.info("cache_bypassed request_id=%s stream=%s reason=policy_disabled", request_id, stream)
            return None
        cached_response = await self.cache_service.lookup(prompt)
        if cached_response is not None:
            logger.info(
                "cache_hit request_id=%s stream=%s prompt_chars=%s",
                request_id,
                str(stream).lower(),
                len(prompt),
            )
        else:
            logger.info(
                "cache_miss request_id=%s stream=%s prompt_chars=%s",
                request_id,
                str(stream).lower(),
                len(prompt),
            )
        return cached_response

    async def _stream_provider(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        prompt: str,
        response_id: str,
        created: int,
        request_id: str | None,
        tenant_id: str,
        cache_enabled: bool,
    ):
        content_parts: list[str] = []
        started_at = perf_counter()

        try:
            async for chunk in provider.stream_complete(request):
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
                    if cache_enabled:
                        await self.cache_service.store(prompt, "".join(content_parts), chunk.model)
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
                                    finish_reason=chunk.finish_reason,
                                )
                            ],
                        )
                    )
                    yield b"data: [DONE]\n\n"
                    return
        except ProviderError:
            COMPLETION_COUNT.labels(provider.name, "error", "true").inc()
            PROVIDER_LATENCY.labels(provider.name, "stream", "error").observe(
                perf_counter() - started_at
            )
            raise
        except Exception as exc:
            COMPLETION_COUNT.labels(provider.name, "error", "true").inc()
            PROVIDER_LATENCY.labels(provider.name, "stream", "error").observe(
                perf_counter() - started_at
            )
            raise ProviderError(f"Streaming failed for {provider.name}: {exc}") from exc

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
        prompt: str,
        response_id: str,
        created: int,
        request_id: str | None,
        tenant_id: str,
        policy_resolution: PolicyResolution,
        cache_enabled: bool,
    ) -> tuple[AsyncIterator[bytes], CompletionMetadata]:
        route_decision = policy_resolution.route_decision
        try:
            stream = await self._prefetched_stream(
                provider=provider,
                request=request,
                prompt=prompt,
                response_id=response_id,
                created=created,
                request_id=request_id,
                tenant_id=tenant_id,
                cache_enabled=cache_enabled,
            )
            return (
                stream,
                self._metadata(
                    tenant_id=tenant_id,
                    route_target=route_decision.target,
                    route_reason=route_decision.reason,
                    provider=provider.name,
                    cache_hit=False,
                    fallback_used=False,
                    policy_resolution=policy_resolution,
                ),
            )
        except ProviderError as exc:
            if route_decision.target != "local" or not policy_resolution.fallback_enabled:
                error_detail = str(exc)
                error_headers: dict[str, str] | None = None
                if route_decision.target == "local" and not policy_resolution.fallback_enabled:
                    error_detail = "Local provider failed and tenant policy disabled premium fallback."
                    error_headers = self._error_headers(
                        tenant_id=tenant_id,
                        route_target="local",
                        route_reason="local_provider_error_fallback_blocked",
                        provider=provider.name,
                        fallback_used=False,
                        policy_resolution=policy_resolution,
                    )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=error_detail,
                    headers=error_headers,
                ) from exc

            logger.warning("stream_fallback request_id=%s tenant_id=%s error=%s", request_id, tenant_id, exc)
            FALLBACK_COUNT.labels("local_provider_error").inc()
            fallback_provider = self.provider_registry.get("premium")
            logger.info(
                "fallback_selected request_id=%s tenant_id=%s stream=true provider=%s",
                request_id,
                tenant_id,
                fallback_provider.name,
            )
            try:
                fallback_stream = await self._prefetched_stream(
                    provider=fallback_provider,
                    request=request,
                    prompt=prompt,
                    response_id=response_id,
                    created=created,
                    request_id=request_id,
                    tenant_id=tenant_id,
                    cache_enabled=cache_enabled,
                )
            except ProviderError as fallback_exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(fallback_exc),
                ) from fallback_exc

            return (
                fallback_stream,
                self._metadata(
                    tenant_id=tenant_id,
                    route_target="premium",
                    route_reason="local_provider_error_fallback",
                    provider=fallback_provider.name,
                    cache_hit=False,
                    fallback_used=True,
                    policy_resolution=policy_resolution,
                ),
            )

    async def _prefetched_stream(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        prompt: str,
        response_id: str,
        created: int,
        request_id: str | None,
        tenant_id: str,
        cache_enabled: bool,
    ) -> AsyncIterator[bytes]:
        provider_stream = self._stream_provider(
            provider=provider,
            request=request,
            prompt=prompt,
            response_id=response_id,
            created=created,
            request_id=request_id,
            tenant_id=tenant_id,
            cache_enabled=cache_enabled,
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

    def _finish_chunk(self, response_id: str, created: int, model: str, finish_reason: str) -> bytes:
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
    ) -> PolicyResolution:
        try:
            return await self.policy_service.resolve(
                prompt=prompt,
                request=request,
                tenant_context=tenant_context,
                router_service=self.router_service,
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                headers = exc.headers or {}
                self.governance_store.record_usage(
                    UsageLedgerRecord(
                        request_id=request_id or f"req-{uuid4().hex}",
                        tenant_id=tenant_context.tenant.id,
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
                        route_reason=headers.get("X-Nebula-Route-Reason"),
                        policy_outcome=headers.get("X-Nebula-Policy-Outcome", exc.detail),
                    )
                )
            raise

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
        terminal_status: Literal[
            "completed",
            "cache_hit",
            "fallback_completed",
            "provider_error",
        ],
    ) -> None:
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
            )
        )

    def _metadata(
        self,
        *,
        tenant_id: str,
        route_target: Literal["local", "premium", "cache", "denied"],
        route_reason: str,
        provider: str,
        cache_hit: bool,
        fallback_used: bool,
        policy_resolution: PolicyResolution,
    ) -> CompletionMetadata:
        return CompletionMetadata(
            tenant_id=tenant_id,
            route_target=route_target,
            route_reason=route_reason,
            provider=provider,
            cache_hit=cache_hit,
            fallback_used=fallback_used,
            policy_mode=policy_resolution.policy_mode,
            policy_outcome=policy_resolution.policy_outcome,
            route_signals=policy_resolution.route_decision.signals or None,
            route_score=policy_resolution.route_decision.score,
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
        return {
            "X-Nebula-Tenant-ID": tenant_id,
            "X-Nebula-Route-Target": route_target,
            "X-Nebula-Route-Reason": route_reason,
            "X-Nebula-Provider": provider,
            "X-Nebula-Cache-Hit": "false",
            "X-Nebula-Fallback-Used": str(fallback_used).lower(),
            "X-Nebula-Policy-Mode": policy_resolution.policy_mode,
            "X-Nebula-Policy-Outcome": policy_resolution.policy_outcome,
        }

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
    ) -> AsyncIterator[bytes]:
        async def iterator():
            content_parts: list[str] = []
            response_model: str | None = None
            try:
                async for event in stream:
                    model = self._extract_model_from_sse(event)
                    if model:
                        response_model = model
                    delta = self._extract_delta_from_sse(event)
                    if delta:
                        content_parts.append(delta)
                    yield event
            except Exception:
                await self._record_usage(
                    request_id=request_id,
                    tenant_id=metadata.tenant_id,
                    request=request,
                    metadata=metadata,
                    response_model=response_model,
                    usage=None,
                    latency_ms=(perf_counter() - started_at) * 1000,
                    terminal_status="provider_error",
                )
                raise

            final_content = "".join(content_parts)
            usage = self.policy_service.estimate_usage(request, final_content)
            await self._record_usage(
                request_id=request_id,
                tenant_id=metadata.tenant_id,
                request=request,
                metadata=metadata,
                response_model=response_model,
                usage=usage,
                latency_ms=(perf_counter() - started_at) * 1000,
                terminal_status=(
                    "cache_hit"
                    if metadata.cache_hit
                    else "fallback_completed"
                    if metadata.fallback_used
                    else "completed"
                ),
            )

        return iterator()
