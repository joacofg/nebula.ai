import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from nebula.observability.logging import reset_request_id, set_request_id
from nebula.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        request.state.request_id = request_id
        token = set_request_id(request_id)
        started_at = perf_counter()
        response = None

        try:
            response = await call_next(request)
            return response
        finally:
            elapsed = perf_counter() - started_at
            path = request.url.path
            status_code = getattr(response, "status_code", 500)
            REQUEST_COUNT.labels(request.method, path, str(status_code)).inc()
            REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
            logger.info("request_completed", extra={"request_id": request_id})
            reset_request_id(token)
            if response is not None:
                response.headers["X-Request-ID"] = request_id
