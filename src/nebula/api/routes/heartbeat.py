from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from nebula.models.heartbeat import HeartbeatRequest, HeartbeatResponse

heartbeat_router = APIRouter(prefix="/heartbeat", tags=["heartbeat"])


@heartbeat_router.post("", response_model=HeartbeatResponse)
async def receive_heartbeat(request: Request, body: HeartbeatRequest) -> HeartbeatResponse:
    container = request.app.state.container
    credential = request.headers.get("X-Nebula-Deployment-Credential")
    success = container.heartbeat_ingest_service.record_heartbeat(
        raw_credential=credential,
        nebula_version=body.nebula_version,
        capability_flags=body.capability_flags,
        dependency_summary=body.dependency_summary,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unknown deployment credential.",
        )
    return HeartbeatResponse(acknowledged=True)
