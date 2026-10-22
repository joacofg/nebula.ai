from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import (
    ApiKeyRecord,
    CalibrationEvidenceSummary,
    TenantPolicy,
    TenantRecord,
)
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionResult
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyService
from nebula.services.router_service import RouterService
from tests.support import StubProvider, admin_headers, configured_app, usage

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeGovernanceStore:
    def __init__(
        self,
        *,
        spend_total: float = 0.0,
        evidence_summary: CalibrationEvidenceSummary | None = None,
    ) -> None:
        self.spend_total = spend_total
        self.calls: list[tuple[str, datetime | None]] = []
        self.evidence_summary = evidence_summary
        self.evidence_summary_calls: list[str] = []

    def tenant_spend_total(self, tenant_id: str, *, before_timestamp: datetime | None = None) -> float:
        assert tenant_id == "default"
        self.calls.append((tenant_id, before_timestamp))
        return self.spend_total

    def summarize_calibration_evidence(self, *, tenant_id: str) -> CalibrationEvidenceSummary:
        assert tenant_id == "default"
        self.evidence_summary_calls.append(tenant_id)
        return self.evidence_summary or CalibrationEvidenceSummary(
            tenant_id=tenant_id,
            scope="tenant",
            state="thin",
            state_reason="No eligible calibrated routing evidence is available yet.",
            generated_at=datetime.now(UTC),
            latest_eligible_request_at=None,
            latest_any_request_at=None,
            eligible_request_count=0,
            sufficient_request_count=0,
            thin_request_threshold=GovernanceStore.CALIBRATION_THIN_REQUEST_THRESHOLD,
            staleness_threshold_hours=GovernanceStore.CALIBRATION_STALENESS_THRESHOLD_HOURS,
            excluded_request_count=0,
            gated_request_count=0,
            degraded_request_count=0,
        )


def _tenant_context(policy: TenantPolicy) -> AuthenticatedTenantContext:
    now = datetime.now(UTC)
    return AuthenticatedTenantContext(
        tenant=TenantRecord(
            id="default",
            name="Default",
            created_at=now,
            updated_at=now,
        ),
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


def _request(model: str = "nebula-auto", *, prompt: str = "hello", max_tokens: int | None = None) -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )


def _pricing() -> PricingCatalog:
    return PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")


@pytest.mark.asyncio
async def test_routing_mode_matrix() -> None:
    settings = Settings()
    pricing = _pricing()
    router_service = RouterService(settings)

    auto_service = PolicyService(settings, FakeGovernanceStore(), pricing)
    auto_resolution = await auto_service.resolve(
        prompt="hello",
        request=_request(),
        tenant_context=_tenant_context(TenantPolicy()),
        router_service=router_service,
    )

    local_only_service = PolicyService(settings, FakeGovernanceStore(), pricing)
    local_only_resolution = await local_only_service.resolve(
        prompt="analyze this design",
        request=_request(),
        tenant_context=_tenant_context(TenantPolicy(routing_mode_default="local_only")),
        router_service=router_service,
    )

    premium_only_service = PolicyService(settings, FakeGovernanceStore(), pricing)
    premium_only_resolution = await premium_only_service.resolve(
        prompt="hello",
        request=_request(),
        tenant_context=_tenant_context(TenantPolicy(routing_mode_default="premium_only")),
        router_service=router_service,
    )

    assert auto_resolution.route_decision.target == "local"
    assert auto_resolution.route_decision.reason == "token_complexity"
    assert local_only_resolution.route_decision.target == "local"
    assert local_only_resolution.route_decision.reason == "policy_local_only"
    assert premium_only_resolution.route_decision.target == "premium"
    assert premium_only_resolution.route_decision.reason == "policy_premium_only"


@pytest.mark.asyncio
async def test_routing_mode_denies_explicit_model_conflicts() -> None:
    settings = Settings()
    service = PolicyService(settings, FakeGovernanceStore(), _pricing())
    router_service = RouterService(settings)

    with pytest.raises(HTTPException) as premium_only_local_exc:
        await service.resolve(
            prompt="hello",
            request=_request(settings.local_model),
            tenant_context=_tenant_context(TenantPolicy(routing_mode_default="premium_only")),
            router_service=router_service,
        )

    with pytest.raises(HTTPException) as local_only_premium_exc:
        await service.resolve(
            prompt="hello",
            request=_request("openai/gpt-4o-mini"),
            tenant_context=_tenant_context(TenantPolicy(routing_mode_default="local_only")),
            router_service=router_service,
        )

    assert premium_only_local_exc.value.status_code == 403
    assert premium_only_local_exc.value.detail == "Tenant policy requires premium-only routing."
    assert local_only_premium_exc.value.status_code == 403
    assert local_only_premium_exc.value.detail == "Tenant policy does not allow explicit premium routing."


