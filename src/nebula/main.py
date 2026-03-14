from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from nebula.api.dependencies import get_container
from nebula.api.routes.chat import router as chat_router
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
    app.state.container = container
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
    if settings.enable_metrics:
        app.mount("/metrics", make_asgi_app())

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        container = get_container(app)
        return {"status": "ok", "cache_enabled": str(container.cache_service.enabled).lower()}

    return app


app = create_app()
