from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from nebula.api.dependencies import require_admin
from nebula.api.routes.chat import _nebula_headers
from nebula.core.container import ServiceContainer
from nebula.models.governance import (
    AdminSessionStatus,
    AdminPlaygroundRequest,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyRecord,
    PolicyOptionsResponse,
    PlaygroundResponse,
    TenantCreateRequest,
    TenantPolicy,
    TenantRecord,
    TenantUpdateRequest,
    UsageLedgerRecord,
)
from nebula.models.openai import ChatCompletionRequest

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/session", response_model=AdminSessionStatus)
async def get_admin_session(
    container: ServiceContainer = Depends(require_admin),
) -> AdminSessionStatus:
    return AdminSessionStatus(status="ok")


@router.get("/tenants", response_model=list[TenantRecord])
async def list_tenants(
    container: ServiceContainer = Depends(require_admin),
) -> list[TenantRecord]:
    return container.governance_store.list_tenants()


@router.post("/tenants", response_model=TenantRecord, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreateRequest,
    container: ServiceContainer = Depends(require_admin),
) -> TenantRecord:
    return container.governance_store.create_tenant(
        tenant_id=payload.id,
        name=payload.name,
        description=payload.description,
        metadata=payload.metadata,
        active=payload.active,
        policy=payload.policy,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantRecord)
async def get_tenant(
    tenant_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> TenantRecord:
    tenant = container.governance_store.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return tenant


@router.patch("/tenants/{tenant_id}", response_model=TenantRecord)
async def update_tenant(
    tenant_id: str,
    payload: TenantUpdateRequest,
    container: ServiceContainer = Depends(require_admin),
) -> TenantRecord:
    tenant = container.governance_store.update_tenant(
        tenant_id,
        name=payload.name,
        description=payload.description,
        metadata=payload.metadata,
        active=payload.active,
    )
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return tenant


@router.get("/tenants/{tenant_id}/policy", response_model=TenantPolicy)
async def get_tenant_policy(
    tenant_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> TenantPolicy:
    if container.governance_store.get_tenant(tenant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return container.governance_store.get_policy(tenant_id)


@router.put("/tenants/{tenant_id}/policy", response_model=TenantPolicy)
async def upsert_tenant_policy(
    tenant_id: str,
    payload: TenantPolicy,
    container: ServiceContainer = Depends(require_admin),
) -> TenantPolicy:
    if container.governance_store.get_tenant(tenant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return container.governance_store.upsert_policy(tenant_id, payload)


@router.get("/policy/options", response_model=PolicyOptionsResponse)
async def get_policy_options(
    container: ServiceContainer = Depends(require_admin),
) -> PolicyOptionsResponse:
    return PolicyOptionsResponse(
        routing_modes=["auto", "local_only", "premium_only"],
        known_premium_models=container.governance_store.list_known_premium_models(),
        default_premium_model=container.settings.premium_model,
    )


@router.get("/api-keys", response_model=list[ApiKeyRecord])
async def list_api_keys(
    tenant_id: str | None = Query(default=None),
    container: ServiceContainer = Depends(require_admin),
) -> list[ApiKeyRecord]:
    return container.governance_store.list_api_keys(tenant_id=tenant_id)


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    container: ServiceContainer = Depends(require_admin),
) -> ApiKeyCreateResponse:
    record, raw_key = container.governance_store.create_api_key(
        name=payload.name,
        tenant_id=payload.tenant_id,
        allowed_tenant_ids=payload.allowed_tenant_ids,
        raw_key=payload.key,
    )
    return ApiKeyCreateResponse(api_key=raw_key, record=record)


@router.post("/api-keys/{api_key_id}/revoke", response_model=ApiKeyRecord)
async def revoke_api_key(
    api_key_id: str,
    container: ServiceContainer = Depends(require_admin),
) -> ApiKeyRecord:
    record = container.governance_store.revoke_api_key(api_key_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    return record


@router.get("/usage/ledger", response_model=list[UsageLedgerRecord])
async def list_usage_ledger(
    request_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    terminal_status: str | None = Query(default=None),
    route_target: str | None = Query(default=None),
    from_timestamp: datetime | None = Query(default=None),
    to_timestamp: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    container: ServiceContainer = Depends(require_admin),
) -> list[UsageLedgerRecord]:
    return container.governance_store.list_usage_records(
        request_id=request_id,
        tenant_id=tenant_id,
        terminal_status=terminal_status,
        route_target=route_target,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        limit=limit,
    )


@router.post("/playground/completions", response_model=PlaygroundResponse)
async def create_playground_completion(
    payload: AdminPlaygroundRequest,
    request: Request,
    response: Response,
    container: ServiceContainer = Depends(require_admin),
) -> PlaygroundResponse:
    if payload.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playground only supports non-streaming requests in Phase 3.",
        )

    tenant_context = container.auth_service.resolve_playground_context(payload.tenant_id)
    request_id = getattr(request.state, "request_id", None)
    completion_envelope = await container.chat_service.create_completion_with_metadata(
        ChatCompletionRequest.model_validate(payload.model_dump(exclude={"tenant_id"})),
        tenant_context=tenant_context,
        request_id=request_id,
    )
    response.headers["X-Request-ID"] = request_id or ""
    response.headers.update(_nebula_headers(completion_envelope.metadata))
    return PlaygroundResponse(
        **completion_envelope.response.model_dump(),
        request_id=request_id,
    )
