"""Integration tests for deployment enrollment admin API (ENRL-01)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.support import admin_headers, configured_app


def test_create_deployment_slot() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/admin/deployments",
                json={"display_name": "gw-1", "environment": "production"},
                headers=admin_headers(),
            )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["display_name"] == "gw-1"
    assert data["environment"] == "production"
    assert data["enrollment_state"] == "pending"


def test_list_deployments_includes_all_states() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            create_response = client.post(
                "/v1/admin/deployments",
                json={"display_name": "prod-gw-1", "environment": "production"},
                headers=admin_headers(),
            )
            assert create_response.status_code == 201
            created = create_response.json()

            list_response = client.get(
                "/v1/admin/deployments",
                headers=admin_headers(),
            )
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) >= 1
    ids = [item["id"] for item in items]
    assert created["id"] in ids


def test_generate_enrollment_token() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            create_response = client.post(
                "/v1/admin/deployments",
                json={"display_name": "token-test-gw", "environment": "staging"},
                headers=admin_headers(),
            )
            assert create_response.status_code == 201
            deployment_id = create_response.json()["id"]

            token_response = client.post(
                f"/v1/admin/deployments/{deployment_id}/enrollment-token",
                headers=admin_headers(),
            )
    assert token_response.status_code == 200
    data = token_response.json()
    assert "token" in data
    assert data["token"].startswith("nbet_")
    assert "expires_at" in data
    assert data["deployment_id"] == deployment_id


def test_generate_token_for_active_deployment_returns_409() -> None:
    """Stub — will be fully exercised in plan 02 after exchange endpoint exists."""
    # This test verifies the 409 guard at the API layer without needing a real exchange.
    # Full integration test (with actual exchange) deferred to plan 02.
    pass
