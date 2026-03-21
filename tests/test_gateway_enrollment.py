"""Integration tests for gateway-side enrollment at startup (ENRL-02)."""

from __future__ import annotations


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from tests.support import admin_headers, configured_app


def test_startup_enrollment_exchange() -> None:
    """07-02-04: Gateway with NEBULA_ENROLLMENT_TOKEN set performs exchange and stores identity.

    Strategy:
    1. Create a deployment slot + token via admin API.
    2. Call GatewayEnrollmentService.attempt_enrollment directly, injecting an
       httpx.ASGITransport so the outbound call routes through the same ASGI app.
    3. Verify local_hosted_identity table has a row after enrollment.
    """
    import asyncio

    import httpx

    from nebula.db.models import LocalHostedIdentityModel
    from nebula.db.session import create_session_factory
    from nebula.services.gateway_enrollment_service import GatewayEnrollmentService

    with configured_app(NEBULA_HOSTED_PLANE_URL="http://testserver") as app:
        with TestClient(app) as client:
            # Create deployment slot and generate enrollment token
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

            # Inject ASGI transport so outbound httpx routes through the same app
            transport = httpx.ASGITransport(app=app)
            settings = app.state.container.settings
            session_factory = create_session_factory(settings)

            svc = GatewayEnrollmentService(
                settings=settings,
                session_factory=session_factory,
                http_transport=transport,
            )

            result = asyncio.get_event_loop().run_until_complete(
                svc.attempt_enrollment(raw_token)
            )
            assert result is True

            # Verify local_hosted_identity table has a row
            db_url = settings.database_url
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            Session = sessionmaker(bind=engine)
            with Session() as session:
                identity_rows = session.scalars(
                    select(LocalHostedIdentityModel).where(
                        LocalHostedIdentityModel.unlinked_at.is_(None)
                    )
                ).all()
                assert len(identity_rows) == 1
                identity = identity_rows[0]
                assert identity.deployment_id == deployment_id
                assert identity.display_name == "startup-gw"


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


def test_startup_already_enrolled_skips_exchange(caplog: pytest.LogCaptureFixture) -> None:
    """Already stored local identity causes gateway to skip enrollment exchange."""
    import asyncio
    import logging
    from datetime import UTC, datetime

    import httpx

    from nebula.db.models import LocalHostedIdentityModel
    from nebula.db.session import create_session_factory
    from nebula.services.gateway_enrollment_service import GatewayEnrollmentService

    with configured_app(NEBULA_HOSTED_PLANE_URL="http://testserver") as app:
        with TestClient(app):
            settings = app.state.container.settings
            db_url = settings.database_url

            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            Session = sessionmaker(bind=engine)

            # Pre-populate the local_hosted_identity table (simulating prior enrollment)
            with Session() as session:
                session.add(
                    LocalHostedIdentityModel(
                        deployment_id="existing-deployment-id",
                        display_name="already-enrolled-gw",
                        environment="production",
                        credential_hash="abc" * 20 + "abcd",
                        credential_prefix="nbdc_prefixXX",
                        enrolled_at=datetime.now(UTC),
                        unlinked_at=None,
                    )
                )
                session.commit()

            # Now call attempt_enrollment — it should skip because identity exists
            transport = httpx.ASGITransport(app=app)
            session_factory = create_session_factory(settings)
            svc = GatewayEnrollmentService(
                settings=settings,
                session_factory=session_factory,
                http_transport=transport,
            )

            with caplog.at_level(
                logging.INFO, logger="nebula.services.gateway_enrollment_service"
            ):
                result = asyncio.get_event_loop().run_until_complete(
                    svc.attempt_enrollment("nbet_some_token")
                )

            assert result is True
            # Should log "Already enrolled" message
            assert any("Already enrolled" in record.message for record in caplog.records)
