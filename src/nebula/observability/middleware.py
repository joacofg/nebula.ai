import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.routing import replace_params

from nebula.observability.logging import reset_request_id, set_request_id
from nebula.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)

# The ledger stores request_id in a String(255) column; keep a client value well inside it.
MAX_REQUEST_ID_LENGTH = 128
# The Prometheus `path` label of a request that matched no route.
UNMATCHED_PATH = "unmatched"


def _mount_path(request: Request) -> str | None:
    """The path of the mounted app that served the request ("/metrics"), if one did.

    A Mount leaves no `route` in the scope, but it extends the scope's `root_path` beyond the
    app's own (`app_root_path`, which a proxy prefix may have set). A real 404 leaves both equal.
    """
    app_root = request.scope.get("app_root_path")
    root = request.scope.get("root_path", "")
    if app_root is None or len(root) <= len(app_root) or not root.startswith(app_root):
        return None
    return root[len(app_root) :]


def route_template(request: Request) -> str:
    """The matched route's template ("/v1/admin/tenants/{tenant_id}"), never the raw path.

    Ids in a label would grow the series without bound, and requests no route matched (404s,
    scanners) would add one series each, so those share one value. Read it after the route has
    matched: Starlette's scope dict is shared with the endpoint, which is where the route lands.
    """
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if not template:
        return _mount_path(request) or UNMATCHED_PATH
    # Newer FastAPI reports an included router's route without the `include_router` prefix, so
    # the prefix is whatever precedes the route's own path in the request path.
    path_format = getattr(route, "path_format", None)
    convertors = getattr(route, "param_convertors", None)
    if path_format is None or convertors is None:
        return template
    relative, _ = replace_params(path_format, convertors, dict(request.scope.get("path_params", {})))
    raw = request.scope["path"]
    if raw.endswith(relative):
        return raw[: len(raw) - len(relative)] + template
    return template


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))[:MAX_REQUEST_ID_LENGTH]
        request.state.request_id = request_id
        token = set_request_id(request_id)
        started_at = perf_counter()
        response = None

        try:
            response = await call_next(request)
            return response
        finally:
            elapsed = perf_counter() - started_at
            path = route_template(request)
            status_code = getattr(response, "status_code", 500)
            REQUEST_COUNT.labels(request.method, path, str(status_code)).inc()
            REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
            logger.info("request_completed", extra={"request_id": request_id})
            reset_request_id(token)
            if response is not None:
                response.headers["X-Request-ID"] = request_id
