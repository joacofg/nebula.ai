from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI
from nebula.models.resilience import DependencyHealthReason, build_dependency_health
from nebula.providers.base import CompletionResult
from nebula.services.premium_provider_health_service import PremiumProviderHealthService
from tests.support import (
    FakeCacheService,
    StubProvider,
    auth_headers,
    configured_app,
    usage,
)


@asynccontextmanager
async def configured_outage_client():
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        transport = httpx.ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            _install_serving_stubs(app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=True,
            ) as client:
                yield app, client


def _install_serving_stubs(app: FastAPI) -> None:
    container = app.state.container
    container.local_provider = StubProvider(
        "ollama",
        completion_result=CompletionResult(
            content="local outage-safe response",
            model=container.settings.local_model,
            provider="ollama",
            usage=usage(),
        ),
    )
    container.provider_registry.local_provider = container.local_provider
    container.cache_service = FakeCacheService()
    container.chat_service.cache_service = container.cache_service


def _semantic_cache_outage_payload(detail: str = "Qdrant unavailable: injected semantic cache outage") -> dict[str, object]:
    return build_dependency_health(
        dependency_class="serving_optional",
        lifecycle_state="degraded",
        serving_effect="continuity_limited",
        reason_code=DependencyHealthReason.SEMANTIC_CACHE_UNAVAILABLE,
        detail=detail,
        required=False,
        extra={"enabled": True},
    )


class StatefulSemanticCacheService(FakeCacheService):
    def __init__(self) -> None:
        super().__init__()

    def set_outage(
        self,
        detail: str = "Qdrant unavailable: injected semantic cache outage",
    ) -> None:
        self.health_status_payload = _semantic_cache_outage_payload(detail)

    def set_recovering(
        self,
        *,
        detail: str = "Qdrant recovered and warming semantic cache availability.",
        last_failure_at: datetime | None,
        last_recovery_at: datetime | None,
    ) -> None:
        self.health_status_payload = build_dependency_health(
            dependency_class="serving_optional",
            lifecycle_state="recovering",
            serving_effect="continuity_limited",
            reason_code="semantic_cache_ready",
            detail=detail,
            required=False,
            recovering=True,
            last_failure_at=last_failure_at,
            last_recovery_at=last_recovery_at,
            extra={"enabled": True},
        )

    def set_ready(
        self,
        *,
        detail: str = "Semantic cache collection is reachable.",
        last_failure_at: datetime | None = None,
        last_recovery_at: datetime | None = None,
    ) -> None:
        self.health_status_payload = build_dependency_health(
            dependency_class="serving_optional",
            lifecycle_state="ready",
            serving_effect="continuity_limited",
            reason_code="semantic_cache_ready",
            detail=detail,
            required=False,
            last_failure_at=last_failure_at,
            last_recovery_at=last_recovery_at,
            extra={"enabled": True},
        )



class FailingPremiumProviderHealthService(PremiumProviderHealthService):
    async def health_status(self) -> dict[str, object]:
        return build_dependency_health(
            dependency_class="serving_optional",
            lifecycle_state="degraded",
            serving_effect="continuity_limited",
            reason_code=DependencyHealthReason.PREMIUM_PROVIDER_UNAVAILABLE,
            detail="Premium provider unavailable: injected outage.",
            required=False,
        )


class ReachableLocalOllamaHealth:
    """Pins local_ollama to ready.

    /health/ready reports "degraded" when ANY dependency is degraded
    (runtime_health_service.py:66). A test that asserts the overall status
    flips to "ready" therefore has to hold every other dependency steady, or
    it silently measures the host instead of the code: with a live Ollama on
    :11434 it passes, and on a machine without one (CI) it fails with
    `assert 'degraded' == 'ready'`.
    """

    async def health_status(self) -> dict[str, object]:
        return build_dependency_health(
            dependency_class="serving_optional",
            lifecycle_state="ready",
            serving_effect="continuity_limited",
            reason_code=DependencyHealthReason.LOCAL_OLLAMA_READY,
            detail="Local Ollama endpoint is reachable.",
            required=False,
        )