@pytest.mark.asyncio
async def test_policy_enforces_premium_allowlist_and_request_guardrail() -> None:
    settings = Settings()
    service = PolicyService(settings, FakeGovernanceStore(), _pricing())
    router_service = RouterService(settings)

    with pytest.raises(HTTPException) as allowlist_exc:
        await service.resolve(
            prompt="hello",
            request=_request("openai/gpt-4.1-mini"),
            tenant_context=_tenant_context(
                TenantPolicy(
                    routing_mode_default="premium_only",
                    allowed_premium_models=["openai/gpt-4o-mini"],
                )
            ),
            router_service=router_service,
        )

    with pytest.raises(HTTPException) as guardrail_exc:
        await service.resolve(
            prompt="hello",
            request=_request("openai/gpt-4o-mini", max_tokens=2048),
            tenant_context=_tenant_context(
                TenantPolicy(
                    routing_mode_default="premium_only",
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    max_premium_cost_per_request=0.0001,
                )
            ),
            router_service=router_service,
        )

    assert allowlist_exc.value.status_code == 403
    assert allowlist_exc.value.detail == "Premium model 'openai/gpt-4.1-mini' is not allowed for this tenant."
    assert guardrail_exc.value.status_code == 403
    assert guardrail_exc.value.detail == "Request exceeds the tenant premium spend guardrail."


@pytest.mark.asyncio
async def test_soft_budget_annotations_do_not_block_routing() -> None:
    settings = Settings()
    service = PolicyService(settings, FakeGovernanceStore(spend_total=12.0), _pricing())
    resolution = await service.resolve(
        prompt="analyze this design",
        request=_request(),
        tenant_context=_tenant_context(TenantPolicy(soft_budget_usd=10.0)),
        router_service=RouterService(settings),
    )

    assert resolution.route_decision.target == "premium"
    assert resolution.soft_budget_exceeded is True
    assert "soft_budget=exceeded" in resolution.policy_outcome


@pytest.mark.asyncio
async def test_hard_budget_downgrades_auto_routed_premium_requests_to_local() -> None:
    settings = Settings()
    service = PolicyService(settings, FakeGovernanceStore(spend_total=12.0), _pricing())
    resolution = await service.resolve(
        prompt="analyze this architecture tradeoff",
        request=_request(),
        tenant_context=_tenant_context(
            TenantPolicy(
                hard_budget_limit_usd=10.0,
                hard_budget_enforcement="downgrade",
            )
        ),
        router_service=RouterService(settings),
    )

    assert resolution.route_decision.target == "local"
    assert resolution.route_decision.reason == "hard_budget_downgrade"
    assert resolution.route_decision.signals["route_mode"] == "calibrated"
    assert resolution.route_decision.signals["score_components"]["total_score"] == resolution.route_decision.score
    assert resolution.hard_budget_exceeded is True
    assert resolution.tenant_spend_total == 12.0
    assert "hard_budget=exceeded" in resolution.policy_outcome
    assert "budget_action=downgraded_to_local" in resolution.policy_outcome
    assert resolution.projected_premium_cost is None


@pytest.mark.asyncio
async def test_hard_budget_denies_explicit_premium_requests_when_downgrade_not_allowed() -> None:
    settings = Settings()
    service = PolicyService(settings, FakeGovernanceStore(spend_total=12.0), _pricing())
    router_service = RouterService(settings)

    with pytest.raises(HTTPException) as exc_info:
        await service.resolve(
            prompt="premium required",
            request=_request("openai/gpt-4o-mini"),
            tenant_context=_tenant_context(
                TenantPolicy(
                    allowed_premium_models=["openai/gpt-4o-mini"],
                    hard_budget_limit_usd=10.0,
                    hard_budget_enforcement="downgrade",
                )
            ),
            router_service=router_service,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Tenant hard budget limit reached; premium routing is blocked "
        "(spent_usd=12, limit_usd=10)."
    )


@pytest.mark.asyncio
async def test_hard_budget_evaluate_uses_before_timestamp_for_replay_windows() -> None:
    settings = Settings()
    store = FakeGovernanceStore(spend_total=12.0)
    service = PolicyService(settings, store, _pricing())
    replay_timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    evaluation = await service.evaluate(
        request=_request(prompt="analyze this architecture tradeoff"),
        tenant_context=_tenant_context(
            TenantPolicy(
                hard_budget_limit_usd=10.0,
                hard_budget_enforcement="deny",
            )
        ),
        router_service=RouterService(settings),
        replay_context=None,
        before_timestamp=replay_timestamp,
        prompt="analyze this architecture tradeoff",
    )

    assert store.calls == [("default", replay_timestamp)]
    assert evaluation.denied is True
    assert evaluation.hard_budget_exceeded is True
    assert evaluation.tenant_spend_total == 12.0


