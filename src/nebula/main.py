from collections.abc import Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from starlette.exceptions import HTTPException as StarletteHTTPException

from nebula.api.dependencies import get_container
from nebula.api.routes.admin import router as admin_router
from nebula.api.routes.chat import router as chat_router
from nebula.api.routes.embeddings import router as embeddings_router
from nebula.core.config import get_settings
from nebula.core.container import ServiceContainer
from nebula.observability.logging import configure_logging
from nebula.observability.middleware import RequestContextMiddleware


_OPENAI_ROUTE_SUFFIXES = ("/chat/completions", "/embeddings")
_OPENAI_ERROR_TYPES = {
    400: "invalid_request_error",
    401: "authentication_error",
    403: "permission_error",
    404: "not_found_error",
    409: "conflict_error",
    422: "invalid_request_error",
    429: "rate_limit_error",
}


def _openai_error_type(status_code: int) -> str:
    if status_code >= 500:
        return "api_error"
    return _OPENAI_ERROR_TYPES.get(status_code, "invalid_request_error")


def _openai_error_response(
    request: Request,
    *,
    status_code: int,
    message: str,
    detail: object,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """OpenAI's error body, with FastAPI's `detail` kept for clients that read it.

    A raised exception discards the headers set on the injected `response`, so the
    rate-limit headers travel on request.state and are merged back in here.
    """
    merged = {**getattr(request.state, "rate_limit_headers", {}), **(headers or {})}
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": _openai_error_type(status_code),
                "code": merged.get("X-Nebula-Route-Reason"),
            },
            "detail": detail,
        },
        headers=merged,
    )


def _validation_message(errors: Sequence[Mapping[str, Any]]) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in errors
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    container = ServiceContainer(settings=settings)
    await container.initialize()
    app.state.container = container
    container.retention_lifecycle_service.start()
    try:
        yield {"settings": settings}
    finally:
        await container.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    prefix = settings.api_v1_prefix.rstrip("/")
    openai_paths = frozenset(f"{prefix}{suffix}" for suffix in _OPENAI_ROUTE_SUFFIXES)

    def is_openai_route(request: Request) -> bool:
        return request.url.path.rstrip("/") in openai_paths

    @app.exception_handler(StarletteHTTPException)
    async def openai_shaped_http_error(request: Request, exc: StarletteHTTPException):
        if not is_openai_route(request):
            return await http_exception_handler(request, exc)
        return _openai_error_response(
            request,
            status_code=exc.status_code,
            message=str(exc.detail),
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def openai_shaped_validation_error(request: Request, exc: RequestValidationError):
        if not is_openai_route(request):
            return await request_validation_exception_handler(request, exc)
        errors = jsonable_encoder(exc.errors())
        return _openai_error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message=_validation_message(errors),
            # Clients index into FastAPI's error list, so `detail` stays that list.
            detail=errors,
        )

    app.include_router(chat_router, prefix=settings.api_v1_prefix)
    app.include_router(embeddings_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router, prefix=settings.api_v1_prefix)
    if settings.enable_metrics:
        app.mount("/metrics", make_asgi_app())

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> JSONResponse:
        container = get_container(app)
        report = await container.runtime_health_service.readiness()
        status_code = 200 if report["status"] in {"ready", "degraded"} else 503
        return JSONResponse(content=report, status_code=status_code)

    @app.get("/health/dependencies", tags=["health"])
    async def health_dependencies() -> dict[str, object]:
        container = get_container(app)
        return await container.runtime_health_service.readiness()

    return app


app = create_app()
