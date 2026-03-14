from fastapi import APIRouter, Depends, Request, status
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
    service: ChatService = Depends(get_chat_service),
) -> ChatCompletionResponse | StreamingResponse:
    request_id = getattr(request.state, "request_id", None)
    if payload.stream:
        return StreamingResponse(
            service.stream_completion(payload, request_id=request_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id or "",
            },
        )

    return await service.create_completion(payload, request_id=request_id)