class StatefulGovernanceStore:
    def __init__(self, delegate, detail: str = "Governance store query failed: injected outage") -> None:
        self.delegate = delegate
        self.detail = detail
        self.mode = "outage"
        self.last_failure_at: datetime | None = None
        self.last_recovery_at: datetime | None = None

    def set_outage(
        self,
        detail: str = "Governance store query failed: injected outage",
        *,
        last_failure_at: datetime | None = None,
    ) -> None:
        self.mode = "outage"
        self.detail = detail
        self.last_failure_at = last_failure_at
        self.last_recovery_at = None

    def set_recovering(
        self,
        *,
        detail: str = "Governance store recovered and is stabilizing.",
        last_failure_at: datetime | None,
        last_recovery_at: datetime | None,
    ) -> None:
        self.mode = "recovering"
        self.detail = detail
        self.last_failure_at = last_failure_at
        self.last_recovery_at = last_recovery_at

    def set_ready(
        self,
        *,
        detail: str = "Governance store is reachable.",
        last_failure_at: datetime | None = None,
        last_recovery_at: datetime | None = None,
    ) -> None:
        self.mode = "ready"
        self.detail = detail
        self.last_failure_at = last_failure_at
        self.last_recovery_at = last_recovery_at

    def find_api_key(self, raw_key: str):
        if self.mode == "outage":
            raise RuntimeError("injected governance auth outage")
        return self.delegate.find_api_key(raw_key)

    def get_tenant(self, tenant_id: str):
        return self.delegate.get_tenant(tenant_id)

    def get_policy(self, tenant_id: str):
        return self.delegate.get_policy(tenant_id)

    def health_status(self) -> dict[str, object]:
        if self.mode == "outage":
            return build_dependency_health(
                dependency_class="serving_critical",
                lifecycle_state="not_ready",
                serving_effect="fail_closed",
                reason_code="governance_query_failed",
                detail=self.detail,
                required=True,
                last_failure_at=self.last_failure_at,
                last_recovery_at=self.last_recovery_at,
            )
        if self.mode == "recovering":
            return build_dependency_health(
                dependency_class="serving_critical",
                lifecycle_state="recovering",
                serving_effect="fail_closed",
                reason_code="governance_ready",
                detail=self.detail,
                required=True,
                recovering=True,
                last_failure_at=self.last_failure_at,
                last_recovery_at=self.last_recovery_at,
            )
        return build_dependency_health(
            dependency_class="serving_critical",
            lifecycle_state="ready",
            serving_effect="fail_closed",
            reason_code="governance_ready",
            detail=self.detail,
            required=True,
            last_failure_at=self.last_failure_at,
            last_recovery_at=self.last_recovery_at,
        )


@pytest.mark.asyncio
async def test_semantic_cache_outage_keeps_chat_completion_serving_and_health_degraded() -> None:
    async with configured_outage_client() as (app, client):
        failing_cache = StatefulSemanticCacheService()
        failing_cache.set_outage()
        app.state.container.cache_service = failing_cache
        app.state.container.chat_service.cache_service = failing_cache
        app.state.container.runtime_health_service.semantic_cache = failing_cache

        response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Semantic cache outage should degrade without blocking local serving",
                    }
                ],
            },
        )
        readiness = await client.get("/health/ready")
        dependencies = await client.get("/health/dependencies")

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "local outage-safe response"
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Cache-Hit"] == "false"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"

    readiness_payload = readiness.json()
    dependency_payload = dependencies.json()

    assert readiness.status_code == 200
    assert readiness_payload["status"] == "degraded"
    semantic_cache_ready = readiness_payload["dependencies"]["semantic_cache"]
    assert semantic_cache_ready["enabled"] is True
    assert semantic_cache_ready == {
        "status": "degraded",
        "required": False,
        "detail": "Qdrant unavailable: injected semantic cache outage",
        "dependency_class": "serving_optional",
        "lifecycle_state": "degraded",
        "serving_effect": "continuity_limited",
        "reason_code": "semantic_cache_unavailable",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
        "enabled": True,
    }
    assert dependencies.status_code == 200
    assert dependency_payload["status"] == "degraded"
    semantic_cache_dependency = dependency_payload["dependencies"]["semantic_cache"]
    assert semantic_cache_dependency["enabled"] is True
    assert semantic_cache_dependency == {
        "status": "degraded",
        "required": False,
        "detail": "Qdrant unavailable: injected semantic cache outage",
        "dependency_class": "serving_optional",
        "lifecycle_state": "degraded",
        "serving_effect": "continuity_limited",
        "reason_code": "semantic_cache_unavailable",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
        "enabled": True,
    }



