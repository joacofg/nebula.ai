"""Integration and contract tests for hosted remote management APIs."""

from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from nebula.db.models import DeploymentRemoteActionModel
from nebula.models.deployment import DeploymentRecord, RemoteActionRecord, RemoteActionSummary
from tests.support import admin_headers, configured_app


def _make_active_deployment(client: TestClient) -> str:
    create_resp = client.post(
        "/v1/admin/deployments",
        json={"display_name": "remote-gw", "environment": "production"},
        headers=admin_headers(),
    )
    assert create_resp.status_code == 201
    deployment_id = create_resp.json()["id"]

    token_resp = client.post(
        f"/v1/admin/deployments/{deployment_id}/enrollment-token",
        headers=admin_headers(),
    )
    assert token_resp.status_code == 200

    exchange_resp = client.post(
        "/v1/enrollment/exchange",
        json={
            "enrollment_token": token_resp.json()["token"],
            "nebula_version": "2.0.0",
            "capability_flags": ["remote_management"],
        },
    )
    assert exchange_resp.status_code == 200
    return deployment_id


def test_models_remote_action_record_serializes_queue_contract() -> None:
    requested_at = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
    expires_at = datetime(2026, 3, 22, 12, 15, tzinfo=UTC)
    record = RemoteActionRecord(
        id="action-1",
        deployment_id="dep-1",
        action_type="rotate_deployment_credential",
        status="queued",
        note="Rotate after access review",
        requested_at=requested_at.isoformat(),
        expires_at=expires_at.isoformat(),
        started_at=None,
        finished_at=None,
        failure_reason=None,
        failure_detail=None,
        result_credential_prefix=None,
    )

    assert record.model_dump() == {
        "id": "action-1",
        "deployment_id": "dep-1",
        "action_type": "rotate_deployment_credential",
        "status": "queued",
        "note": "Rotate after access review",
        "requested_at": requested_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "started_at": None,
        "finished_at": None,
        "failure_reason": None,
        "failure_detail": None,
        "result_credential_prefix": None,
    }


def test_models_deployment_record_supports_remote_action_summary() -> None:
    record = DeploymentRecord(
        id="dep-1",
        display_name="gw-1",
        environment="production",
        enrollment_state="active",
        nebula_version="2.0.0",
        capability_flags=["remote_management"],
        enrolled_at="2026-03-22T12:00:00+00:00",
        revoked_at=None,
        unlinked_at=None,
        created_at="2026-03-22T12:00:00+00:00",
        updated_at="2026-03-22T12:00:00+00:00",
        remote_action_summary=RemoteActionSummary(
            queued=1,
            applied=3,
            failed=2,
            last_action_at="2026-03-22T12:30:00+00:00",
        ),
    )

    assert record.model_dump()["remote_action_summary"] == {
        "queued": 1,
        "applied": 3,
        "failed": 2,
        "last_action_at": "2026-03-22T12:30:00+00:00",
    }


def test_schema_remote_actions_has_unique_live_action_guard() -> None:
    live_indexes = [
        index
        for index in DeploymentRemoteActionModel.__table__.indexes
        if index.name == "uq_remote_actions_live"
    ]

    assert len(live_indexes) == 1
    where_clause = live_indexes[0].dialect_options["postgresql"]["where"]
    assert isinstance(where_clause, sa.ClauseElement)
    compiled = str(where_clause.compile(compile_kwargs={"literal_binds": True}))
    assert "queued" in compiled
    assert "in_progress" in compiled


def test_queue_rotate_credential_returns_201_for_active_deployment() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id = _make_active_deployment(client)

            response = client.post(
                f"/v1/admin/deployments/{deployment_id}/remote-actions/rotate-credential",
                json={"note": "Rotate after access review"},
                headers=admin_headers(),
            )

    assert response.status_code == 201
    data = response.json()
    assert data["deployment_id"] == deployment_id
    assert data["action_type"] == "rotate_deployment_credential"
    assert data["status"] == "queued"
    assert data["note"] == "Rotate after access review"
    assert data["requested_at"] is not None
    assert data["expires_at"] is not None


