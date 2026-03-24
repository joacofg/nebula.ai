from fastapi import Header, Request

from nebula.core.container import ServiceContainer
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