@pytest.mark.asyncio
async def test_premium_provider_outage_keeps_local_serving_and_reports_degraded_truth() -> None:
    async with configured_outage_client() as (app, client):
        app.state.container.runtime_health_service.premium_provider_health = (
            FailingPremiumProviderHealthService(app.state.container.settings)
        )

        response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Premium provider outage should not block unrelated healthy local serving",
                    }
                ],
            },
        )
        readiness = await client.get("/health/ready")
        dependencies = await client.get("/health/dependencies")

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "local outage-safe response"
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"

    assert readiness.status_code == 200
    assert readiness.json()["status"] == "degraded"
    assert readiness.json()["dependencies"]["premium_provider"] == {
        "status": "degraded",
        "required": False,
        "detail": "Premium provider unavailable: injected outage.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "degraded",
        "serving_effect": "continuity_limited",
        "reason_code": "premium_provider_unavailable",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
    }

    assert dependencies.status_code == 200
    assert dependencies.json()["status"] == "degraded"
    assert dependencies.json()["dependencies"]["premium_provider"] == {
        "status": "degraded",
        "required": False,
        "detail": "Premium provider unavailable: injected outage.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "degraded",
        "serving_effect": "continuity_limited",
        "reason_code": "premium_provider_unavailable",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
    }


    async with configured_outage_client() as (app, client):
        failing_store = StatefulGovernanceStore(app.state.container.governance_store)
        failing_store.set_outage()
        app.state.container.auth_service.store = failing_store
        app.state.container.runtime_health_service.governance_store = failing_store

        response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Governance outage must fail closed",
                    }
                ],
            },
        )
        readiness = await client.get("/health/ready")
        dependencies = await client.get("/health/dependencies")

    assert response.status_code == 503
    assert response.json() == {"detail": "Governance store unavailable."}

    assert readiness.status_code == 503
    assert readiness.json()["status"] == "not_ready"

    dependency_payload = dependencies.json()
    assert dependencies.status_code == 200
    assert dependency_payload["status"] == "not_ready"
    assert dependency_payload["dependencies"]["governance_store"] == {
        "status": "not_ready",
        "required": True,
        "detail": "Governance store query failed: injected outage",
        "dependency_class": "serving_critical",
        "lifecycle_state": "not_ready",
        "serving_effect": "fail_closed",
        "reason_code": "governance_query_failed",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
    }


@pytest.mark.asyncio
async def test_governance_outage_recovery_restores_serving_and_health_truth() -> None:
    failure_at = datetime(2026, 5, 23, 20, 0, tzinfo=UTC)
    recovery_at = datetime(2026, 5, 23, 20, 5, tzinfo=UTC)

    async with configured_outage_client() as (app, client):
        governance_store = StatefulGovernanceStore(app.state.container.governance_store)
        governance_store.set_outage(last_failure_at=failure_at)
        app.state.container.auth_service.store = governance_store
        app.state.container.runtime_health_service.governance_store = governance_store

        outage_response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Governance outage must fail closed before recovery",
                    }
                ],
            },
        )
        outage_ready = await client.get("/health/ready")
        outage_dependencies = await client.get("/health/dependencies")

        governance_store.set_ready(
            detail="Governance store recovered and is serving requests.",
            last_failure_at=failure_at,
            last_recovery_at=recovery_at,
        )

        recovered_response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Governance recovery should restore serving",
                    }
                ],
            },
        )
        recovered_ready = await client.get("/health/ready")
        recovered_dependencies = await client.get("/health/dependencies")

    assert outage_response.status_code == 503
    assert outage_response.json() == {"detail": "Governance store unavailable."}
    assert outage_ready.status_code == 503
    assert outage_ready.json()["status"] == "not_ready"
    assert outage_dependencies.status_code == 200
    assert outage_dependencies.json()["dependencies"]["governance_store"] == {
        "status": "not_ready",
        "required": True,
        "detail": "Governance store query failed: injected outage",
        "dependency_class": "serving_critical",
        "lifecycle_state": "not_ready",
        "serving_effect": "fail_closed",
        "reason_code": "governance_query_failed",
        "recovering": False,
        "last_failure_at": "2026-05-23T20:00:00+00:00",
        "last_recovery_at": None,
    }

    assert recovered_response.status_code == 200
    assert recovered_response.json()["choices"][0]["message"]["content"] == "local outage-safe response"
    assert recovered_response.headers["X-Nebula-Route-Target"] == "local"
    assert recovered_ready.status_code == 200
    assert recovered_ready.json()["status"] in {"ready", "degraded"}
    assert recovered_ready.json()["dependencies"]["governance_store"] == {
        "status": "ready",
        "required": True,
        "detail": "Governance store recovered and is serving requests.",
        "dependency_class": "serving_critical",
        "lifecycle_state": "ready",
        "serving_effect": "fail_closed",
        "reason_code": "governance_ready",
        "recovering": False,
        "last_failure_at": "2026-05-23T20:00:00+00:00",
        "last_recovery_at": "2026-05-23T20:05:00+00:00",
    }
    assert recovered_dependencies.status_code == 200
    assert recovered_dependencies.json()["status"] in {"ready", "degraded"}
    assert recovered_dependencies.json()["dependencies"]["governance_store"] == {
        "status": "ready",
        "required": True,
        "detail": "Governance store recovered and is serving requests.",
        "dependency_class": "serving_critical",
        "lifecycle_state": "ready",
        "serving_effect": "fail_closed",
        "reason_code": "governance_ready",
        "recovering": False,
        "last_failure_at": "2026-05-23T20:00:00+00:00",
        "last_recovery_at": "2026-05-23T20:05:00+00:00",
    }


