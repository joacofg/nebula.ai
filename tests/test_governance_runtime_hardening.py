from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import HTTPException

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import ApiKeyRecord, TenantPolicy, TenantRecord
from nebula.models.openai import ChatCompletionRequest
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.policy_service import PolicyService
from nebula.services.router_service import RouterService

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeGovernanceStore:
    def __init__(self, *, spend_total: float = 0.0) -> None:
        self.spend_total = spend_total
        self.calls: list[tuple[str, datetime | None]] = []

    def tenant_spend_total(self, tenant_id: str, *, before_timestamp: datetime | None = None) -> float:
        assert tenant_id == "default"
        self.calls.append((tenant_id, before_timestamp))
        return self.spend_total


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
