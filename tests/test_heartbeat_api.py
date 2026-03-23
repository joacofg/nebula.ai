"""Integration tests for heartbeat endpoint and last_seen_at updates (INVT-01, INVT-02, INVT-04)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.support import admin_headers, configured_app


def _make_active_deployment_with_credential(
    client: TestClient,
    display_name: str = "heartbeat-gw",
    environment: str = "production",
) -> tuple[str, str]:
    """Create a deployment slot, exchange enrollment token, return (deployment_id, deployment_credential)."""
    create_resp = client.post(
        "/v1/admin/deployments",
        json={"display_name": display_name, "environment": environment},
        headers=admin_headers(),
    )
    assert create_resp.status_code == 201
    deployment_id = create_resp.json()["id"]

    token_resp = client.post(
        f"/v1/admin/deployments/{deployment_id}/enrollment-token",
        headers=admin_headers(),
    )
    assert token_resp.status_code == 200
    raw_token = token_resp.json()["token"]

    exchange_resp = client.post(
        "/v1/enrollment/exchange",
        json={
            "enrollment_token": raw_token,
            "nebula_version": "2.0.0",
            "capability_flags": ["semantic_cache"],
        },
    )
    assert exchange_resp.status_code == 200
    deployment_credential = exchange_resp.json()["deployment_credential"]

    return deployment_id, deployment_credential


def _heartbeat_headers(credential: str) -> dict[str, str]:
    return {"X-Nebula-Deployment-Credential": credential}


def _default_heartbeat_body() -> dict:
    return {
        "nebula_version": "2.0.0",
        "capability_flags": ["semantic_cache", "local_provider"],
        "dependency_summary": {
            "healthy": ["gateway", "governance_store"],
            "degraded": [],
            "unavailable": [],
        },
    }


# ---------------------------------------------------------------------------
# Authentication tests
# ---------------------------------------------------------------------------


def test_heartbeat_valid_credential() -> None:
    """POST /v1/heartbeat with valid credential returns 200 + acknowledged=true."""
    with configured_app() as app:
        with TestClient(app) as client:
            _, credential = _make_active_deployment_with_credential(client)

            response = client.post(
                "/v1/heartbeat",
                json=_default_heartbeat_body(),
                headers=_heartbeat_headers(credential),
            )
    assert response.status_code == 200
    assert response.json()["acknowledged"] is True


def test_heartbeat_invalid_credential() -> None:
    """POST /v1/heartbeat with an invalid credential returns 401."""
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/heartbeat",
                json=_default_heartbeat_body(),
                headers=_heartbeat_headers("bad-credential"),
            )
    assert response.status_code == 401


def test_heartbeat_no_credential() -> None:
    """POST /v1/heartbeat without the credential header returns 401."""
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/heartbeat",
                json=_default_heartbeat_body(),
            )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# INVT-01: Heartbeat updates last_seen_at
# ---------------------------------------------------------------------------


def test_heartbeat_updates_last_seen_at() -> None:
    """After heartbeat, GET deployment returns non-null last_seen_at (INVT-01)."""
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, credential = _make_active_deployment_with_credential(client)

            # Confirm last_seen_at is null before heartbeat
            pre_resp = client.get(
                f"/v1/admin/deployments/{deployment_id}",
                headers=admin_headers(),
            )
            assert pre_resp.status_code == 200
            assert pre_resp.json()["last_seen_at"] is None

            # Send heartbeat
            client.post(
                "/v1/heartbeat",
                json=_default_heartbeat_body(),
                headers=_heartbeat_headers(credential),
            )

            # Confirm last_seen_at is now set
            post_resp = client.get(
                f"/v1/admin/deployments/{deployment_id}",
                headers=admin_headers(),
            )
    assert post_resp.status_code == 200
    assert post_resp.json()["last_seen_at"] is not None


# ---------------------------------------------------------------------------
# INVT-02: Freshness is "connected" immediately after heartbeat
# ---------------------------------------------------------------------------


def test_heartbeat_freshness_connected() -> None:
    """After heartbeat, freshness_status is 'connected' (INVT-02)."""
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, credential = _make_active_deployment_with_credential(
                client, display_name="freshness-gw"
            )

            client.post(
                "/v1/heartbeat",
                json=_default_heartbeat_body(),
                headers=_heartbeat_headers(credential),
            )

            resp = client.get(
                f"/v1/admin/deployments/{deployment_id}",
                headers=admin_headers(),
            )
    assert resp.status_code == 200
    deployment = resp.json()
    assert deployment["freshness_status"] == "connected"


# ---------------------------------------------------------------------------
# INVT-04: Heartbeat updates capability_flags
# ---------------------------------------------------------------------------


def test_heartbeat_updates_capability_flags() -> None:
    """Heartbeat updates capability_flags on existing active deployment (INVT-04)."""
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, credential = _make_active_deployment_with_credential(
                client, display_name="flags-gw"
            )

            updated_flags = ["semantic_cache", "premium_routing", "local_provider"]
            client.post(
                "/v1/heartbeat",
                json={
                    "nebula_version": "2.1.0",
                    "capability_flags": updated_flags,
                    "dependency_summary": {
                        "healthy": ["gateway"],
                        "degraded": [],
                        "unavailable": [],
                    },
                },
                headers=_heartbeat_headers(credential),
            )

            resp = client.get(
                f"/v1/admin/deployments/{deployment_id}",
                headers=admin_headers(),
            )
    assert resp.status_code == 200
    deployment = resp.json()
    assert set(deployment["capability_flags"]) == set(updated_flags)


# ---------------------------------------------------------------------------
# Dependency summary update
# ---------------------------------------------------------------------------


def test_heartbeat_updates_dependency_summary() -> None:
    """Heartbeat updates dependency_summary_json on deployment."""
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, credential = _make_active_deployment_with_credential(
                client, display_name="dep-summary-gw"
            )

            dep_summary = {
                "healthy": ["gateway"],
                "degraded": [],
                "unavailable": [],
            }
            client.post(
                "/v1/heartbeat",
                json={
                    "nebula_version": "2.0.0",
                    "capability_flags": ["local_provider"],
                    "dependency_summary": dep_summary,
                },
                headers=_heartbeat_headers(credential),
            )

            resp = client.get(
                f"/v1/admin/deployments/{deployment_id}",
                headers=admin_headers(),
            )
    assert resp.status_code == 200
    deployment = resp.json()
    assert deployment["dependency_summary"] == dep_summary
