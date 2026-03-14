from fastapi import APIRouter, Depends, Request, Response, status
from starlette.responses import StreamingResponse

from nebula.api.dependencies import get_chat_service
from nebula.models.openai import ChatCompletionRequest, ChatCompletionResponse
from nebula.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_200_OK,
)
async def create_chat_completion(
    payload: ChatCompletionRequest,
    request: Request,
    response: Response,
    service: ChatService = Depends(get_chat_service),
) -> ChatCompletionResponse | StreamingResponse:
    request_id = getattr(request.state, "request_id", None)
    if payload.stream:
        stream_envelope = await service.stream_completion_with_metadata(payload, request_id=request_id)
        return StreamingResponse(
            stream_envelope.stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id or "",
                **_nebula_headers(stream_envelope.metadata),
            },
        )

    completion_envelope = await service.create_completion_with_metadata(payload, request_id=request_id)
    response.headers.update(_nebula_headers(completion_envelope.metadata))
    return completion_envelope.response


def _nebula_headers(metadata) -> dict[str, str]:
    return {
        "X-Nebula-Route-Target": metadata.route_target,
        "X-Nebula-Route-Reason": metadata.route_reason,
        "X-Nebula-Provider": metadata.provider,
        "X-Nebula-Cache-Hit": str(metadata.cache_hit).lower(),
        "X-Nebula-Fallback-Used": str(metadata.fallback_used).lower(),
    }
