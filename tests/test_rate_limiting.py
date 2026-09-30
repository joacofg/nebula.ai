from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from nebula.models.governance import TenantPolicy
from tests.support import admin_headers, configured_app


def test_rate_limit_defaults_to_unlimited_and_rejects_nonsense() -> None:
    assert TenantPolicy().rate_limit_requests_per_minute is None
    assert TenantPolicy(rate_limit_requests_per_minute=60).rate_limit_requests_per_minute == 60
    for bad in (0, -1, 100_001):
        with pytest.raises(ValidationError):
            TenantPolicy(rate_limit_requests_per_minute=bad)


def test_store_round_trips_the_rate_limit_and_options_list_it() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            store = app.state.container.governance_store
            store.upsert_policy("default", TenantPolicy(rate_limit_requests_per_minute=30))
            reread = store.get_policy("default")
            options = client.get("/v1/admin/policy/options", headers=admin_headers()).json()

    assert reread.rate_limit_requests_per_minute == 30
    assert "rate_limit_requests_per_minute" in options["runtime_enforced_fields"]
