from fastapi.testclient import TestClient

from nebula.models.resilience import build_dependency_health
from tests.support import configured_app


class FakeSemanticCacheHealth:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    async def health_status(self) -> dict[str, object]:
        return self.payload


def test_healthcheck() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_degraded_optional_semantic_cache_dependencies() -> None:
    semantic_cache_health = build_dependency_health(
        dependency_class="serving_optional",
        lifecycle_state="degraded",
        serving_effect="continuity_limited",
        reason_code="semantic_cache_unavailable",
        detail="Qdrant unavailable: injected semantic cache outage",
        required=False,
        last_failure_at=None,
        last_recovery_at=None,
        extra={"enabled": True},
    )

    with configured_app() as app:
        with TestClient(app) as client:
            app.state.container.runtime_health_service.semantic_cache = FakeSemanticCacheHealth(
                semantic_cache_health
            )
            ready = client.get("/health/ready")
            dependencies = client.get("/health/dependencies")

    ready_body = ready.json()
    dependencies_body = dependencies.json()

    assert ready.status_code == 200
    assert ready_body["status"] == "degraded"
    semantic_cache_ready = ready_body["dependencies"]["semantic_cache"]
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
    assert dependencies_body["status"] == "degraded"
    assert dependencies_body["dependencies"]["semantic_cache"] == {
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


def test_readiness_reports_degraded_optional_dependencies() -> None:
    class DegradedPremiumProviderHealth:
        async def health_status(self) -> dict[str, object]:
            return build_dependency_health(
                dependency_class="serving_optional",
                lifecycle_state="degraded",
                serving_effect="continuity_limited",
                reason_code="premium_provider_timeout",
                detail="Premium provider probe timed out.",
                required=False,
                last_failure_at=None,
                last_recovery_at=None,
            )

    with configured_app(
        NEBULA_ENV="production",
        NEBULA_RUNTIME_PROFILE="premium_first",
        NEBULA_PREMIUM_PROVIDER="openai_compatible",
        NEBULA_PREMIUM_BASE_URL="https://api.openai.com/v1",
        NEBULA_PREMIUM_API_KEY="prod-secret",
        NEBULA_PREMIUM_MODEL="gpt-4o-mini",
        NEBULA_ADMIN_API_KEY="prod-admin-key",
        NEBULA_BOOTSTRAP_API_KEY="prod-bootstrap-key",
    ) as app:
        with TestClient(app) as client:
            app.state.container.runtime_health_service.premium_provider_health = (
                DegradedPremiumProviderHealth()
            )
            ready = client.get("/health/ready")
            dependencies = client.get("/health/dependencies")

    ready_body = ready.json()
    dependencies_body = dependencies.json()
    ready_dependency_names = list(ready_body["dependencies"].keys())
    dependency_names = list(dependencies_body["dependencies"].keys())

    assert ready.status_code == 200
    assert ready_body["status"] == "degraded"
    assert ready_body["runtime_profile"] == "premium_first"
    assert ready_body["dependencies"]["gateway"]["status"] == "ready"
    assert ready_body["dependencies"]["governance_store"]["status"] == "ready"
    assert ready_body["dependencies"]["premium_provider"] == {
        "status": "degraded",
        "required": False,
        "detail": "Premium provider probe timed out.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "degraded",
        "serving_effect": "continuity_limited",
        "reason_code": "premium_provider_timeout",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
    }
    assert ready_body["dependencies"]["retention_lifecycle"]["status"] == "ready"
    assert ready_body["dependencies"]["retention_lifecycle"]["required"] is False
    assert ready_dependency_names.index("governance_store") < ready_dependency_names.index(
        "retention_lifecycle"
    )
    assert dependency_names.index("governance_store") < dependency_names.index("retention_lifecycle")
    assert dependencies.status_code == 200
    assert dependencies_body["status"] == "degraded"
    assert dependencies_body["runtime_profile"] == "premium_first"
    assert dependencies_body["dependencies"]["premium_provider"]["detail"] == "Premium provider probe timed out."


def test_readiness_returns_503_when_serving_critical_dependency_is_not_ready() -> None:
    class BrokenGovernanceStore:
        def health_status(self) -> dict[str, object]:
            return build_dependency_health(
                dependency_class="serving_critical",
                lifecycle_state="not_ready",
                serving_effect="fail_closed",
                reason_code="governance_query_failed",
                detail="Database unreachable.",
                required=False,
            )

    with configured_app() as app:
        with TestClient(app) as client:
            app.state.container.runtime_health_service.governance_store = BrokenGovernanceStore()
            ready = client.get("/health/ready")
            dependencies = client.get("/health/dependencies")

    assert ready.status_code == 503
    assert ready.json()["status"] == "not_ready"
    assert ready.json()["dependencies"]["governance_store"] == {
        "status": "not_ready",
        "required": False,
        "detail": "Database unreachable.",
        "dependency_class": "serving_critical",
        "lifecycle_state": "not_ready",
        "serving_effect": "fail_closed",
        "reason_code": "governance_query_failed",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
    }
    assert dependencies.status_code == 200
    assert dependencies.json()["status"] == "not_ready"


def test_readiness_reports_recovering_dependencies_as_degraded() -> None:
    class RecoveringPremiumProviderHealth:
        async def health_status(self) -> dict[str, object]:
            return build_dependency_health(
                dependency_class="serving_optional",
                lifecycle_state="recovering",
                serving_effect="continuity_limited",
                reason_code="premium_provider_recovering",
                detail="Premium provider probe recovered and is stabilizing.",
                required=False,
                recovering=True,
                last_failure_at=None,
                last_recovery_at=None,
            )

    with configured_app(
        NEBULA_PREMIUM_PROVIDER="openai_compatible",
        NEBULA_PREMIUM_BASE_URL="https://api.openai.com/v1",
        NEBULA_PREMIUM_API_KEY="prod-secret",
        NEBULA_PREMIUM_MODEL="gpt-4o-mini",
    ) as app:
        with TestClient(app) as client:
            app.state.container.runtime_health_service.premium_provider_health = (
                RecoveringPremiumProviderHealth()
            )
            ready = client.get("/health/ready")
            dependencies = client.get("/health/dependencies")

    assert ready.status_code == 200
    assert ready.json()["status"] == "degraded"
    assert ready.json()["dependencies"]["premium_provider"] == {
        "status": "recovering",
        "required": False,
        "detail": "Premium provider probe recovered and is stabilizing.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "recovering",
        "serving_effect": "continuity_limited",
        "reason_code": "premium_provider_recovering",
        "recovering": True,
        "last_failure_at": None,
        "last_recovery_at": None,
    }
    assert dependencies.status_code == 200
    assert dependencies.json()["status"] == "degraded"


def test_readiness_returns_503_for_recovering_serving_critical_dependency() -> None:
    class RecoveringGovernanceStore:
        def health_status(self) -> dict[str, object]:
            return build_dependency_health(
                dependency_class="serving_critical",
                lifecycle_state="recovering",
                serving_effect="fail_closed",
                reason_code="governance_ready",
                detail="Governance store recovered and is stabilizing.",
                required=True,
                recovering=True,
                last_failure_at=None,
                last_recovery_at=None,
            )

    with configured_app() as app:
        with TestClient(app) as client:
            app.state.container.runtime_health_service.governance_store = RecoveringGovernanceStore()
            ready = client.get("/health/ready")
            dependencies = client.get("/health/dependencies")

    assert ready.status_code == 503
    assert ready.json()["status"] == "not_ready"
    assert ready.json()["dependencies"]["governance_store"] == {
        "status": "recovering",
        "required": True,
        "detail": "Governance store recovered and is stabilizing.",
        "dependency_class": "serving_critical",
        "lifecycle_state": "recovering",
        "serving_effect": "fail_closed",
        "reason_code": "governance_ready",
        "recovering": True,
        "last_failure_at": None,
        "last_recovery_at": None,
    }
    assert dependencies.status_code == 200
    assert dependencies.json()["status"] == "not_ready"


def test_dependencies_include_mock_premium_provider_status() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            dependencies = client.get("/health/dependencies")

    assert dependencies.status_code == 200
    assert dependencies.json()["dependencies"]["premium_provider"] == {
        "status": "ready",
        "required": False,
        "detail": "Mock premium provider configured for local development.",
        "dependency_class": "serving_optional",
        "lifecycle_state": "ready",
        "serving_effect": "continuity_limited",
        "reason_code": "premium_provider_mock",
        "recovering": False,
        "last_failure_at": None,
        "last_recovery_at": None,
    }