def test_queue_rotate_credential_rejects_non_active_deployments() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            pending_response = client.post(
                "/v1/admin/deployments/missing/remote-actions/rotate-credential",
                json={"note": "Rotate"},
                headers=admin_headers(),
            )
            assert pending_response.status_code == 404

            pending_create = client.post(
                "/v1/admin/deployments",
                json={"display_name": "pending-gw", "environment": "production"},
                headers=admin_headers(),
            )
            assert pending_create.status_code == 201
            pending_id = pending_create.json()["id"]

            pending_queue = client.post(
                f"/v1/admin/deployments/{pending_id}/remote-actions/rotate-credential",
                json={"note": "Rotate"},
                headers=admin_headers(),
            )
            assert pending_queue.status_code == 409
            assert pending_queue.json()["detail"] == "Deployment is not in an active linked state."

            revoked_id = _make_active_deployment(client)
            revoke_resp = client.post(
                f"/v1/admin/deployments/{revoked_id}/revoke",
                headers=admin_headers(),
            )
            assert revoke_resp.status_code == 200
            revoked_queue = client.post(
                f"/v1/admin/deployments/{revoked_id}/remote-actions/rotate-credential",
                json={"note": "Rotate"},
                headers=admin_headers(),
            )
            assert revoked_queue.status_code == 409

            unlinked_id = _make_active_deployment(client)
            unlink_resp = client.post(
                f"/v1/admin/deployments/{unlinked_id}/unlink",
                headers=admin_headers(),
            )
            assert unlink_resp.status_code == 200
            unlinked_queue = client.post(
                f"/v1/admin/deployments/{unlinked_id}/remote-actions/rotate-credential",
                json={"note": "Rotate"},
                headers=admin_headers(),
            )
            assert unlinked_queue.status_code == 409

            db_url = app.state.container.settings.database_url
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            Session = sessionmaker(bind=engine)
            with Session() as session:
                rows = session.scalars(select(DeploymentRemoteActionModel)).all()

    assert rows == []


def test_queue_rotate_credential_returns_existing_live_action() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id = _make_active_deployment(client)

            first = client.post(
                f"/v1/admin/deployments/{deployment_id}/remote-actions/rotate-credential",
                json={"note": "Rotate now"},
                headers=admin_headers(),
            )
            assert first.status_code == 201

            second = client.post(
                f"/v1/admin/deployments/{deployment_id}/remote-actions/rotate-credential",
                json={"note": "Rotate now"},
                headers=admin_headers(),
            )

    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def test_list_remote_actions_returns_deployment_history_newest_first() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id = _make_active_deployment(client)

            first = client.post(
                f"/v1/admin/deployments/{deployment_id}/remote-actions/rotate-credential",
                json={"note": "First rotation"},
                headers=admin_headers(),
            )
            assert first.status_code == 201

            db_url = app.state.container.settings.database_url
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            Session = sessionmaker(bind=engine)
            with Session() as session:
                first_row = session.get(DeploymentRemoteActionModel, first.json()["id"])
                assert first_row is not None
                first_row.status = "applied"
                first_row.finished_at = datetime(2026, 3, 22, 13, 5, tzinfo=UTC)
                first_row.updated_at = datetime(2026, 3, 22, 13, 5, tzinfo=UTC)
                session.commit()

            second = client.post(
                f"/v1/admin/deployments/{deployment_id}/remote-actions/rotate-credential",
                json={"note": "Second rotation"},
                headers=admin_headers(),
            )
            assert second.status_code == 201

            response = client.get(
                f"/v1/admin/deployments/{deployment_id}/remote-actions",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [second.json()["id"], first.json()["id"]]
