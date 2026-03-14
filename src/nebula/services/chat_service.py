from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import AsyncIterator, Literal
from time import perf_counter
from time import time
from uuid import uuid4

from fastapi import HTTPException, status

from nebula.core.config import Settings
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
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouterService
from nebula.services.semantic_cache_service import SemanticCacheService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CompletionMetadata:
    route_target: Literal["local", "premium", "cache"]
    route_reason: str
    provider: str
    cache_hit: bool
    fallback_used: bool


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
    ) -> None:
        self.settings = settings
        self.cache_service = cache_service
        self.router_service = router_service
        self.provider_registry = provider_registry

    async def create_completion(
        self,
        request: ChatCompletionRequest,
        request_id: str | None = None,
    ) -> ChatCompletionResponse:
        envelope = await self.create_completion_with_metadata(request, request_id=request_id)
        return envelope.response

    async def create_completion_with_metadata(
        self,
        request: ChatCompletionRequest,
        request_id: str | None = None,
    ) -> CompletionResponseEnvelope:
        latest_user_prompt = self._extract_latest_user_prompt(request)
        cached_response = await self.cache_service.lookup(latest_user_prompt)
        if cached_response:
            logger.info(
                "cache_hit request_id=%s stream=false prompt_chars=%s",
                request_id,
                len(latest_user_prompt),
            )
            COMPLETION_COUNT.labels("cache", "ok", "false").inc()
            return CompletionResponseEnvelope(
                response=self._build_response(
                    content=cached_response,
                    model="nebula-cache",
                    usage=None,
                ),
                metadata=CompletionMetadata(
                    route_target="cache",
                    route_reason="cache_hit",
                    provider="cache",
                    cache_hit=True,
                    fallback_used=False,
                ),
            )

        logger.info(
            "cache_miss request_id=%s stream=false prompt_chars=%s",
            request_id,
            len(latest_user_prompt),
        )
        route_decision = await self.router_service.choose_target_with_reason(latest_user_prompt, request)
        ROUTE_DECISION_COUNT.labels(route_decision.target, route_decision.reason, "false").inc()
        logger.info(
            "route_selected request_id=%s stream=false target=%s reason=%s",
            request_id,
            route_decision.target,
            route_decision.reason,
        )
        provider = self.provider_registry.get(route_decision.target)
        try:
            result = await self._complete_with_provider(provider, request, request_id)
            COMPLETION_COUNT.labels(provider.name, "ok", "false").inc()
            metadata = CompletionMetadata(
                route_target=route_decision.target,
                route_reason=route_decision.reason,
                provider=provider.name,
                cache_hit=False,
                fallback_used=False,
            )
        except ProviderError as exc:
            logger.warning("provider_failed request_id=%s provider=%s error=%s", request_id, provider.name, exc)
            if route_decision.target != "local":
                COMPLETION_COUNT.labels(provider.name, "error", "false").inc()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc
            fallback_provider = self.provider_registry.get("premium")
            FALLBACK_COUNT.labels("local_provider_error").inc()
            logger.info(
                "fallback_selected request_id=%s stream=false provider=%s",
                request_id,
                fallback_provider.name,
            )
            try:
                result = await self._complete_with_provider(fallback_provider, request, request_id)
            except ProviderError as fallback_exc:
                COMPLETION_COUNT.labels(fallback_provider.name, "error", "false").inc()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(fallback_exc),
                ) from fallback_exc
            COMPLETION_COUNT.labels(fallback_provider.name, "fallback", "false").inc()
            metadata = CompletionMetadata(
                route_target="premium",
                route_reason="local_provider_error_fallback",
                provider=fallback_provider.name,
                cache_hit=False,
                fallback_used=True,
            )

        await self.cache_service.store(latest_user_prompt, result.content, result.model)
        return CompletionResponseEnvelope(
            response=self._build_response(content=result.content, model=result.model, usage=result.usage),
            metadata=metadata,
        )

    async def stream_completion(
        self,
        request: ChatCompletionRequest,
        request_id: str | None = None,
    ):
        envelope = await self.stream_completion_with_metadata(request, request_id=request_id)
        async for event in envelope.stream:
            yield event

    async def stream_completion_with_metadata(
        self,
        request: ChatCompletionRequest,
        request_id: str | None = None,
    ) -> StreamingCompletionEnvelope:
        latest_user_prompt = self._extract_latest_user_prompt(request)
        cached_response = await self.cache_service.lookup(latest_user_prompt)
        response_id = f"chatcmpl-{uuid4().hex}"
        created = int(time())

        if cached_response:
            logger.info(
                "cache_hit request_id=%s stream=true prompt_chars=%s",
                request_id,
                len(latest_user_prompt),
            )
            COMPLETION_COUNT.labels("cache", "ok", "true").inc()
            return StreamingCompletionEnvelope(
                stream=self._stream_text(cached_response, response_id, created, "nebula-cache"),
                metadata=CompletionMetadata(
                    route_target="cache",
                    route_reason="cache_hit",
                    provider="cache",
                    cache_hit=True,
                    fallback_used=False,
                ),
            )

        logger.info(
            "cache_miss request_id=%s stream=true prompt_chars=%s",
            request_id,
            len(latest_user_prompt),
        )
        route_decision = await self.router_service.choose_target_with_reason(latest_user_prompt, request)
        ROUTE_DECISION_COUNT.labels(route_decision.target, route_decision.reason, "true").inc()
        logger.info(
            "route_selected request_id=%s stream=true target=%s reason=%s",
            request_id,
            route_decision.target,
            route_decision.reason,
        )
        provider = self.provider_registry.get(route_decision.target)
        stream, stream_metadata = await self._prepare_stream_provider(
            provider=provider,
            request=request,
            prompt=latest_user_prompt,
            response_id=response_id,
            created=created,
            request_id=request_id,
            route_target=route_decision.target,
            route_reason=route_decision.reason,
        )
        return StreamingCompletionEnvelope(stream=stream, metadata=stream_metadata)

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

    async def _stream_provider(
        self,
        provider: CompletionProvider,
        request: ChatCompletionRequest,
        prompt: str,
        response_id: str,
        created: int,
        request_id: str | None,
        stream_state: dict[str, bool],
    ):
        content_parts: list[str] = []
        started_at = perf_counter()

        try:
            async for chunk in provider.stream_complete(request):
                if chunk.delta:
                    stream_state["started"] = True
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
                    stream_state["started"] = True
                    await self.cache_service.store(prompt, "".join(content_parts), chunk.model)
                    COMPLETION_COUNT.labels(provider.name, "ok", "true").inc()
                    PROVIDER_LATENCY.labels(provider.name, "stream", "ok").observe(
                        perf_counter() - started_at
                    )
                    logger.info(
                        "provider_completed request_id=%s provider=%s mode=stream latency_ms=%.2f",
                        request_id,
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

        logger.warning("stream_terminated_without_finish request_id=%s provider=%s", request_id, provider.name)
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
        route_target: Literal["local", "premium"],
        route_reason: str,
    ) -> tuple[AsyncIterator[bytes], CompletionMetadata]:
        try:
            stream = await self._prefetched_stream(
                provider=provider,
                request=request,
                prompt=prompt,
                response_id=response_id,
                created=created,
                request_id=request_id,
            )
            return (
                stream,
                CompletionMetadata(
                    route_target=route_target,
                    route_reason=route_reason,
                    provider=provider.name,
                    cache_hit=False,
                    fallback_used=False,
                ),
            )
        except ProviderError as exc:
            if route_target != "local":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc

            logger.warning("stream_fallback request_id=%s error=%s", request_id, exc)
            FALLBACK_COUNT.labels("local_provider_error").inc()
            fallback_provider = self.provider_registry.get("premium")
            logger.info(
                "fallback_selected request_id=%s stream=true provider=%s",
                request_id,
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
                )
            except ProviderError as fallback_exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(fallback_exc),
                ) from fallback_exc

            return (
                fallback_stream,
                CompletionMetadata(
                    route_target="premium",
                    route_reason="local_provider_error_fallback",
                    provider=fallback_provider.name,
                    cache_hit=False,
                    fallback_used=True,
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
    ) -> AsyncIterator[bytes]:
        stream_state = {"started": False}
        provider_stream = self._stream_provider(
            provider=provider,
            request=request,
            prompt=prompt,
            response_id=response_id,
            created=created,
            request_id=request_id,
            stream_state=stream_state,
        )

        try:
            first_event = await provider_stream.__anext__()
        except StopAsyncIteration:
            async def empty_stream():
                yield self._assistant_role_chunk(response_id=response_id, created=created, model=request.model)
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
            "provider_completed request_id=%s provider=%s mode=completion latency_ms=%.2f",
            request_id,
            provider.name,
            (perf_counter() - started_at) * 1000,
        )
        return result

    def _extract_model_from_sse(self, payload: bytes) -> str | None:
        prefix = b"data: "
        if not payload.startswith(prefix):
            return None
        body = payload[len(prefix) :].strip()
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError:
            return None
        return decoded.get("model")
