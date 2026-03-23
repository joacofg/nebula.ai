from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nebula.db.models import DeploymentRemoteActionModel
from tests.support import admin_headers, configured_app


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _session_factory(app) -> sessionmaker:
    db_url = app.state.container.settings.database_url
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine)


def _make_active_deployment(client: TestClient) -> tuple[str, str]:
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
            "capability_flags": ["remote_credential_rotation"],
        },
    )
    assert exchange_resp.status_code == 200
    return deployment_id, exchange_resp.json()["deployment_credential"]


def test_expired_queued_and_in_progress_actions_fail_with_expired_reason() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, credential = _make_active_deployment(client)
            queued_deployment_id, _ = _make_active_deployment(client)
            service = app.state.container.enrollment_service
            base_now = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
            service._now = lambda: base_now  # type: ignore[method-assign]

            in_progress_action = service.queue_rotate_deployment_credential(
                deployment_id, "Expire before polling"
            )
            claimed_action = service.claim_next_remote_action(credential)
            assert claimed_action is not None
            assert claimed_action.id == in_progress_action.id

            queued_action = service.queue_rotate_deployment_credential(
                queued_deployment_id, "Expire while queued"
            )

            expired_at = base_now + timedelta(minutes=16)
            service._now = lambda: expired_at  # type: ignore[method-assign]

            deployments = service.list_deployments()
            assert {row.id for row in deployments} >= {deployment_id, queued_deployment_id}
            in_progress_history = service.list_remote_actions(deployment_id, limit=10)
            queued_history = service.list_remote_actions(queued_deployment_id, limit=10)

    assert in_progress_history[0].id == in_progress_action.id
    assert in_progress_history[0].status == "failed"
    assert in_progress_history[0].failure_reason == "expired"
    assert in_progress_history[0].failure_detail == "Remote action expired before completion."
    assert _parse_iso(in_progress_history[0].finished_at or "") == expired_at
    assert queued_history[0].id == queued_action.id
    assert queued_history[0].status == "failed"
    assert queued_history[0].failure_reason == "expired"
    assert queued_history[0].failure_detail == "Remote action expired before completion."
    assert _parse_iso(queued_history[0].finished_at or "") == expired_at


def test_list_and_get_deployment_project_remote_action_summary_counts() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, _ = _make_active_deployment(client)
            service = app.state.container.enrollment_service
            summary_now = datetime(2026, 3, 22, 13, 0, tzinfo=UTC)
            service._now = lambda: summary_now  # type: ignore[method-assign]
            queued = service.queue_rotate_deployment_credential(deployment_id, "Queued rotation")

            Session = _session_factory(app)
            with Session() as session:
                queued_row = session.get(DeploymentRemoteActionModel, queued.id)
                assert queued_row is not None
                applied_row = DeploymentRemoteActionModel(
                    id="applied-action",
                    deployment_id=deployment_id,
                    action_type="rotate_deployment_credential",
                    status="applied",
                    note="Applied rotation",
                    requested_at=summary_now - timedelta(minutes=10),
                    expires_at=summary_now - timedelta(minutes=5),
                    finished_at=summary_now - timedelta(minutes=4),
                    created_at=summary_now - timedelta(minutes=10),
                    updated_at=summary_now - timedelta(minutes=4),
                )
                failed_row = DeploymentRemoteActionModel(
                    id="failed-action",
                    deployment_id=deployment_id,
                    action_type="rotate_deployment_credential",
                    status="failed",
                    note="Failed rotation",
                    requested_at=summary_now - timedelta(minutes=6),
                    expires_at=summary_now - timedelta(minutes=1),
                    finished_at=summary_now - timedelta(minutes=1),
                    failure_reason="apply_error",
                    failure_detail="failed on host",
                    created_at=summary_now - timedelta(minutes=6),
                    updated_at=summary_now - timedelta(minutes=1),
                )
                session.add_all([applied_row, failed_row])
                session.commit()

            listed = service.list_deployments()
            fetched = service.get_deployment(deployment_id)

    listed_record = next(row for row in listed if row.id == deployment_id)
    assert listed_record.remote_action_summary is not None
    assert listed_record.remote_action_summary.model_dump() == {
        "queued": 1,
        "applied": 1,
        "failed": 1,
        "last_action_at": queued.requested_at,
    }
    assert fetched is not None
    assert fetched.remote_action_summary is not None
    assert fetched.remote_action_summary.model_dump() == listed_record.remote_action_summary.model_dump()


def test_duplicate_queue_returns_existing_live_action_until_expiry_then_creates_new_one() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            deployment_id, _ = _make_active_deployment(client)
            service = app.state.container.enrollment_service
            initial_now = datetime(2026, 3, 22, 14, 0, tzinfo=UTC)
            service._now = lambda: initial_now  # type: ignore[method-assign]

            first = service.queue_rotate_deployment_credential(deployment_id, "Rotate now")
            duplicate = service.queue_rotate_deployment_credential(deployment_id, "Rotate now")

            expired_now = initial_now + timedelta(minutes=16)
            service._now = lambda: expired_now  # type: ignore[method-assign]
            replacement = service.queue_rotate_deployment_credential(deployment_id, "Rotate after expiry")
            history = service.list_remote_actions(deployment_id, limit=10)

    assert duplicate.id == first.id
    assert replacement.id != first.id
    assert history[0].id == replacement.id
    expired = next(action for action in history if action.id == first.id)
    assert expired.status == "failed"
    assert expired.failure_reason == "expired"
    assert expired.failure_detail == "Remote action expired before completion."
