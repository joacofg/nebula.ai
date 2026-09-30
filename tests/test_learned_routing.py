from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import ApiKeyRecord, TenantPolicy, TenantRecord
from nebula.models.openai import ChatCompletionRequest
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.learned_router import LearnedRouterModel
from nebula.services.policy_service import PolicyService
from nebula.services.router_service import RouterService
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


# --- Task 6: the router consults the learned model ----------------------------

LOCAL_MODEL = "qwen2.5:7b"
ECONOMY_MODEL = "anthropic/claude-haiku-4.5"
FRONTIER_MODEL = "openai/gpt-4.1"

# Two dimensions: x[0] drives p_local, x[1] drives p_economy.
LOCAL_VECTOR = [6.0, -6.0]
ECONOMY_VECTOR = [-6.0, 6.0]
FRONTIER_VECTOR = [-6.0, -6.0]


def _artifact() -> dict:
    return {
        "version": 1,
        "label": "v1-test",
        "embedding_model": "nomic-embed-text",
        "prefix": "none",
        "models": {
            "local": {"weights": [1.0, 0.0], "bias": 0.0},
            "economy": {"weights": [0.0, 1.0], "bias": 0.0},
        },
        "operating_points": [
            {"tau_local": 0.5, "tau_economy": 0.5, "quality": 0.9, "cost_per_prompt": 0.001},
        ],
    }


def _write_artifact(tmp_path: Path) -> Path:
    path = tmp_path / "learned_router_test.json"
    path.write_text(json.dumps(_artifact()), encoding="utf-8")
    return path


def _learned() -> LearnedRouterModel:
    return LearnedRouterModel.from_dict(_artifact())


def _settings(**overrides) -> Settings:
    values = {
        "local_model": LOCAL_MODEL,
        "premium_model": FRONTIER_MODEL,
        "economy_model": ECONOMY_MODEL,
    }
    values.update(overrides)
    return Settings(**values)


def _request(content: str = "hello", model: str = "nebula-auto") -> ChatCompletionRequest:
    return ChatCompletionRequest(model=model, messages=[{"role": "user", "content": content}])


def _policy(**overrides) -> TenantPolicy:
    values = {
        "allowed_premium_models": [ECONOMY_MODEL, FRONTIER_MODEL],
        "routing_quality_target": 0.9,
    }
    values.update(overrides)
    return TenantPolicy(**values)


def _tenant_context(policy: TenantPolicy) -> AuthenticatedTenantContext:
    now = datetime.now(UTC)
    return AuthenticatedTenantContext(
        tenant=TenantRecord(id="default", name="Default", created_at=now, updated_at=now),
        api_key=ApiKeyRecord(
            id="key-1",
            name="default",
            key_prefix="nebula-",
            tenant_id="default",
            allowed_tenant_ids=["default"],
            created_at=now,
            updated_at=now,
        ),
        policy=policy,
    )


class _PolicyStore:
    def tenant_spend_total(self, tenant_id: str, *, before_timestamp=None) -> float:
        return 0.0

    def summarize_calibration_evidence(self, *, tenant_id: str):
        return None


def _policy_service(settings: Settings) -> PolicyService:
    return PolicyService(
        settings,
        _PolicyStore(),
        PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json"),
    )


async def _route(vector, *, policy=None, request=None, settings=None, routing_mode="auto"):
    settings = settings or _settings()
    router = RouterService(settings, learned=_learned())
    return await router.choose_target_with_reason(
        "hello",
        request or _request(),
        routing_mode=routing_mode,
        policy=policy or _policy(),
        prompt_embedding=vector,
    )


def test_router_uses_embeddings_only_with_a_learned_model() -> None:
    assert RouterService(_settings()).uses_embeddings is False
    assert RouterService(_settings(), learned=_learned()).uses_embeddings is True


async def test_learned_router_picks_the_tier_from_the_vector() -> None:
    local = await _route(LOCAL_VECTOR)
    economy = await _route(ECONOMY_VECTOR)
    frontier = await _route(FRONTIER_VECTOR)

    assert (local.target, local.reason, local.model) == ("local", "learned_router", None)
    assert local.signals["tier"] == "local"
    assert (economy.target, economy.model, economy.signals["tier"]) == (
        "premium",
        ECONOMY_MODEL,
        "economy",
    )
    assert (frontier.target, frontier.model, frontier.signals["tier"]) == (
        "premium",
        FRONTIER_MODEL,
        "frontier",
    )


async def test_learned_decision_carries_probabilities_point_and_heuristic_signals() -> None:
    decision = await _route(ECONOMY_VECTOR)

    signals = decision.signals
    assert decision.score == pytest.approx(1 - signals["p_local"])
    assert signals["p_economy"] > 0.99
    assert signals["quality_target"] == 0.9
    assert signals["operating_point"] == {
        "tau_local": 0.5,
        "tau_economy": 0.5,
        "quality": 0.9,
        "cost_per_prompt": 0.001,
    }
    assert signals["learned_router"] == "v1-test"
    # Heuristic signals stay for continuity with the ledger and the console.
    assert signals["token_count"] == 2
    assert signals["route_mode"] == "calibrated"


async def test_quality_target_above_every_point_routes_to_frontier() -> None:
    decision = await _route(LOCAL_VECTOR, policy=_policy(routing_quality_target=1.0))

    assert decision.target == "premium"
    assert decision.model == FRONTIER_MODEL
    assert decision.signals["tier"] == "frontier"
    # ALL_FRONTIER's inf/nan must not leak into JSON-persisted signals.
    assert decision.signals["operating_point"]["tau_local"] is None
    json.dumps(decision.signals, allow_nan=False)


