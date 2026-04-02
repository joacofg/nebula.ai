from fastapi import APIRouter, Depends, Request, Response, status
from starlette.responses import StreamingResponse

from nebula.api.dependencies import get_chat_service, get_tenant_context
from nebula.models.openai import ChatCompletionRequest, ChatCompletionResponse
from nebula.services.auth_service import AuthenticatedTenantContext
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
    tenant_context: AuthenticatedTenantContext = Depends(get_tenant_context),
) -> ChatCompletionResponse | StreamingResponse:
    request_id = getattr(request.state, "request_id", None)
    if payload.stream:
        stream_envelope = await service.stream_completion_with_metadata(
            payload,
            tenant_context=tenant_context,
            request_id=request_id,
        )
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

    completion_envelope = await service.create_completion_with_metadata(
        payload,
        tenant_context=tenant_context,
        request_id=request_id,
    )
    response.headers.update(_nebula_headers(completion_envelope.metadata))
    return completion_envelope.response


def _nebula_headers(metadata) -> dict[str, str]:
    headers = {
        "X-Nebula-Tenant-ID": metadata.tenant_id,
        "X-Nebula-Route-Target": metadata.route_target,
        "X-Nebula-Route-Reason": metadata.route_reason,
        "X-Nebula-Provider": metadata.provider,
        "X-Nebula-Route-Score": f"{metadata.route_score:.4f}",
        "X-Nebula-Cache-Hit": str(metadata.cache_hit).lower(),
        "X-Nebula-Fallback-Used": str(metadata.fallback_used).lower(),
        "X-Nebula-Policy-Mode": metadata.policy_mode,
        "X-Nebula-Policy-Outcome": metadata.policy_outcome,
    }
    if metadata.route_signals:
        route_mode = metadata.route_signals.get("route_mode")
        if route_mode is not None:
            headers["X-Nebula-Route-Mode"] = str(route_mode)
    return headers
