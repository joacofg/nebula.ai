from __future__ import annotations

import json
import logging
import sys

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from nebula.observability.logging import JsonFormatter
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


def test_json_formatter_omits_the_keys_when_there_is_no_exception() -> None:
    payload = json.loads(JsonFormatter().format(_record()))

    assert "exc_info" not in payload
    assert "stack_info" not in payload


def _request_count_paths() -> set[str]:
    return {
        sample.labels["path"]
        for metric in REGISTRY.collect()
        if metric.name == "nebula_http_requests"
        for sample in metric.samples
        if sample.name == "nebula_http_requests_total"
    }


def test_metrics_path_label_uses_route_template() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            for tenant_id in ("tenant-aaa-111", "tenant-bbb-222"):
                client.get(f"/v1/admin/tenants/{tenant_id}", headers=admin_headers())
            paths = _request_count_paths()

    assert "/v1/admin/tenants/{tenant_id}" in paths
    assert not {"/v1/admin/tenants/tenant-aaa-111", "/v1/admin/tenants/tenant-bbb-222"} & paths


def test_metrics_path_label_unmatched() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/nope/123")
            paths = _request_count_paths()

    assert response.status_code == 404
    assert "unmatched" in paths
    assert "/nope/123" not in paths