async def test_economy_tier_without_an_economy_model_goes_to_frontier() -> None:
    decision = await _route(ECONOMY_VECTOR, settings=_settings(economy_model=None))

    assert decision.target == "premium"
    assert decision.model == FRONTIER_MODEL
    assert decision.signals["tier"] == "frontier"


async def test_missing_embedding_falls_back_to_the_heuristic_with_a_signal() -> None:
    decision = await _route(None)

    assert decision.reason == "token_complexity"
    assert decision.target == "local"
    assert decision.model is None
    assert decision.signals["learned_router"] == "embedding_unavailable"


async def test_embedding_of_the_wrong_dimension_falls_back_to_the_heuristic() -> None:
    decision = await _route([1.0, 2.0, 3.0])

    assert decision.reason == "token_complexity"
    assert decision.signals["learned_router"] == "embedding_dimension_mismatch"


async def test_explicit_model_and_forced_modes_bypass_the_learned_router() -> None:
    explicit = await _route(LOCAL_VECTOR, request=_request(model=FRONTIER_MODEL))
    premium_only = await _route(LOCAL_VECTOR, routing_mode="premium_only")
    local_only = await _route(FRONTIER_VECTOR, routing_mode="local_only")

    assert (explicit.target, explicit.reason, explicit.model) == (
        "premium",
        "explicit_premium_model",
        None,
    )
    assert (premium_only.target, premium_only.reason) == ("premium", "policy_premium_only")
    assert (local_only.target, local_only.reason) == ("local", "policy_local_only")


async def _evaluate(policy: TenantPolicy, vector, *, settings=None):
    settings = settings or _settings()
    return await _policy_service(settings).evaluate(
        request=_request(),
        tenant_context=_tenant_context(policy),
        router_service=RouterService(settings, learned=_learned()),
        prompt="hello",
        prompt_embedding=vector,
    )


async def test_calibrated_routing_disabled_also_disables_the_learned_router() -> None:
    evaluation = await _evaluate(_policy(calibrated_routing_enabled=False), ECONOMY_VECTOR)

    assert evaluation.route_decision.reason == "calibrated_routing_disabled"
    assert evaluation.route_decision.target == "local"
    assert evaluation.route_decision.model is None


async def test_allowed_models_check_uses_the_decision_model() -> None:
    denied = await _evaluate(_policy(allowed_premium_models=[FRONTIER_MODEL]), ECONOMY_VECTOR)
    allowed = await _evaluate(_policy(allowed_premium_models=[ECONOMY_MODEL]), ECONOMY_VECTOR)

    assert denied.denied is True
    assert denied.denial_detail == f"Premium model '{ECONOMY_MODEL}' is not allowed for this tenant."
    assert allowed.denied is False


async def test_cost_cap_is_priced_by_the_decision_model() -> None:
    service = _policy_service(_settings())
    request = _request()
    economy_cost = service._estimate_request_cost(request, ECONOMY_MODEL)
    frontier_cost = service._estimate_request_cost(request, FRONTIER_MODEL)
    assert economy_cost is not None and frontier_cost is not None
    cap = (economy_cost + frontier_cost) / 2

    economy = await _evaluate(_policy(max_premium_cost_per_request=cap), ECONOMY_VECTOR)
    frontier = await _evaluate(_policy(max_premium_cost_per_request=cap), FRONTIER_VECTOR)

    assert economy.denied is False
    assert economy.projected_premium_cost == pytest.approx(economy_cost)
    assert frontier.denial_detail == "Request exceeds the tenant premium spend guardrail."


async def test_policy_resolve_forwards_the_embedding() -> None:
    settings = _settings()
    resolution = await _policy_service(settings).resolve(
        prompt="hello",
        request=_request(),
        tenant_context=_tenant_context(_policy()),
        router_service=RouterService(settings, learned=_learned()),
        prompt_embedding=ECONOMY_VECTOR,
    )

    assert resolution.route_decision.reason == "learned_router"
    assert resolution.route_decision.model == ECONOMY_MODEL


def test_container_loads_the_artifact_only_when_enabled(tmp_path: Path) -> None:
    artifact = _write_artifact(tmp_path)
    with configured_app() as app:
        with TestClient(app):
            assert app.state.container.router_service.uses_embeddings is False
    with configured_app(
        NEBULA_LEARNED_ROUTER_ENABLED="true", NEBULA_LEARNED_ROUTER_PATH=str(artifact)
    ) as app:
        with TestClient(app):
            router = app.state.container.router_service
            assert router.uses_embeddings is True
            assert router.learned.version == "v1-test"


def test_container_fails_loud_on_a_missing_or_invalid_artifact(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({**_artifact(), "version": 2}), encoding="utf-8")

    with configured_app(
        NEBULA_LEARNED_ROUTER_ENABLED="true",
        NEBULA_LEARNED_ROUTER_PATH=str(tmp_path / "missing.json"),
    ) as app:
        with pytest.raises(FileNotFoundError):
            with TestClient(app):
                pass
    with configured_app(
        NEBULA_LEARNED_ROUTER_ENABLED="true", NEBULA_LEARNED_ROUTER_PATH=str(invalid)
    ) as app:
        with pytest.raises(ValueError, match="version"):
            with TestClient(app):
                pass
