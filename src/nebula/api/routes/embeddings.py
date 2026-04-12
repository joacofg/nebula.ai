from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from nebula.api.dependencies import get_embeddings_service, get_tenant_context
from nebula.core.container import ServiceContainer
from nebula.models.governance import UsageLedgerRecord
from nebula.models.openai import EmbeddingsResponse, EmbeddingsUsage, EmbeddingsRequest, EmbeddingData
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.embeddings_service import (
    EmbeddingsEmptyResultError,
    EmbeddingsUpstreamError,
    EmbeddingsValidationError,
    OllamaEmbeddingsService,
)

router = APIRouter(tags=["embeddings"])


@router.post(
    "/embeddings",
    response_model=EmbeddingsResponse,
    status_code=status.HTTP_200_OK,
)
async def create_embeddings(
    payload: EmbeddingsRequest,
    request: Request,
    response: Response,
    service: OllamaEmbeddingsService = Depends(get_embeddings_service),
    tenant_context: AuthenticatedTenantContext = Depends(get_tenant_context),
) -> EmbeddingsResponse:
    container = request.app.state.container
    request_id = getattr(request.state, "request_id", None)
    try:
        result = await service.create_embeddings(model=payload.model, input=payload.input)
    except EmbeddingsValidationError as exc:
        _record_usage(
            container=container,
            tenant_context=tenant_context,
            request_id=request_id,
            requested_model=payload.model,
            response_model=None,
            terminal_status="provider_error",
            route_reason="embeddings_validation_error",
            policy_outcome=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except EmbeddingsUpstreamError as exc:
        _record_usage(
            container=container,
            tenant_context=tenant_context,
            request_id=request_id,
            requested_model=payload.model,
            response_model=None,
            terminal_status="provider_error",
            route_reason="embeddings_upstream_error",
            policy_outcome=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except EmbeddingsEmptyResultError as exc:
        _record_usage(
            container=container,
            tenant_context=tenant_context,
            request_id=request_id,
            requested_model=payload.model,
            response_model=None,
            terminal_status="provider_error",
            route_reason="embeddings_empty_result",
            policy_outcome=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    _record_usage(
        container=container,
        tenant_context=tenant_context,
        request_id=request_id,
        requested_model=payload.model,
        response_model=result.model,
        terminal_status="completed",
        route_reason="embeddings_direct",
        policy_outcome="embeddings=completed",
    )
    response.headers["X-Nebula-Tenant-ID"] = tenant_context.tenant.id
    response.headers["X-Nebula-Route-Target"] = "embeddings"
    response.headers["X-Nebula-Route-Reason"] = "embeddings_direct"
    response.headers["X-Nebula-Provider"] = "ollama"
    response.headers["X-Nebula-Cache-Hit"] = "false"
    response.headers["X-Nebula-Fallback-Used"] = "false"
    response.headers["X-Nebula-Policy-Mode"] = "embeddings_direct"
    response.headers["X-Nebula-Policy-Outcome"] = "embeddings=completed"
    return EmbeddingsResponse(
        data=[EmbeddingData(index=item.index, embedding=item.embedding) for item in result.data],
        model=result.model,
        usage=EmbeddingsUsage(prompt_tokens=0, total_tokens=0),
    )


def _record_usage(
    *,
    container: ServiceContainer,
    tenant_context: AuthenticatedTenantContext,
    request_id: str | None,
    requested_model: str,
    response_model: str | None,
    terminal_status: str,
    route_reason: str,
    policy_outcome: str,
) -> None:
    container.governance_store.record_usage(
        UsageLedgerRecord(
            request_id=request_id or f"req-{uuid4().hex}",
            tenant_id=tenant_context.tenant.id,
            requested_model=requested_model,
            final_route_target="embeddings",
            final_provider="ollama",
            fallback_used=False,
            cache_hit=False,
            response_model=response_model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            latency_ms=None,
            timestamp=datetime.now(UTC),
            terminal_status=terminal_status,
            route_reason=route_reason,
            policy_outcome=policy_outcome,
            message_type="embeddings",
        )
    )