def test_restart_keeps_bootstrap_tenant_policy() -> None:
    with configured_app() as app:
        with TestClient(app):
            store = app.state.container.governance_store
            tenant_id = store.settings.bootstrap_tenant_id
            store.update_tenant(tenant_id, active=False)
            store.upsert_policy(
                tenant_id,
                store.default_policy().model_copy(
                    update={
                        "rate_limit_requests_per_minute": 5,
                        "routing_quality_target": 0.8,
                        "hard_budget_limit_usd": 1.0,
                    }
                ),
            )

            store.ensure_bootstrap()

            tenant = store.get_tenant(tenant_id)
            policy = store.get_policy(tenant_id)

    assert tenant is not None
    assert tenant.active is False
    assert policy.rate_limit_requests_per_minute == 5
    assert policy.routing_quality_target == 0.8
    assert policy.hard_budget_limit_usd == 1.0


_STORE_LOGGER = "nebula.services.governance_store"


def _restart_warnings(
    caplog, allowed_premium_models: list[str] | None
) -> tuple[list[str], str, str]:
    """Restart with the given stored allowlist (None keeps the default one)."""
    with configured_app() as app:
        with TestClient(app):
            store = app.state.container.governance_store
            tenant_id = store.settings.bootstrap_tenant_id
            if allowed_premium_models is not None:
                store.upsert_policy(
                    tenant_id,
                    store.default_policy().model_copy(
                        update={"allowed_premium_models": allowed_premium_models}
                    ),
                )
            caplog.clear()
            with caplog.at_level(logging.WARNING, logger=_STORE_LOGGER):
                store.ensure_bootstrap()

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == _STORE_LOGGER and record.levelno == logging.WARNING
    ]
    return messages, tenant_id, store.settings.premium_model


def test_restart_warns_when_the_bootstrap_allowlist_lacks_the_premium_model(caplog) -> None:
    # Startup never rewrites an existing bootstrap policy, so a database first
    # booted with other model settings (`make demo` vs `make run`) keeps an
    # allowlist that rejects this process's premium model with a 403.
    messages, tenant_id, premium_model = _restart_warnings(
        caplog, ["openai/gpt-4.1", "anthropic/claude-haiku-4.5"]
    )

    assert len(messages) == 1
    assert tenant_id in messages[0]
    assert premium_model in messages[0]
    assert "openai/gpt-4.1" in messages[0]
    assert "console" in messages[0]
    assert "database" in messages[0]


@pytest.mark.parametrize("allowed", [None, []], ids=["default", "empty"])
def test_restart_is_quiet_when_the_premium_model_is_allowed(
    caplog, allowed: list[str] | None
) -> None:
    # An empty allowlist allows every premium model.
    messages, _, _ = _restart_warnings(caplog, allowed)

    assert messages == []


def _revoke_bootstrap_key(store: GovernanceStore) -> None:
    bootstrap = store.find_api_key(store.settings.bootstrap_api_key)
    assert bootstrap is not None
    store.revoke_api_key(bootstrap.id)


def test_restart_with_revoked_bootstrap_key() -> None:
    with configured_app() as app:
        with TestClient(app):
            store = app.state.container.governance_store
            _revoke_bootstrap_key(store)

            store.ensure_bootstrap()

            still_usable = store.find_api_key(store.settings.bootstrap_api_key)

    assert still_usable is None


def test_operator_flows_work_with_revoked_bootstrap_key() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            container = app.state.container
            container.local_provider = StubProvider(
                "ollama",
                completion_result=CompletionResult(
                    content="local response",
                    model="llama3.2:3b",
                    provider="ollama",
                    usage=usage(),
                ),
            )
            container.provider_registry.local_provider = container.local_provider
            _revoke_bootstrap_key(container.governance_store)

            policy = client.get("/v1/admin/tenants/default/policy", headers=admin_headers()).json()
            recommendations = client.get(
                "/v1/admin/tenants/default/recommendations", headers=admin_headers()
            )
            simulation = client.post(
                "/v1/admin/tenants/default/policy/simulate",
                headers=admin_headers(),
                json={"candidate_policy": policy},
            )
            playground = client.post(
                "/v1/admin/playground/completions",
                headers=admin_headers(),
                json={
                    "tenant_id": "default",
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": False,
                },
            )

    assert recommendations.status_code == 200
    assert simulation.status_code == 200
    assert playground.status_code == 200


def test_fresh_database_gets_bootstrap_tenant_and_key() -> None:
    with configured_app() as app:
        with TestClient(app):
            store = app.state.container.governance_store
            tenant = store.get_tenant(store.settings.bootstrap_tenant_id)
            policy = store.get_policy(store.settings.bootstrap_tenant_id)
            key = store.find_api_key(store.settings.bootstrap_api_key)

    assert tenant is not None
    assert tenant.name == store.settings.bootstrap_tenant_name
    assert tenant.active is True
    assert policy == store.default_policy()
    assert key is not None
    assert key.revoked_at is None
    assert key.allowed_tenant_ids == [store.settings.bootstrap_tenant_id]
