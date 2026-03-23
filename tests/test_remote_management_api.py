"""Integration and contract tests for hosted remote management APIs."""

from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from fastapi.testclient import TestClient

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

