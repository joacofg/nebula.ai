"""Integration tests for deployment enrollment admin API (ENRL-01) and exchange endpoint (ENRL-02)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
    """Verifies the 409 guard for an already-active deployment after exchange."""
    with configured_app() as app:
        with TestClient(app) as client:
            # Create slot and generate token
            create_response = client.post(
                "/v1/admin/deployments",
                json={"display_name": "active-test-gw", "environment": "production"},
                headers=admin_headers(),
            )
            assert create_response.status_code == 201
            deployment_id = create_response.json()["id"]

            token_response = client.post(
                f"/v1/admin/deployments/{deployment_id}/enrollment-token",
                headers=admin_headers(),
            )
            assert token_response.status_code == 200
            raw_token = token_response.json()["token"]

            # Exchange the token — makes deployment active
            exchange_response = client.post(
                "/v1/enrollment/exchange",
                json={
                    "enrollment_token": raw_token,
                    "nebula_version": "2.0.0",
                    "capability_flags": ["semantic_cache"],
                },
            )
            assert exchange_response.status_code == 200

            # Now try generating another token for the active deployment — should 409
            token_again_response = client.post(
                f"/v1/admin/deployments/{deployment_id}/enrollment-token",
                headers=admin_headers(),
            )
    assert token_again_response.status_code == 409


# ---------------------------------------------------------------------------
# ENRL-02: Exchange endpoint tests
# ---------------------------------------------------------------------------


def test_enrollment_exchange_success() -> None:
    """07-02-01: Valid token exchange returns 200 with deployment credential."""
    with configured_app() as app:
        with TestClient(app) as client:
            # Create a deployment slot
            create_resp = client.post(
                "/v1/admin/deployments",
                json={"display_name": "exchange-gw", "environment": "production"},
                headers=admin_headers(),
            )
            assert create_resp.status_code == 201
            deployment_id = create_resp.json()["id"]

            # Generate an enrollment token
            token_resp = client.post(
                f"/v1/admin/deployments/{deployment_id}/enrollment-token",
                headers=admin_headers(),
            )
            assert token_resp.status_code == 200
            raw_token = token_resp.json()["token"]

            # Exchange the token
            exchange_resp = client.post(
                "/v1/enrollment/exchange",
                json={
                    "enrollment_token": raw_token,
                    "nebula_version": "2.0.0",
                    "capability_flags": ["semantic_cache"],
                },
            )
            assert exchange_resp.status_code == 200
            exchange_data = exchange_resp.json()
            assert exchange_data["deployment_id"] == deployment_id
            assert exchange_data["deployment_credential"].startswith("nbdc_")
            assert exchange_data["display_name"] == "exchange-gw"
            assert exchange_data["environment"] == "production"

            # Verify deployment is now active
            get_resp = client.get(
                f"/v1/admin/deployments/{deployment_id}",
                headers=admin_headers(),
            )
            assert get_resp.status_code == 200
            deployment = get_resp.json()
            assert deployment["enrollment_state"] == "active"
            assert deployment["enrolled_at"] is not None


def test_enrollment_exchange_expired_token() -> None:
    """07-02-02: Expired token returns 401."""
    with configured_app() as app:
        with TestClient(app) as client:
            # Create a deployment slot
            create_resp = client.post(
                "/v1/admin/deployments",
                json={"display_name": "expired-token-gw", "environment": "staging"},
                headers=admin_headers(),
            )
            assert create_resp.status_code == 201
            deployment_id = create_resp.json()["id"]

            # Generate an enrollment token
            token_resp = client.post(
                f"/v1/admin/deployments/{deployment_id}/enrollment-token",
                headers=admin_headers(),
            )
            assert token_resp.status_code == 200
            raw_token = token_resp.json()["token"]

            # Manually expire the token in the DB
            import hashlib

            from sqlalchemy import create_engine, select
            from sqlalchemy.orm import sessionmaker

            from nebula.db.models import EnrollmentTokenModel

            db_url = app.state.container.settings.database_url
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            Session = sessionmaker(bind=engine)
            with Session() as session:
                token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                token_row = session.scalars(
                    select(EnrollmentTokenModel).where(
                        EnrollmentTokenModel.token_hash == token_hash
                    )
                ).first()
                assert token_row is not None
                token_row.expires_at = datetime.now(UTC) - timedelta(hours=2)
                session.commit()

            # Exchange should return 401
            exchange_resp = client.post(
                "/v1/enrollment/exchange",
                json={
                    "enrollment_token": raw_token,
                    "nebula_version": "2.0.0",
                    "capability_flags": [],
                },
            )
    assert exchange_resp.status_code == 401


def test_enrollment_exchange_consumed_token() -> None:
    """07-02-03: Already-consumed token returns 401."""
    with configured_app() as app:
        with TestClient(app) as client:
            # Create a deployment slot
            create_resp = client.post(
                "/v1/admin/deployments",
                json={"display_name": "consumed-token-gw", "environment": "development"},
                headers=admin_headers(),
            )
            assert create_resp.status_code == 201
            deployment_id = create_resp.json()["id"]

            # Generate an enrollment token
            token_resp = client.post(
                f"/v1/admin/deployments/{deployment_id}/enrollment-token",
                headers=admin_headers(),
            )
            assert token_resp.status_code == 200
            raw_token = token_resp.json()["token"]

            # First exchange — succeeds
            first_exchange = client.post(
                "/v1/enrollment/exchange",
                json={
                    "enrollment_token": raw_token,
                    "nebula_version": "2.0.0",
                    "capability_flags": [],
                },
            )
            assert first_exchange.status_code == 200

            # Second exchange with same token — should 401
            second_exchange = client.post(
                "/v1/enrollment/exchange",
                json={
                    "enrollment_token": raw_token,
                    "nebula_version": "2.0.0",
                    "capability_flags": [],
                },
            )
    assert second_exchange.status_code == 401
