from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from nebula.db.models import UsageLedgerModel
from tests.support import configured_app


def _insert_usage_row(
    app,
    *,
    request_id: str,
    timestamp: datetime,
    evidence_expires_at: datetime | None,
) -> None:
    with app.state.container.governance_store.session_factory() as session:
        session.add(
            UsageLedgerModel(
                request_id=request_id,
                tenant_id="default",
                requested_model="nebula-auto",
                final_route_target="local",
                final_provider="ollama",
                fallback_used=False,
                cache_hit=False,
                response_model="llama3.2:3b",
                prompt_tokens=12,
                completion_tokens=8,
                total_tokens=20,
                estimated_cost=0.0,
                latency_ms=12.5,
                timestamp=timestamp,
                terminal_status="completed",
                route_reason="simple_prompt",
                policy_outcome="allowed",
                route_signals={"route_mode": "auto"},
                message_type="chat",
                evidence_retention_window="24h",
                evidence_expires_at=evidence_expires_at,
                metadata_minimization_level="standard",
                metadata_fields_suppressed_json=[],
                governance_source="tenant_policy",
            )
        )
        session.commit()


@pytest.mark.asyncio
async def test_run_cleanup_once_deletes_only_rows_with_expired_evidence_markers() -> None:
    with configured_app() as app:
        async with app.router.lifespan_context(app):
            store = app.state.container.governance_store
            now = datetime.now(UTC)
            expired_at = now - timedelta(minutes=5)
            future_at = now + timedelta(days=2)

            _insert_usage_row(
                app,
                request_id="expired-row",
                timestamp=now - timedelta(days=2),
                evidence_expires_at=expired_at,
            )
            _insert_usage_row(
                app,
                request_id="future-row",
                timestamp=now,
                evidence_expires_at=future_at,
            )
            _insert_usage_row(
                app,
                request_id="none-row",
                timestamp=now,
                evidence_expires_at=None,
            )

            result = await app.state.container.retention_lifecycle_service.run_cleanup_once(now=now)
            remaining_ids = {record.request_id for record in store.list_usage_records(limit=20)}
            health = await app.state.container.retention_lifecycle_service.health_status()

    assert result["status"] == "ok"
    assert result["eligible_count"] == 1
    assert result["deleted_count"] == 1
    assert result["cutoff"] == now
    assert remaining_ids == {"future-row", "none-row"}
    assert health["status"] == "ready"
    assert health["last_status"] == "ok"
    assert health["last_deleted_count"] == 1
    assert health["last_eligible_count"] == 1
    assert health["last_error"] is None
    assert health["last_run_at"] is not None
    assert health["last_attempted_run_at"] is not None


@pytest.mark.asyncio
async def test_retention_lifecycle_health_reports_failure_without_breaking_calls() -> None:
    with configured_app() as app:
        async with app.router.lifespan_context(app):
            service = app.state.container.retention_lifecycle_service
            original = app.state.container.governance_store.delete_expired_usage_records

            def boom(*, now=None):
                raise RuntimeError("cleanup query timed out")

            app.state.container.governance_store.delete_expired_usage_records = boom
            try:
                with pytest.raises(RuntimeError, match="cleanup query timed out"):
                    await service.run_cleanup_once()
                health = await service.health_status()
            finally:
                app.state.container.governance_store.delete_expired_usage_records = original

    assert health["status"] == "degraded"
    assert health["last_status"] == "failed"
    assert health["last_error"] == "cleanup query timed out"
    assert health["last_attempted_run_at"] is not None
    assert health["last_run_at"] is None


@pytest.mark.asyncio
async def test_retention_lifecycle_disabled_does_not_start_background_task() -> None:
    with configured_app(NEBULA_RETENTION_CLEANUP_ENABLED="false") as app:
        async with app.router.lifespan_context(app):
            service = app.state.container.retention_lifecycle_service
            health = await service.health_status()

            assert service._task is None
            assert health["status"] == "ready"
            assert health["enabled"] is False
            assert health["last_status"] == "idle"
            assert health["detail"] == "Retention lifecycle is disabled by configuration."


@pytest.mark.asyncio
async def test_health_dependencies_expose_retention_lifecycle_runtime_state() -> None:
    with configured_app() as app:
        async with app.router.lifespan_context(app):
            now = datetime.now(UTC)
            _insert_usage_row(
                app,
                request_id="health-expired",
                timestamp=now - timedelta(days=3),
                evidence_expires_at=now - timedelta(minutes=1),
            )
            await app.state.container.retention_lifecycle_service.run_cleanup_once(now=now)
            dependency = (await app.state.container.runtime_health_service.readiness())["dependencies"][
                "retention_lifecycle"
            ]

    assert dependency["status"] == "ready"
    assert dependency["enabled"] is True
    assert dependency["last_status"] == "ok"
    assert dependency["last_deleted_count"] == 1
    assert dependency["last_eligible_count"] == 1
    assert dependency["last_error"] is None
    assert dependency["last_run_at"] is not None


def test_health_dependencies_endpoint_exposes_retention_lifecycle_dependency() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/health/dependencies")

    assert response.status_code == 200
    dependency = response.json()["dependencies"]["retention_lifecycle"]
    assert dependency["status"] == "ready"
    assert dependency["required"] is False
    assert dependency["enabled"] is True
    assert dependency["last_status"] == "idle"
