from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from nebula.api.dependencies import require_admin
from nebula.core.container import ServiceContainer
from nebula.models.deployment import (
    DeploymentCreateRequest,
    DeploymentRecord,
    EnrollmentTokenResponse,
)

router = APIRouter(prefix="/admin/deployments", tags=["deployments"])


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
