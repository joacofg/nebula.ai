from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from nebula.models.deployment import (
    RemoteActionCompletionRequest,
    RemoteActionCompletionResponse,
    RemoteActionPollResponse,
)

remote_management_router = APIRouter(prefix="/remote-actions", tags=["remote-management"])


def _deployment_credential(request: Request) -> str:
    credential = request.headers.get("X-Nebula-Deployment-Credential")
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unknown deployment credential.",
        )
    return credential


@remote_management_router.post("/poll", response_model=RemoteActionPollResponse)
async def poll_remote_actions(request: Request) -> RemoteActionPollResponse:
    container = request.app.state.container
    credential = _deployment_credential(request)
    if not container.enrollment_service.validate_deployment_credential(credential):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unknown deployment credential.",
        )
    action = container.enrollment_service.claim_next_remote_action(credential)
    return RemoteActionPollResponse(action=action)


@remote_management_router.post(
    "/{action_id}/complete",
    response_model=RemoteActionCompletionResponse,
)
async def complete_remote_action(
    action_id: str,
    payload: RemoteActionCompletionRequest,
    request: Request,
) -> RemoteActionCompletionResponse:
    container = request.app.state.container
    credential = _deployment_credential(request)
    result = container.enrollment_service.complete_remote_action(
        raw_credential=credential,
        action_id=action_id,
        payload=payload,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unknown deployment credential.",
        )
    return result
