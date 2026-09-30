from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, Response, status

from nebula.core.container import ServiceContainer
from nebula.models.governance import UsageLedgerRecord
from nebula.observability.metrics import RATE_LIMITED_COUNT
from nebula.services.auth_service import (
    ADMIN_API_KEY_HEADER,
    API_KEY_HEADER,
    TENANT_HEADER,
    AuthenticatedTenantContext,
)
from nebula.services.chat_service import ChatService
from nebula.services.embeddings_service import OllamaEmbeddingsService


def get_container(request_or_app) -> ServiceContainer:
    app = request_or_app.app if isinstance(request_or_app, Request) else request_or_app
    return app.state.container


def get_chat_service(request: Request) -> ChatService:
    return get_container(request).chat_service


def get_embeddings_service(request: Request) -> OllamaEmbeddingsService:
    return get_container(request).embeddings_service


def get_tenant_context(
    request: Request,
    api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
    tenant_id: str | None = Header(default=None, alias=TENANT_HEADER),
) -> AuthenticatedTenantContext:
    container = get_container(request)
    return container.auth_service.resolve_tenant_context(
        raw_api_key=api_key,
        explicit_tenant_id=tenant_id,
    )


def require_admin(
    request: Request,
    admin_api_key: str | None = Header(default=None, alias=ADMIN_API_KEY_HEADER),
) -> ServiceContainer:
    container = get_container(request)
    container.auth_service.authenticate_admin(admin_api_key)
    return container


def _rate_limit_headers(result) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_seconds),
    }


async def get_rate_limited_tenant_context(
    request: Request,
    response: Response,
    tenant_context: AuthenticatedTenantContext = Depends(get_tenant_context),
) -> AuthenticatedTenantContext:
    """Authenticate, then spend one of the tenant's requests for this minute.

    Runs before routing, so a rejected request costs neither an embedding nor a model call.
    """
    limit = tenant_context.policy.rate_limit_requests_per_minute
    if limit is None:
        return tenant_context
    container = get_container(request)
    tenant_id = tenant_context.tenant.id
    result = await container.rate_limiter.acquire(tenant_id, limit_per_minute=limit)
    headers = _rate_limit_headers(result)
    request.state.rate_limit_headers = headers
    if result.allowed:
        response.headers.update(headers)
        return tenant_context

    RATE_LIMITED_COUNT.labels(tenant_id).inc()
    try:
        body = await request.json()
        requested_model = str(body.get("model") or "unknown") if isinstance(body, dict) else "unknown"
    except Exception:  # noqa: BLE001 - a malformed body is still a rate-limited request
        requested_model = "unknown"
    request_id = getattr(request.state, "request_id", None) or f"req-{uuid4().hex}"
    container.governance_store.record_usage(
        UsageLedgerRecord(
            request_id=request_id,
            tenant_id=tenant_id,
            requested_model=requested_model,
            final_route_target="denied",
            final_provider="none",
            fallback_used=False,
            cache_hit=False,
            response_model=None,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=None,
            latency_ms=None,
            timestamp=datetime.now(UTC),
            terminal_status="rate_limited",
            route_reason="rate_limited",
            policy_outcome=f"rate_limit={limit}/min",
            message_type="embeddings" if request.url.path.endswith("/embeddings") else "chat",
        )
    )
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Tenant rate limit of {limit} requests per minute exceeded.",
        headers={
            **headers,
            "Retry-After": str(result.retry_after_seconds),
            "X-Nebula-Tenant-ID": tenant_id,
            "X-Nebula-Route-Target": "denied",
            "X-Nebula-Route-Reason": "rate_limited",
            "X-Nebula-Route-Tier": "denied",
        },
    )
