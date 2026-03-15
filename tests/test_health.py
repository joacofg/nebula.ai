from fastapi.testclient import TestClient

from tests.support import configured_app


def test_healthcheck() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_degraded_optional_dependencies() -> None:
    class DegradedRuntimeHealthService:
        async def readiness(self) -> dict[str, object]:
            return {
                "status": "degraded",
                "runtime_profile": "premium_first",
                "dependencies": {
                    "gateway": {"status": "ready", "required": True, "detail": "ok"},
                    "governance_store": {"status": "ready", "required": True, "detail": "ok"},
                    "semantic_cache": {
                        "status": "degraded",
                        "required": False,
                        "detail": "Qdrant unavailable.",
                    },
                    "local_ollama": {
                        "status": "degraded",
                        "required": False,
                        "detail": "Ollama unavailable.",
                    },
                },
            }

        async def dependencies(self) -> dict[str, dict[str, object]]:
            return (await self.readiness())["dependencies"]

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
            app.state.container.runtime_health_service = DegradedRuntimeHealthService()
            ready = client.get("/health/ready")
            dependencies = client.get("/health/dependencies")

    ready_body = ready.json()
    dependencies_body = dependencies.json()

    assert ready.status_code == 200
    assert ready_body["status"] == "degraded"
    assert ready_body["runtime_profile"] == "premium_first"
    assert ready_body["dependencies"]["gateway"]["status"] == "ready"
    assert ready_body["dependencies"]["governance_store"]["status"] == "ready"
    assert ready_body["dependencies"]["semantic_cache"]["status"] == "degraded"
    assert ready_body["dependencies"]["local_ollama"]["status"] == "degraded"
    assert dependencies.status_code == 200
    assert dependencies_body["runtime_profile"] == "premium_first"


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
