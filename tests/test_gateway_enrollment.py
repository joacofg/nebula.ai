"""Integration tests for gateway-side enrollment at startup (ENRL-02)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from tests.support import admin_headers, configured_app


def test_startup_enrollment_exchange() -> None:
    """07-02-04: Gateway with NEBULA_ENROLLMENT_TOKEN set performs exchange and stores identity."""
    with configured_app() as app:
        with TestClient(app) as client:
            # Create a deployment slot + token via admin API
            create_resp = client.post(
                "/v1/admin/deployments",
                json={"display_name": "startup-gw", "environment": "production"},
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

        # Now restart app with enrollment token set
        # The app itself serves /v1/enrollment/exchange, so hosted_plane_url is the same app.
        # We use patch to make GatewayEnrollmentService call the local exchange endpoint.

    db_url = None
    import os
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from uuid import uuid4

    # Create a shared DB for both the token setup and the enrollment startup
    temp_dir = TemporaryDirectory()
    database_path = Path(temp_dir.name) / "nebula.db"

    with configured_app(
        NEBULA_DATABASE_URL=f"sqlite+pysqlite:///{database_path}",
        NEBULA_DATA_STORE_PATH=str(database_path),
        NEBULA_SEMANTIC_CACHE_COLLECTION=f"nebula-test-cache-{uuid4().hex}",
    ) as shared_app:
        with TestClient(shared_app) as setup_client:
            # Create deployment slot and token using the shared DB app
            create_resp2 = setup_client.post(
                "/v1/admin/deployments",
                json={"display_name": "startup-gw-2", "environment": "production"},
                headers=admin_headers(),
            )
            assert create_resp2.status_code == 201
            deployment_id2 = create_resp2.json()["id"]

            token_resp2 = setup_client.post(
                f"/v1/admin/deployments/{deployment_id2}/enrollment-token",
                headers=admin_headers(),
            )
            assert token_resp2.status_code == 200
            raw_token2 = token_resp2.json()["token"]

    # Now start a new app with the enrollment token set and the same DB
    # We mock the outbound httpx call to hit the local exchange endpoint
    with configured_app(
        NEBULA_DATABASE_URL=f"sqlite+pysqlite:///{database_path}",
        NEBULA_DATA_STORE_PATH=str(database_path),
        NEBULA_SEMANTIC_CACHE_COLLECTION=f"nebula-test-cache-{uuid4().hex}",
        NEBULA_ENROLLMENT_TOKEN=raw_token2,
        NEBULA_HOSTED_PLANE_URL="http://testserver",
    ) as enrolled_app:
        from nebula.db.models import LocalHostedIdentityModel

        db_url2 = enrolled_app.state.container.settings.database_url
        engine = create_engine(db_url2, connect_args={"check_same_thread": False})
        Session = sessionmaker(bind=engine)
        with Session() as session:
            identity_rows = session.scalars(
                select(LocalHostedIdentityModel).where(
                    LocalHostedIdentityModel.unlinked_at.is_(None)
                )
            ).all()
            assert len(identity_rows) == 1
            identity = identity_rows[0]
            assert identity.deployment_id == deployment_id2
            assert identity.display_name == "startup-gw-2"

    temp_dir.cleanup()


def test_startup_no_token_skips_enrollment() -> None:
    """07-02-05: Gateway startup without NEBULA_ENROLLMENT_TOKEN skips enrollment silently."""
    with configured_app() as app:
        with TestClient(app) as client:
            # App starts fine — health check passes
            resp = client.get("/health")
            assert resp.status_code == 200

        # Verify local_hosted_identity table is empty
        from nebula.db.models import LocalHostedIdentityModel

        db_url = app.state.container.settings.database_url
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Session = sessionmaker(bind=engine)
        with Session() as session:
            count = session.scalars(select(LocalHostedIdentityModel)).all()
            assert len(count) == 0


def test_startup_enrollment_failure_nonfatal() -> None:
    """07-02-06: Unreachable hosted plane logs error and gateway starts normally."""
    with configured_app(
        NEBULA_ENROLLMENT_TOKEN="nbet_invalid_token_xyz",
        NEBULA_HOSTED_PLANE_URL="http://localhost:1",  # unreachable
    ) as app:
        with TestClient(app) as client:
            # App should start normally despite enrollment failure
            resp = client.get("/health")
            assert resp.status_code == 200

        # Local identity table should be empty (enrollment failed)
        from nebula.db.models import LocalHostedIdentityModel

        db_url = app.state.container.settings.database_url
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Session = sessionmaker(bind=engine)
        with Session() as session:
            count = session.scalars(select(LocalHostedIdentityModel)).all()
            assert len(count) == 0
