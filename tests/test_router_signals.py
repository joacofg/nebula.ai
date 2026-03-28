from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nebula.core.config import Settings
from nebula.models.governance import TenantPolicy
from nebula.models.openai import ChatCompletionRequest
from nebula.services.router_service import RouteDecision, RouterService
from tests.support import admin_headers, auth_headers, configured_app


def _request(model: str = "nebula-auto", prompt: str = "hello") -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )


@pytest.mark.asyncio
async def test_route_decision_carries_signals() -> None:
    decision = RouteDecision(target="local", reason="token_complexity")

    assert decision.signals == {}
    assert decision.score == 0.0


@pytest.mark.asyncio
async def test_token_count_signal_from_prompt() -> None:
    router = RouterService(Settings())

    decision = await router.choose_target_with_reason(
        "a" * 120,
        _request(prompt="a" * 120),
    )

    assert decision.reason == "token_complexity"
    assert decision.signals["token_count"] == 30
    assert decision.signals["complexity_tier"] == "low"
    assert decision.signals["budget_proximity"] is None
    assert decision.signals["model_constraint"] is False
    assert decision.signals["keyword_match"] is False


@pytest.mark.asyncio
async def test_budget_proximity_signal() -> None:
    router = RouterService(Settings())

    decision = await router.choose_target_with_reason(
        "simple prompt",
        _request(prompt="simple prompt"),
        policy=TenantPolicy(soft_budget_usd=5.0),
    )

    assert "budget_proximity" in decision.signals
    assert decision.signals["budget_proximity"] is None


@pytest.mark.asyncio
async def test_model_constraint_signal() -> None:
    router = RouterService(Settings())

    decision = await router.choose_target_with_reason(
        "simple prompt",
        _request(prompt="simple prompt"),
        policy=TenantPolicy(allowed_premium_models=["gpt-4o-mini"]),
    )

    assert decision.signals["model_constraint"] is True
    assert decision.score > 0.0


@pytest.mark.asyncio
async def test_score_by_complexity_tier() -> None:
    router = RouterService(Settings())

    low = await router.choose_target_with_reason("a" * 120, _request(prompt="a" * 120))
    medium = await router.choose_target_with_reason("a" * 2400, _request(prompt="a" * 2400))
    high = await router.choose_target_with_reason("a" * 9000, _request(prompt="a" * 9000))

    assert low.signals["complexity_tier"] == "low"
    assert medium.signals["complexity_tier"] == "medium"
    assert high.signals["complexity_tier"] == "high"
    assert 0.0 <= low.score <= medium.score <= high.score <= 1.0
    assert low.target == "local"
    assert medium.target == "premium"
    assert high.target == "premium"


def test_route_signals_persisted_in_ledger() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "a" * 2400}],
                },
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    assert response.status_code == 200
    assert ledger.status_code == 200
    body = ledger.json()
    assert len(body) == 1
    assert body[0]["request_id"] == request_id
    assert body[0]["route_reason"] == "token_complexity"
    assert body[0]["route_signals"] == {
        "budget_proximity": None,
        "complexity_tier": "medium",
        "keyword_match": False,
        "model_constraint": False,
        "token_count": 600,
    }


def test_route_score_header() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={
                    "model": "nebula-auto",
                    "messages": [{"role": "user", "content": "a" * 2400}],
                },
            )

    assert response.status_code == 200
    assert response.headers["X-Nebula-Route-Target"] == "premium"
    assert response.headers["X-Nebula-Route-Reason"] == "token_complexity"
    assert response.headers["X-Nebula-Route-Score"] == "0.6000"