@pytest.mark.asyncio
async def test_semantic_cache_recovery_moves_from_degraded_to_recovering_to_ready() -> None:
    failure_at = datetime(2026, 5, 23, 21, 0, tzinfo=UTC)
    recovery_at = datetime(2026, 5, 23, 21, 3, tzinfo=UTC)

    async with configured_outage_client() as (app, client):
        cache_service = StatefulSemanticCacheService()
        cache_service.set_outage()
        app.state.container.cache_service = cache_service
        app.state.container.chat_service.cache_service = cache_service
        app.state.container.runtime_health_service.semantic_cache = cache_service
        app.state.container.runtime_health_service.embeddings_service = (
            ReachableLocalOllamaHealth()
        )

        outage_response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Semantic cache outage should degrade before recovery",
                    }
                ],
            },
        )
        outage_ready = await client.get("/health/ready")
        outage_dependencies = await client.get("/health/dependencies")

        cache_service.set_recovering(
            last_failure_at=failure_at,
            last_recovery_at=recovery_at,
        )
        recovering_response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Semantic cache recovering should keep serving truthfully",
                    }
                ],
            },
        )
        recovering_ready = await client.get("/health/ready")
        recovering_dependencies = await client.get("/health/dependencies")

        cache_service.set_ready(
            detail="Semantic cache collection recovered and is reachable.",
            last_failure_at=failure_at,
            last_recovery_at=recovery_at,
        )
        recovered_ready = await client.get("/health/ready")
        recovered_dependencies = await client.get("/health/dependencies")

    assert outage_response.status_code == 200
    assert outage_ready.status_code == 200
    assert outage_ready.json()["status"] == "degraded"
    assert outage_dependencies.status_code == 200
    assert outage_dependencies.json()["dependencies"]["semantic_cache"] == {
        "status": "degraded",
        "required": False,
        "detail": "Qdrant unavailable: injected semantic cache outage",
        "dependency_class": "serving_optional",
        "lifecycle_state": "degraded",
        "serving_effect": "continuity_limited",
        "reason_code": "semantic_cache_unavailable",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
        "enabled": True,
    }

    assert recovering_response.status_code == 200
    assert recovering_response.json()["choices"][0]["message"]["content"] == "local outage-safe response"
    assert recovering_ready.status_code == 200
    assert recovering_ready.json()["status"] == "degraded"
    assert recovering_dependencies.status_code == 200
    assert recovering_dependencies.json()["dependencies"]["semantic_cache"] == {
        "status": "recovering",
        "required": False,
        "detail": "Qdrant recovered and warming semantic cache availability.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "recovering",
        "serving_effect": "continuity_limited",
        "reason_code": "semantic_cache_ready",
        "recovering": True,
        "last_failure_at": "2026-05-23T21:00:00+00:00",
        "last_recovery_at": "2026-05-23T21:03:00+00:00",
        "enabled": True,
    }

    assert recovered_ready.status_code == 200
    assert recovered_ready.json()["status"] == "ready"
    assert recovered_dependencies.status_code == 200
    assert recovered_dependencies.json()["status"] == "ready"
    assert recovered_dependencies.json()["dependencies"]["semantic_cache"] == {
        "status": "ready",
        "required": False,
        "detail": "Semantic cache collection recovered and is reachable.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "ready",
        "serving_effect": "continuity_limited",
        "reason_code": "semantic_cache_ready",
        "recovering": False,
        "last_failure_at": "2026-05-23T21:00:00+00:00",
        "last_recovery_at": "2026-05-23T21:03:00+00:00",
        "enabled": True,
    }


