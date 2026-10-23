from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from qdrant_client import AsyncQdrantClient

from nebula.db.models import UsageLedgerModel
from nebula.services.semantic_cache_service import TIER_RANK, SemanticCacheService
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


ANY_VECTOR = [1.0, 0.0, 0.0]


async def _cache_with_an_answer_per_tenant(app, tenants: list[str]) -> SemanticCacheService:
    """The gateway's own cache, over an in-memory Qdrant, with one answer per tenant."""
    cache = app.state.container.cache_service
    await cache.client.close()
    cache.client = AsyncQdrantClient(location=":memory:")
    await cache.initialize()
    assert cache.enabled
    for tenant_id in tenants:
        await cache.store(
            f"{tenant_id} answer",
            tenant_id=tenant_id,
            vector=ANY_VECTOR,
            context_hash="ctx",
            tier_rank=TIER_RANK["local"],
            model="local-model",
        )
    return cache


async def _cached_answer(cache: SemanticCacheService, tenant_id: str) -> str | None:
    hit = await cache.lookup(
        "hola",
        tenant_id=tenant_id,
        similarity_threshold=0.9,
        max_entry_age_hours=720,
        context_hash="ctx",
        min_tier_rank=0,
        model=None,
        vector=ANY_VECTOR,
    )
    return hit.response if hit else None


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:Payload indexes have no effect")
async def test_cleanup_deletes_cache_entries_older_than_their_tenants_max_age() -> None:
    with configured_app(NEBULA_EMBEDDING_DIMENSIONS="3") as app:
        async with app.router.lifespan_context(app):
            store = app.state.container.governance_store
            store.create_tenant(
                tenant_id="short-lived",
                name="Short-lived",
                description=None,
                metadata={},
                active=True,
                policy=store.default_policy().model_copy(
                    update={"semantic_cache_max_entry_age_hours": 1}
                ),
            )
            cache = await _cache_with_an_answer_per_tenant(app, ["default", "short-lived"])

            # Two hours on, the 1 h tenant's answer has expired; the default (168 h) one has not.
            result = await app.state.container.retention_lifecycle_service.run_cleanup_once(
                now=datetime.now(UTC) + timedelta(hours=2)
            )
            answers = {
                tenant_id: await _cached_answer(cache, tenant_id)
                for tenant_id in ("default", "short-lived")
            }

    assert result["status"] == "ok"
    assert answers == {"default": "default answer", "short-lived": None}


class _QdrantThatCannotDelete:
    def __init__(self, cache: SemanticCacheService) -> None:
        self._client = cache.client

    def __getattr__(self, name: str):
        return getattr(self._client, name)

    async def delete(self, **kwargs) -> None:
        raise ConnectionError("Qdrant went away")


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:Payload indexes have no effect")
async def test_a_failed_cache_sweep_is_logged_and_leaves_the_ledger_cleanup_ok(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with configured_app(NEBULA_EMBEDDING_DIMENSIONS="3") as app:
        async with app.router.lifespan_context(app):
            cache = await _cache_with_an_answer_per_tenant(app, ["default"])
            cache.client = _QdrantThatCannotDelete(cache)
            now = datetime.now(UTC)
            _insert_usage_row(
                app,
                request_id="expired-row",
                timestamp=now - timedelta(days=2),
                evidence_expires_at=now - timedelta(minutes=5),
            )

            retention = app.state.container.retention_lifecycle_service
            result = await retention.run_cleanup_once(now=now + timedelta(days=30))

    assert result["status"] == "ok"
    assert result["deleted_count"] == 1
    assert "Qdrant went away" in caplog.text


class _QdrantThatCannotDeleteForTenant:
    """Fails the delete aimed at one tenant and lets every other tenant's through."""

    def __init__(self, cache: SemanticCacheService, failing_tenant_id: str) -> None:
        self._client = cache.client
        self._failing_tenant_id = failing_tenant_id

    def __getattr__(self, name: str):
        return getattr(self._client, name)

    async def delete(self, **kwargs) -> None:
        conditions = kwargs["points_selector"].filter.must
        tenant_id = next(c.match.value for c in conditions if c.key == "tenant_id")
        if tenant_id == self._failing_tenant_id:
            raise ConnectionError("Qdrant went away")
        await self._client.delete(**kwargs)


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:Payload indexes have no effect")
async def test_retention_sweep_continues_after_one_tenant_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with configured_app(NEBULA_EMBEDDING_DIMENSIONS="3") as app:
        async with app.router.lifespan_context(app):
            store = app.state.container.governance_store
            store.create_tenant(
                tenant_id="short-lived",
                name="Short-lived",
                description=None,
                metadata={},
                active=True,
                policy=store.default_policy().model_copy(
                    update={"semantic_cache_max_entry_age_hours": 1}
                ),
            )
            cache = await _cache_with_an_answer_per_tenant(app, ["default", "short-lived"])
            real_client = cache.client
            # Tenants sweep in id order, so "default" fails first and "short-lived" comes after.
            cache.client = _QdrantThatCannotDeleteForTenant(cache, "default")
            with caplog.at_level(logging.ERROR):
                result = await app.state.container.retention_lifecycle_service.run_cleanup_once(
                    now=datetime.now(UTC) + timedelta(hours=2)
                )
            cache.client = real_client
            answer = await _cached_answer(cache, "short-lived")

    assert result["status"] == "ok"
    assert answer is None
    assert [r.tenant_id for r in caplog.records if hasattr(r, "tenant_id")] == ["default"]


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
    assert dependency["dependency_class"] == "metadata_only"
    assert dependency["lifecycle_state"] == "ready"
    assert dependency["serving_effect"] == "unaffected"
    assert dependency["reason_code"] == "retention_idle"
    assert dependency["enabled"] is True
    assert dependency["last_status"] == "idle"
