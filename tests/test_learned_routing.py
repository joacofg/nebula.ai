from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import TenantPolicy
from tests.support import admin_headers, configured_app, usage

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# --- Task 5: settings, catalog and the per-tenant quality target -------------


def test_router_settings_default_to_the_two_tier_behaviour() -> None:
    settings = Settings()

    assert settings.economy_model is None
    assert settings.learned_router_enabled is False
    assert Path(settings.learned_router_path).name == "learned_router_v1.json"
    assert Path(settings.learned_router_path).parent.name == "data"


def test_router_settings_read_their_environment_aliases(monkeypatch) -> None:
    monkeypatch.setenv("NEBULA_ECONOMY_MODEL", "anthropic/claude-haiku-4.5")
    monkeypatch.setenv("NEBULA_LEARNED_ROUTER_ENABLED", "true")
    monkeypatch.setenv("NEBULA_LEARNED_ROUTER_PATH", "/tmp/router.json")

    settings = Settings()

    assert settings.economy_model == "anthropic/claude-haiku-4.5"
    assert settings.learned_router_enabled is True
    assert settings.learned_router_path == "/tmp/router.json"


def test_pricing_catalog_prices_the_economy_and_frontier_models() -> None:
    catalog = PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")

    haiku = catalog.estimate_cost("anthropic/claude-haiku-4.5", usage(1_000_000, 1_000_000))
    gpt41 = catalog.estimate_cost("openai/gpt-4.1", usage(1_000_000, 1_000_000))

    assert haiku is not None and abs(haiku - 6.0) < 1e-9
    assert gpt41 is not None and abs(gpt41 - 10.0) < 1e-9


def test_tenant_policy_quality_target_defaults_to_095() -> None:
    assert TenantPolicy().routing_quality_target == 0.95


def test_store_round_trips_the_quality_target() -> None:
    with configured_app() as app:
        with TestClient(app):
            store = app.state.container.governance_store
            stored = store.upsert_policy("default", TenantPolicy(routing_quality_target=0.8))
            reread = store.get_policy("default")

    assert stored.routing_quality_target == 0.8
    assert reread.routing_quality_target == 0.8


def test_policy_api_exposes_and_validates_the_quality_target() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            initial = client.get("/v1/admin/tenants/default/policy", headers=admin_headers())
            updated = client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json={**initial.json(), "routing_quality_target": 0.9},
            )
            reread = client.get("/v1/admin/tenants/default/policy", headers=admin_headers())
            too_low = client.put(
                "/v1/admin/tenants/default/policy",
                headers=admin_headers(),
                json={**initial.json(), "routing_quality_target": 0.3},
            )

    assert initial.json()["routing_quality_target"] == 0.95
    assert updated.status_code == 200
    assert reread.json()["routing_quality_target"] == 0.9
    assert too_low.status_code == 422
