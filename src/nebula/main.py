from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from nebula.api.dependencies import get_container
from nebula.api.routes.admin import router as admin_router
from nebula.api.routes.chat import router as chat_router
from nebula.api.routes.enrollment import exchange_router, router as enrollment_router
from nebula.api.routes.heartbeat import heartbeat_router
from nebula.api.routes.remote_management import remote_management_router
from nebula.core.config import get_settings
from nebula.core.container import ServiceContainer
from nebula.observability.logging import configure_logging
from nebula.observability.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    container = ServiceContainer(settings=settings)
    await container.initialize()
    if settings.enrollment_token:
        try:
            await container.gateway_enrollment_service.attempt_enrollment(
                settings.enrollment_token
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(
                "Enrollment startup hook failed unexpectedly: %s. "
                "Gateway will start without hosted features.",
                exc,
            )
    app.state.container = container
    # Start heartbeat sender AFTER enrollment check (D-04)
    container.heartbeat_service.start()
    container.remote_management_service.start()
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
    app.include_router(chat_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router, prefix=settings.api_v1_prefix)
    app.include_router(enrollment_router, prefix=settings.api_v1_prefix)
    app.include_router(exchange_router, prefix=settings.api_v1_prefix)
    app.include_router(heartbeat_router, prefix=settings.api_v1_prefix)
    app.include_router(remote_management_router, prefix=settings.api_v1_prefix)
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
