from __future__ import annotations

import json
import logging
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
from nebula.observability.metrics import COMPLETION_COUNT, FALLBACK_COUNT
from nebula.providers.base import CompletionProvider, ProviderError
from nebula.services.provider_registry import ProviderRegistry
from nebula.services.router_service import RouterService
from nebula.services.semantic_cache_service import SemanticCacheService

logger = logging.getLogger(__name__)


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
        latest_user_prompt = self._extract_latest_user_prompt(request)
        cached_response = await self.cache_service.lookup(latest_user_prompt)
        if cached_response:
            COMPLETION_COUNT.labels("cache", "ok", "false").inc()
            return self._build_response(
                content=cached_response,
                model="nebula-cache",
            )

        target = await self.router_service.choose_target(latest_user_prompt, request)
        provider = self.provider_registry.get(target)
        try:
            result = await provider.complete(request)
            COMPLETION_COUNT.labels(provider.name, "ok", "false").inc()
        except ProviderError as exc:
            logger.warning("provider_failed request_id=%s provider=%s error=%s", request_id, provider.name, exc)
            if target != "local":
                COMPLETION_COUNT.labels(provider.name, "error", "false").inc()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc
            fallback_provider = self.provider_registry.get("premium")
            FALLBACK_COUNT.labels("local_provider_error").inc()
            result = await fallback_provider.complete(request)
            COMPLETION_COUNT.labels(fallback_provider.name, "fallback", "false").inc()

        await self.cache_service.store(latest_user_prompt, result.content, result.model)
        return self._build_response(content=result.content, model=result.model)

    async def stream_completion(
        self,
        request: ChatCompletionRequest,
        request_id: str | None = None,
    ):
        latest_user_prompt = self._extract_latest_user_prompt(request)
        cached_response = await self.cache_service.lookup(latest_user_prompt)
        response_id = f"chatcmpl-{uuid4().hex}"
        created = int(time())

        yield self._sse(
            ChatCompletionChunk(
                id=response_id,
                created=created,
                model="nebula-cache" if cached_response else request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionStreamDelta(role="assistant"),
                    )
                ],
            )
        )

        if cached_response:
            COMPLETION_COUNT.labels("cache", "ok", "true").inc()
            async for event in self._stream_text(cached_response, response_id, created, "nebula-cache"):
                yield event
            return

        target = await self.router_service.choose_target(latest_user_prompt, request)
        stream_state = {"started": False}
        try:
            async for event in self._stream_provider(
                provider=self.provider_registry.get(target),
                request=request,
                prompt=latest_user_prompt,
                response_id=response_id,
                created=created,
                request_id=request_id,
                stream_state=stream_state,
            ):
                yield event
            return
        except ProviderError as exc:
            if stream_state["started"]:
                logger.warning("stream_partial_failure request_id=%s error=%s", request_id, exc)
                yield b"data: [DONE]\n\n"
                return
            if target != "local":
                COMPLETION_COUNT.labels("premium", "error", "true").inc()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc

            logger.warning("stream_fallback request_id=%s error=%s", request_id, exc)
            FALLBACK_COUNT.labels("local_provider_error").inc()
            async for event in self._stream_provider(
                provider=self.provider_registry.get("premium"),
                request=request,
                prompt=latest_user_prompt,
                response_id=response_id,
                created=created,
                request_id=request_id,
                stream_state=stream_state,
            ):
                yield event

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

    def _build_response(self, content: str, model: str) -> ChatCompletionResponse:
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
            usage=ChatCompletionUsage(),
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
            raise
        except Exception as exc:
            COMPLETION_COUNT.labels(provider.name, "error", "true").inc()
            raise ProviderError(f"Streaming failed for {provider.name}: {exc}") from exc

        logger.warning("stream_terminated_without_finish request_id=%s provider=%s", request_id, provider.name)
        yield b"data: [DONE]\n\n"

    async def _stream_text(self, text: str, response_id: str, created: int, model: str):
        chunk_size = 24
        for start in range(0, len(text), chunk_size):
            delta = text[start : start + chunk_size]
            yield self._sse(
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

        yield self._sse(
            ChatCompletionChunk(
                id=response_id,
                created=created,
                model=model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionStreamDelta(),
                        finish_reason="stop",
                    )
                ],
            )
        )
        yield b"data: [DONE]\n\n"

    def _sse(self, chunk: ChatCompletionChunk) -> bytes:
        return f"data: {json.dumps(chunk.model_dump(mode='json'))}\n\n".encode("utf-8")
