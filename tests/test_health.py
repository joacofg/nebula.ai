from fastapi.testclient import TestClient

from tests.support import configured_app


def test_healthcheck() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_degraded_optional_dependencies() -> None:
    class DegradedPremiumProviderHealth:
        async def health_status(self) -> dict[str, object]:
            return {
                "status": "degraded",
                "required": False,
                "detail": "Premium provider probe timed out.",
            }

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

    assert ready.status_code == 200
    assert ready_body["status"] == "degraded"
    assert ready_body["runtime_profile"] == "premium_first"
    assert ready_body["dependencies"]["gateway"]["status"] == "ready"
    assert ready_body["dependencies"]["governance_store"]["status"] == "ready"
    assert ready_body["dependencies"]["premium_provider"]["status"] == "degraded"
    assert ready_body["dependencies"]["premium_provider"]["required"] is False
    assert dependencies.status_code == 200
    assert dependencies_body["runtime_profile"] == "premium_first"
    assert dependencies_body["dependencies"]["premium_provider"]["detail"] == "Premium provider probe timed out."


def test_readiness_returns_503_when_required_dependency_is_not_ready() -> None:
    class BrokenRuntimeHealthService:
        async def readiness(self) -> dict[str, object]:
            return {
                "status": "not_ready",
                "runtime_profile": "premium_first",
                "dependencies": {
                    "gateway": {"status": "ready", "required": True, "detail": "ok"},
                    "governance_store": {
                        "status": "not_ready",
                        "required": True,
                        "detail": "Database unreachable.",
                    },
                },
            }

        async def dependencies(self) -> dict[str, dict[str, object]]:
            return (await self.readiness())["dependencies"]

    with configured_app() as app:
        with TestClient(app) as client:
            app.state.container.runtime_health_service = BrokenRuntimeHealthService()
            response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_dependencies_include_mock_premium_provider_status() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            dependencies = client.get("/health/dependencies")

    assert dependencies.status_code == 200
    assert dependencies.json()["dependencies"]["premium_provider"] == {
        "status": "ready",
        "required": False,
        "detail": "Mock premium provider configured for local development.",
    }
