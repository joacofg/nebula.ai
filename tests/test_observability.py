from __future__ import annotations

import json
import logging
import sys

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY
from starlette.requests import Request
from starlette.routing import Route

from nebula.observability.logging import JsonFormatter
from nebula.observability.middleware import UNMATCHED_PATH, route_template
from tests.support import admin_headers, configured_app


def _record(**overrides) -> logging.LogRecord:
    record = logging.LogRecord("nebula.test", logging.ERROR, __file__, 1, "it failed", None, None)
    for key, value in overrides.items():
        setattr(record, key, value)
    return record


def test_json_formatter_includes_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = _record(exc_info=sys.exc_info())

    payload = json.loads(JsonFormatter().format(record))

    assert "Traceback" in payload["exc_info"]
    assert "ValueError: boom" in payload["exc_info"]


def test_json_formatter_includes_stack_info() -> None:
    payload = json.loads(JsonFormatter().format(_record(stack_info="Stack (most recent call last):")))

    assert payload["stack_info"] == "Stack (most recent call last):"


def test_json_formatter_omits_exc_info_for_an_empty_exception_tuple() -> None:
    # `logger.error(..., exc_info=True)` outside an except block records (None, None, None).
    payload = json.loads(JsonFormatter().format(_record(exc_info=(None, None, None))))

    assert "exc_info" not in payload


def test_json_formatter_omits_the_keys_when_there_is_no_exception() -> None:
    payload = json.loads(JsonFormatter().format(_record()))

    assert "exc_info" not in payload
    assert "stack_info" not in payload


def _request_count(method: str, path: str, status_code: int) -> float:
    value = REGISTRY.get_sample_value(
        "nebula_http_requests_total",
        {"method": method, "path": path, "status_code": str(status_code)},
    )
    return value or 0.0


def test_metrics_path_label_uses_route_template() -> None:
    template = "/v1/admin/tenants/{tenant_id}"
    before = _request_count("GET", template, 404)
    with configured_app() as app:
        with TestClient(app) as client:
            for tenant_id in ("tenant-aaa-111", "tenant-bbb-222"):
                client.get(f"/v1/admin/tenants/{tenant_id}", headers=admin_headers())
            raw_counts = [
                _request_count("GET", f"/v1/admin/tenants/{tenant_id}", 404)
                for tenant_id in ("tenant-aaa-111", "tenant-bbb-222")
            ]

    assert _request_count("GET", template, 404) - before == 2
    assert raw_counts == [0.0, 0.0]


def test_metrics_path_label_unmatched() -> None:
    before = _request_count("GET", UNMATCHED_PATH, 404)
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/nope/123")
            raw_count = _request_count("GET", "/nope/123", 404)

    assert response.status_code == 404
    assert _request_count("GET", UNMATCHED_PATH, 404) - before == 1
    assert raw_count == 0.0


def test_metrics_path_label_names_a_mounted_app() -> None:
    before = _request_count("GET", "/metrics", 200)
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/metrics/")
            raw_count = _request_count("GET", "/metrics/", 200)

    assert response.status_code == 200
    assert _request_count("GET", "/metrics", 200) - before == 1
    assert raw_count == 0.0


def _request(path: str, **scope) -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": [], **scope})


async def _endpoint(request: Request) -> None:  # pragma: no cover - never called
    return None


def test_route_template_falls_back_to_the_route_path_without_a_path_format() -> None:
    class BareRoute:
        path = "/bare/{item}"

    assert route_template(_request("/bare/7", route=BareRoute())) == "/bare/{item}"


def test_route_template_falls_back_to_the_route_path_when_the_suffix_does_not_match() -> None:
    route = Route("/items/{item_id}", _endpoint)
    request = _request("/rewritten/elsewhere", route=route, path_params={"item_id": "7"})

    assert route_template(request) == "/items/{item_id}"


def test_route_template_keeps_a_prefix_the_route_path_lacks() -> None:
    route = Route("/items/{item_id}", _endpoint)
    request = _request("/v1/items/7", route=route, path_params={"item_id": "7"})

    assert route_template(request) == "/v1/items/{item_id}"
