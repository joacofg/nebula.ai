from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from nebula.api.dependencies import require_admin
from nebula.core.container import ServiceContainer
from nebula.models.deployment import (
    DeploymentCreateRequest,
    DeploymentRecord,
    EnrollmentExchangeRequest,
    EnrollmentExchangeResponse,
    EnrollmentTokenResponse,
)

router = APIRouter(prefix="/admin/deployments", tags=["deployments"])

# Separate router for gateway-facing enrollment exchange (no auth required)
exchange_router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@exchange_router.post("/exchange", response_model=EnrollmentExchangeResponse)
async def enrollment_exchange(
    request: Request,
    body: EnrollmentExchangeRequest,
) -> EnrollmentExchangeResponse:
    container = request.app.state.container
    result = container.enrollment_service.consume_enrollment_token(
        raw_token=body.enrollment_token,
        nebula_version=body.nebula_version,
        capability_flags=body.capability_flags,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or already-consumed enrollment token",
        )
    return result


@router.post("/", response_model=DeploymentRecord, status_code=status.HTTP_201_CREATED)
async def create_deployment_slot(
    body: DeploymentCreateRequest,
    container: ServiceContainer = Depends(require_admin),
) -> DeploymentRecord:
    return container.enrollment_service.create_deployment_slot(
        body.display_name, body.environment
    )


@router.get("/", response_model=list[DeploymentRecord])
async def list_deployments(
    container: ServiceContainer = Depends(require_admin),
) -> list[DeploymentRecord]:
    return container.enrollment_service.list_deployments()


@router.get("/{deployment_id}", response_model=DeploymentRecord)
async def get_deployment(
    deployment_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> DeploymentRecord:
    record = container.enrollment_service.get_deployment(deployment_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found."
        )
    return record


@router.post("/{deployment_id}/revoke", response_model=DeploymentRecord)
async def revoke_deployment(
    deployment_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> DeploymentRecord:
    try:
        result = container.enrollment_service.revoke_deployment(deployment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found.")
    return result


@router.post("/{deployment_id}/unlink", response_model=DeploymentRecord)
async def unlink_deployment(
    deployment_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> DeploymentRecord:
    try:
        result = container.enrollment_service.unlink_deployment(deployment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found.")
    return result


@router.post("/{deployment_id}/enrollment-token", response_model=EnrollmentTokenResponse)
async def generate_token(
    deployment_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> EnrollmentTokenResponse:
    try:
        return container.enrollment_service.generate_enrollment_token(deployment_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found."
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deployment is already active. Unlink or revoke it first.",
        )
