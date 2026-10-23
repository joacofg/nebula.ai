"""Policy simulation re-decides learned-router traffic per tier from the stored probabilities.

The ledger keeps no prompt text, but a learned-router row keeps the two probabilities the
router computed for its prompt. Under a candidate quality target the same probabilities meet
another operating point, so the row can be re-decided exactly, per tier, without the prompt.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import DEFAULT_LEARNED_ROUTER_PATH, Settings
from nebula.models.governance import (
    ApiKeyRecord,
    CalibrationEvidenceSummary,
    PolicySimulationRequest,
    PolicySimulationResponse,
    TenantPolicy,
    TenantRecord,
    UsageLedgerRecord,
)
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionResult
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.learned_router import LearnedRouterModel, tier_for
from nebula.services.policy_service import PolicyService
from nebula.services.policy_simulation_service import PolicySimulationService
from nebula.services.router_service import RouterService
from tests.support import (
    FixedVectorEmbeddings,
    StubProvider,
    admin_headers,
    auth_headers,
    configured_app,
    usage,
    use_fake_cache,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = Path(DEFAULT_LEARNED_ROUTER_PATH)
MODEL = LearnedRouterModel.from_file(ARTIFACT)

LOCAL_MODEL = "qwen2.5:7b"
ECONOMY_MODEL = "anthropic/claude-haiku-4.5"
FRONTIER_MODEL = "openai/gpt-4.1"

# Two prompt embeddings for the real artifact. PROBE: p_local ≈ 0.648, p_economy ≈ 0.813
# (local at a 0.78 target, frontier at 0.95). ECONOMY_LEANING runs along the economy model's
# weights and against the local one's: p_local ≈ 0.154, p_economy ≈ 0.937 (economy at 0.9).
PROBE_VECTOR = [0.013 * ((i % 7) - 3) for i in range(MODEL.dimension)]
_WEIGHTS = json.loads(ARTIFACT.read_text(encoding="utf-8"))["models"]
ECONOMY_LEANING_VECTOR = [
    0.1 * (economy - local)
    for economy, local in zip(_WEIGHTS["economy"]["weights"], _WEIGHTS["local"]["weights"])
]


def _settings(economy_model: str | None = ECONOMY_MODEL) -> Settings:
    return Settings(
        local_model=LOCAL_MODEL, premium_model=FRONTIER_MODEL, economy_model=economy_model
    )


# --- The replay decides like the live router ------------------------------------------------


@pytest.mark.parametrize(
    ("vector", "target", "economy_model", "expected_tier"),
    [
        (PROBE_VECTOR, 0.78, ECONOMY_MODEL, "local"),
        (PROBE_VECTOR, 0.95, ECONOMY_MODEL, "frontier"),
        (PROBE_VECTOR, 1.0, ECONOMY_MODEL, "frontier"),
        (ECONOMY_LEANING_VECTOR, 0.9, ECONOMY_MODEL, "economy"),
        # No economy model configured: the premium provider serves the frontier model.
        (ECONOMY_LEANING_VECTOR, 0.9, None, "frontier"),
    ],
)
async def test_learned_replay_decides_like_the_live_router(
    vector: list[float], target: float, economy_model: str | None, expected_tier: str
) -> None:
    router = RouterService(_settings(economy_model), learned=MODEL)
    policy = TenantPolicy(routing_quality_target=target)
    live = await router.choose_target_with_reason(
        "hi",
        ChatCompletionRequest(model="nebula-auto", messages=[{"role": "user", "content": "hi"}]),
        policy=policy,
        prompt_embedding=vector,
    )

    replay = router.choose_target_for_learned_replay(
        live.signals["p_local"], live.signals["p_economy"], policy
    )

    assert replay is not None
    assert replay.signals["tier"] == expected_tier
    assert (replay.target, replay.reason, replay.model, replay.score) == (
        live.target,
        live.reason,
        live.model,
        live.score,
    )
    # Every learned signal matches; the live decision adds its heuristic breakdown.
    assert replay.signals.items() <= live.signals.items()
    assert set(replay.signals) == {
        "tier",
        "p_local",
        "p_economy",
        "quality_target",
        "operating_point",
        "learned_router",
        "economy_model",
    }


def test_learned_replay_needs_a_loaded_learned_router() -> None:
    router = RouterService(_settings(), learned=None)

    assert router.choose_target_for_learned_replay(0.62, 0.91, TenantPolicy()) is None


# --- The ledger keeps what the router computed ---------------------------------------------


def _mount_providers(app) -> None:
    container = app.state.container
    for attribute, name, model in (
        ("local_provider", "ollama", LOCAL_MODEL),
        ("premium_provider", "openai-compatible", FRONTIER_MODEL),
    ):
        provider = StubProvider(
            name,
            completion_result=CompletionResult(
                content="answer", model=model, provider=name, usage=usage(100, 50)
            ),
        )
        setattr(container, attribute, provider)
        setattr(container.provider_registry, attribute, provider)


@pytest.mark.parametrize("economy_model", [ECONOMY_MODEL, None])
def test_learned_signals_are_stored_unrounded(economy_model: str | None) -> None:
    # Any 768-dimension vector gives probabilities with more than four decimals.
    vector = [0.013 * ((i % 7) - 3) for i in range(MODEL.dimension)]
    expected_p_local, expected_p_economy = MODEL.probabilities(vector)
    assert round(expected_p_local, 4) != expected_p_local

    env = {
        "NEBULA_LOCAL_MODEL": LOCAL_MODEL,
        "NEBULA_PREMIUM_MODEL": FRONTIER_MODEL,
        "NEBULA_LEARNED_ROUTER_ENABLED": "true",
        "NEBULA_LEARNED_ROUTER_PATH": str(ARTIFACT),
    }
    if economy_model is not None:
        env["NEBULA_ECONOMY_MODEL"] = economy_model
    with configured_app(**env) as app:
        with TestClient(app) as client:
            _mount_providers(app)
            use_fake_cache(app.state.container)
            app.state.container.chat_service.embeddings_service = FixedVectorEmbeddings(vector)
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={"model": "nebula-auto", "messages": [{"role": "user", "content": "hi"}]},
            )
            [row] = client.get(
                f"/v1/admin/usage/ledger?request_id={response.headers['X-Request-ID']}",
                headers=admin_headers(),
            ).json()

    assert response.status_code == 200
    assert response.headers["X-Nebula-Route-Reason"] == "learned_router"
    signals = row["route_signals"]
    assert signals["p_local"] == expected_p_local
    assert signals["p_economy"] == expected_p_economy
    assert signals["economy_model"] == economy_model
    assert signals["learned_router"] == "v1"
    # The score and its header keep four decimals.
    assert response.headers["X-Nebula-Route-Score"] == f"{1 - expected_p_local:.4f}"


# --- The simulation re-decides learned rows per tier ----------------------------------------

PRICING = PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)
TOKEN_COUNT = 400
COMPLETION_TOKENS = 200


def _cost(model: str) -> float:
    # The replay prices the row's stored token counts with the current pricing rules.
    cost = PRICING.estimate_cost(model, usage(TOKEN_COUNT, COMPLETION_TOKENS))
    assert cost is not None
    return cost


class _LedgerStore:
    """The ledger reads the simulation makes; it fails on any write."""

    def __init__(self, records: list[UsageLedgerRecord], *, spend_total: float = 0.0) -> None:
        self.records = records
        self.spend_total = spend_total

    def list_usage_records(self, *, tenant_id, from_timestamp=None, to_timestamp=None, limit=100):
        rows = [r for r in self.records if r.tenant_id == tenant_id]
        return sorted(rows, key=lambda r: r.timestamp, reverse=True)[:limit]

    def summarize_calibration_evidence(self, *, tenant_id, **_window) -> CalibrationEvidenceSummary:
        return CalibrationEvidenceSummary(
            tenant_id=tenant_id,
            state="thin",
            state_reason="No eligible calibrated routing evidence is available yet.",
            generated_at=NOW,
            eligible_request_count=0,
            sufficient_request_count=0,
            excluded_request_count=0,
            gated_request_count=0,
            degraded_request_count=0,
        )

    def tenant_spend_total(self, tenant_id: str, *, before_timestamp=None) -> float:
        return self.spend_total

    def record_usage(self, record):  # pragma: no cover - a simulation never writes
        raise AssertionError("the simulation wrote a ledger row")


def _heuristic_signals() -> dict:
    # What the live breakdown stores next to the learned signals; on its own it routes local.
    return {
        "token_count": TOKEN_COUNT,
        "complexity_tier": "low",
        "keyword_match": False,
        "model_constraint": False,
        "route_mode": "calibrated",
        "calibrated_routing": True,
        "degraded_routing": False,
        "score_components": {"total_score": 0.8},
        "replay": False,
    }


def _learned_signals(p_local, p_economy, *, tier: str = "frontier", label: str = "v1") -> dict:
    return {
        **_heuristic_signals(),
        "tier": tier,
        "p_local": p_local,
        "p_economy": p_economy,
        "quality_target": 0.95,
        "operating_point": {"tau_local": 0.82, "tau_economy": 0.92, "quality": 0.9568},
        "learned_router": label,
        "economy_model": ECONOMY_MODEL,
    }


def _row(
    request_id: str,
    *,
    seconds: int = 0,
    route_signals: dict | None,
    final_route_target: str = "premium",
    response_model: str | None = FRONTIER_MODEL,
    requested_model: str = "nebula-auto",
    route_reason: str = "learned_router",
    terminal_status: str = "completed",
    estimated_cost: float | None = None,
    fallback_used: bool = False,
) -> UsageLedgerRecord:
    if estimated_cost is None:
        estimated_cost = _cost(response_model) if final_route_target == "premium" else 0.0
    return UsageLedgerRecord(
        request_id=request_id,
        tenant_id="default",
        requested_model=requested_model,
        final_route_target=final_route_target,
        final_provider="ollama" if final_route_target == "local" else "openai-compatible",
        fallback_used=fallback_used,
        cache_hit=final_route_target == "cache",
        response_model=response_model,
        prompt_tokens=TOKEN_COUNT,
        completion_tokens=COMPLETION_TOKENS,
        total_tokens=TOKEN_COUNT + COMPLETION_TOKENS,
        estimated_cost=estimated_cost,
        timestamp=NOW + timedelta(seconds=seconds),
        terminal_status=terminal_status,  # type: ignore[arg-type]
        route_reason=route_reason,
        policy_outcome="default",
        route_signals=route_signals,
    )


def _tenant_context(policy: TenantPolicy | None = None) -> AuthenticatedTenantContext:
    return AuthenticatedTenantContext(
        tenant=TenantRecord(id="default", name="Default", created_at=NOW, updated_at=NOW),
        api_key=ApiKeyRecord(
            id="key-1",
            name="default",
            key_prefix="nebula-",
            tenant_id="default",
            allowed_tenant_ids=["default"],
            created_at=NOW,
            updated_at=NOW,
        ),
        policy=policy or TenantPolicy(),
    )


async def _simulate(
    records: list[UsageLedgerRecord],
    candidate: TenantPolicy,
    *,
    economy_model: str | None = ECONOMY_MODEL,
    learned: LearnedRouterModel | None = MODEL,
    spend_total: float = 0.0,
) -> PolicySimulationResponse:
    settings = _settings(economy_model)
    store = _LedgerStore(records, spend_total=spend_total)
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings, learned=learned),
        policy_service=PolicyService(settings, store, PRICING),
    )
    return await service.simulate(
        tenant_context=_tenant_context(),
        payload=PolicySimulationRequest(
            candidate_policy=candidate, limit=200, changed_sample_limit=50
        ),
    )


def _counts(local: int = 0, economy: int = 0, frontier: int = 0) -> dict[str, int]:
    return {"local": local, "economy": economy, "frontier": frontier}


@pytest.mark.parametrize(
    ("target", "expected_tier", "expected_cost"),
    [
        (0.78, "local", 0.0),
        (0.9, "economy", _cost(ECONOMY_MODEL)),
        # The target the row was decided under: the replay reproduces it, nothing changes.
        (0.95, "frontier", _cost(FRONTIER_MODEL)),
    ],
)
async def test_learned_row_is_redecided_per_tier_under_the_candidate_target(
    target: float, expected_tier: str, expected_cost: float
) -> None:
    assert tier_for(0.62, 0.91, MODEL.operating_point(target)) == expected_tier
    row = _row("req-learned", route_signals=_learned_signals(0.62, 0.91))

    response = await _simulate([row], TenantPolicy(routing_quality_target=target))

    summary = response.summary
    assert summary.learned_router_rows == 1
    assert summary.heuristic_rows == 0
    assert summary.baseline_tier_counts == _counts(frontier=1)
    assert summary.simulated_tier_counts == _counts(**{expected_tier: 1})
    assert summary.simulated_premium_cost == pytest.approx(expected_cost)
    assert "heuristic_fallback_rows" not in response.approximation_note_codes
    if expected_tier == "frontier":
        assert response.changed_requests == []
        return
    [changed] = response.changed_requests
    assert changed.decision_source == "learned_router"
    assert changed.baseline_tier == "frontier"
    assert changed.simulated_tier == expected_tier
    assert changed.simulated_route_target == ("local" if expected_tier == "local" else "premium")
    assert changed.simulated_route_reason == "learned_router"
    assert changed.simulated_estimated_cost == pytest.approx(expected_cost)


async def test_a_learned_redecision_reports_the_routing_parity_of_the_live_router() -> None:
    row = _row("req-learned", route_signals=_learned_signals(0.62, 0.91))

    response = await _simulate([row], TenantPolicy(routing_quality_target=0.9))

    [changed] = response.changed_requests
    # Like a live learned decision: the heuristic breakdown rides along (here replayed from
    # complete stored signals) and the score is 1 - p_local, the X-Nebula-Route-Score it sent.
    assert (changed.baseline_route_mode, changed.simulated_route_mode) == ("calibrated",) * 2
    assert changed.simulated_calibrated_routing is True
    assert changed.simulated_degraded_routing is False
    assert changed.baseline_route_score == changed.simulated_route_score == 0.38


async def test_an_economy_pick_without_an_economy_model_is_simulated_as_frontier() -> None:
    # The 0.9 target picks economy for these probabilities; no economy model is configured.
    assert tier_for(0.62, 0.91, MODEL.operating_point(0.9)) == "economy"
    row = _row(
        "req-learned",
        route_signals=_learned_signals(0.62, 0.91),
        # A recorded cost no estimate reproduces, so the row shows up among the changed ones.
        estimated_cost=0.05,
    )

    response = await _simulate([row], TenantPolicy(routing_quality_target=0.9), economy_model=None)

    [changed] = response.changed_requests
    assert changed.decision_source == "learned_router"
    assert changed.simulated_tier == "frontier"
    assert changed.simulated_estimated_cost == pytest.approx(_cost(FRONTIER_MODEL))
    assert response.summary.simulated_tier_counts == _counts(frontier=1)


def _strict_row(request_id: str, **overrides) -> UsageLedgerRecord:
    # Strict evidence minimization drops every route signal before the row is stored.
    return _row(request_id, route_signals=None, **overrides).model_copy(
        update={"metadata_minimization_level": "strict", "metadata_fields_suppressed": ["route_signals"]}
    )


@pytest.mark.parametrize(
    ("row", "candidate", "learned", "expected_reason"),
    [
        pytest.param(
            _row("req-heuristic", route_signals=_heuristic_signals(), route_reason="token_complexity"),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="no-probabilities",
        ),
        pytest.param(
            _row("req-other-artifact", route_signals=_learned_signals(0.62, 0.91, label="v0")),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="another-artifact",
        ),
        pytest.param(
            _row("req-no-p-local", route_signals=_learned_signals(None, 0.91)),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="p-local-not-a-number",
        ),
        pytest.param(
            _row("req-no-p-economy", route_signals=_learned_signals(0.62, True)),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="p-economy-not-a-number",
        ),
        pytest.param(
            # Outside [0, 1] a stored probability is corrupt: nothing to re-decide from.
            _row("req-corrupt", route_signals=_learned_signals(1.5, 0.91)),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="p-local-out-of-range",
        ),
        pytest.param(
            _row("req-corrupt-economy", route_signals=_learned_signals(0.62, -0.01)),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="p-economy-out-of-range",
        ),
        pytest.param(
            _strict_row("req-strict"),
            TenantPolicy(),
            MODEL,
            "token_complexity",
            id="strict-minimization",
        ),
        pytest.param(
            _row(
                "req-explicit",
                route_signals=_learned_signals(0.62, 0.91),
                requested_model=FRONTIER_MODEL,
            ),
            TenantPolicy(),
            MODEL,
            "explicit_premium_model",
            id="explicit-model",
        ),
        pytest.param(
            _row("req-learned", route_signals=_learned_signals(0.62, 0.91)),
            TenantPolicy(calibrated_routing_enabled=False),
            MODEL,
            "calibrated_routing_disabled",
            id="candidate-turns-routing-off",
        ),
        pytest.param(
            _row("req-learned", route_signals=_learned_signals(0.62, 0.91)),
            TenantPolicy(),
            None,
            "token_complexity",
            id="no-learned-router-loaded",
        ),
    ],
)
async def test_rows_without_learned_signals_use_the_heuristic(
    row: UsageLedgerRecord,
    candidate: TenantPolicy,
    learned: LearnedRouterModel | None,
    expected_reason: str,
) -> None:
    # A recorded cost no estimate reproduces, so every row shows up among the changed ones.
    row = row.model_copy(update={"estimated_cost": 0.05})

    response = await _simulate([row], candidate, learned=learned)

    assert response.summary.heuristic_rows == 1
    assert response.summary.learned_router_rows == 0
    [changed] = response.changed_requests
    assert changed.decision_source == "heuristic"
    assert changed.simulated_route_reason == expected_reason
    assert "heuristic_fallback_rows" in response.approximation_note_codes
    assert len(response.approximation_note_codes) == len(response.approximation_notes)


def _cache_row(request_id: str, *, seconds: int = 0) -> UsageLedgerRecord:
    # A cache hit keeps the router's decision in its signals; at 0.95 these probabilities pick
    # frontier, so re-deciding the row would turn it into a premium request.
    return _row(
        request_id,
        seconds=seconds,
        route_signals=_learned_signals(0.62, 0.91, tier="frontier"),
        final_route_target="cache",
        response_model="nebula-cache",
        terminal_status="cache_hit",
        route_reason="cache",
    )


async def test_a_cache_row_stays_cache_while_the_candidate_keeps_the_cache() -> None:
    rows = [
        _cache_row("req-cache", seconds=0),
        _row("req-learned", seconds=1, route_signals=_learned_signals(0.62, 0.91)),
    ]

    response = await _simulate(rows, TenantPolicy(routing_quality_target=0.95))

    summary = response.summary
    assert response.changed_requests == []
    assert summary.changed_routes == 0
    assert summary.evaluated_rows == 2
    # Neither router re-decides a held cache row: it has its own bucket.
    assert (summary.learned_router_rows, summary.heuristic_rows, summary.cache_rows) == (1, 0, 1)
    assert summary.learned_router_rows + summary.heuristic_rows + summary.cache_rows == summary.evaluated_rows
    # No tier on either side, and no cost: the cache answers it again.
    assert summary.baseline_tier_counts == summary.simulated_tier_counts == _counts(frontier=1)
    assert summary.simulated_premium_cost == pytest.approx(summary.baseline_premium_cost)
    # Holding the row is an assumption, and the notes say so.
    assert "cache_rows_held" in response.approximation_note_codes
    assert len(response.approximation_note_codes) == len(response.approximation_notes)


async def test_a_window_without_held_cache_rows_has_no_cache_note() -> None:
    response = await _simulate(
        [_row("req-learned", route_signals=_learned_signals(0.62, 0.91))],
        TenantPolicy(routing_quality_target=0.95),
    )

    assert response.summary.cache_rows == 0
    assert "cache_rows_held" not in response.approximation_note_codes


async def test_a_cache_row_is_redecided_when_the_candidate_turns_the_cache_off() -> None:
    response = await _simulate(
        [_cache_row("req-cache")],
        TenantPolicy(routing_quality_target=0.95, semantic_cache_enabled=False),
    )

    summary = response.summary
    [changed] = response.changed_requests
    assert changed.request_id == "req-cache"
    assert changed.decision_source == "learned_router"
    assert (changed.baseline_route_target, changed.simulated_route_target) == ("cache", "premium")
    assert (changed.baseline_tier, changed.simulated_tier) == (None, "frontier")
    assert summary.changed_routes == 1
    assert (summary.learned_router_rows, summary.heuristic_rows, summary.cache_rows) == (1, 0, 0)
    assert summary.simulated_tier_counts == _counts(frontier=1)
    assert "cache_rows_held" not in response.approximation_note_codes


async def test_embeddings_rows_are_not_replayed_as_chat() -> None:
    # An embeddings call has no chat route to re-decide; like a rate-limited row, it is left out
    # of the window instead of being replayed as a chat request.
    embeddings = _row(
        "req-embeddings",
        seconds=1,
        route_signals=None,
        final_route_target="embeddings",
        requested_model="nomic-embed-text",
        response_model="nomic-embed-text",
        route_reason="embeddings_request",
        estimated_cost=0.0,
    ).model_copy(update={"message_type": "embeddings"})
    rows = [_row("req-learned", seconds=0, route_signals=_learned_signals(0.62, 0.91)), embeddings]

    response = await _simulate(rows, TenantPolicy(routing_quality_target=0.95))

    summary = response.summary
    assert response.window.returned_rows == 1
    assert summary.evaluated_rows == 1
    assert (summary.learned_router_rows, summary.heuristic_rows, summary.cache_rows) == (1, 0, 0)
    assert summary.learned_router_rows + summary.heuristic_rows + summary.cache_rows == summary.evaluated_rows
    assert [item.request_id for item in response.changed_requests] == []
    assert "heuristic_fallback_rows" not in response.approximation_note_codes


async def test_mixed_window_counts_add_up() -> None:
    keyword_signals = {**_heuristic_signals(), "keyword_match": True}
    rows = [
        # p_economy clears the 0.9 target's tau_economy (0.90): economy.
        _row("req-learned", seconds=0, route_signals=_learned_signals(0.6234567891, 0.9123456789)),
        # Stored with four decimals before this change; 0.8999 misses tau_economy: frontier.
        _row("req-rounded", seconds=1, route_signals=_learned_signals(0.6235, 0.8999)),
        # A keyword sends the heuristic to the frontier model.
        _row(
            "req-heuristic",
            seconds=2,
            route_signals=keyword_signals,
            final_route_target="local",
            response_model=LOCAL_MODEL,
            route_reason="token_complexity",
        ),
        _strict_row("req-strict", seconds=3),
        # Served from the cache, and the candidate keeps the cache on: it stays a cache hit.
        _row(
            "req-cache",
            seconds=4,
            route_signals=_learned_signals(0.8, 0.95, tier="local"),
            final_route_target="cache",
        ),
        _row(
            "req-denied",
            seconds=5,
            route_signals=None,
            final_route_target="denied",
            response_model=None,
            route_reason="token_complexity",
            terminal_status="policy_denied",
        ),
        # Decided local, the local model failed, the economy model answered.
        _row(
            "req-fallback",
            seconds=6,
            route_signals=_learned_signals(0.8, 0.95, tier="local"),
            response_model=ECONOMY_MODEL,
            fallback_used=True,
        ),
    ]
    # Only the economy model is allowed: a frontier pick is denied, learned or heuristic.
    candidate = TenantPolicy(routing_quality_target=0.9, allowed_premium_models=[ECONOMY_MODEL])

    response = await _simulate(rows, candidate)

    summary = response.summary
    changed = {item.request_id: item for item in response.changed_requests}
    assert {request_id: item.decision_source for request_id, item in changed.items()} == {
        "req-learned": "learned_router",
        "req-rounded": "learned_router",
        "req-heuristic": "heuristic",
        "req-strict": "heuristic",
        "req-denied": "heuristic",
        "req-fallback": "learned_router",
    }
    assert {
        request_id: (item.baseline_tier, item.simulated_tier) for request_id, item in changed.items()
    } == {
        "req-learned": ("frontier", "economy"),
        "req-rounded": ("frontier", None),
        "req-heuristic": ("local", None),
        "req-strict": ("frontier", "local"),
        "req-denied": (None, "local"),
        "req-fallback": ("economy", "local"),
    }
    assert summary.evaluated_rows == 7
    assert (summary.learned_router_rows, summary.heuristic_rows, summary.cache_rows) == (3, 3, 1)
    assert (
        summary.learned_router_rows + summary.heuristic_rows + summary.cache_rows
        == summary.evaluated_rows
    )
    assert summary.baseline_tier_counts == _counts(local=1, economy=1, frontier=3)
    assert summary.simulated_tier_counts == _counts(local=3, economy=1)
    simulated_denied = [i for i in changed.values() if i.simulated_route_target == "denied"]
    assert sum(summary.simulated_tier_counts.values()) == summary.evaluated_rows - len(
        simulated_denied
    ) - summary.cache_rows
    assert summary.simulated_premium_cost == pytest.approx(_cost(ECONOMY_MODEL))


async def test_a_tier_change_alone_is_a_changed_request() -> None:
    # Neither model has a price in the catalog: frontier → economy changes no cost, no route.
    settings = Settings(
        local_model=LOCAL_MODEL, premium_model="acme/frontier", economy_model="acme/economy"
    )
    row = _row(
        "req-learned",
        route_signals=_learned_signals(0.62, 0.91),
        response_model="acme/frontier",
        estimated_cost=0.0,
    )
    store = _LedgerStore([row])
    service = PolicySimulationService(
        governance_store=store,
        router_service=RouterService(settings, learned=MODEL),
        policy_service=PolicyService(settings, store, PRICING),
    )

    response = await service.simulate(
        tenant_context=_tenant_context(),
        payload=PolicySimulationRequest(candidate_policy=TenantPolicy(routing_quality_target=0.9)),
    )

    [changed] = response.changed_requests
    assert (changed.baseline_route_target, changed.simulated_route_target) == ("premium",) * 2
    assert changed.baseline_estimated_cost == changed.simulated_estimated_cost == 0.0
    assert (changed.baseline_tier, changed.simulated_tier) == ("frontier", "economy")


HARD_BUDGET = {"hard_budget_limit_usd": 1.0}


@pytest.mark.parametrize(
    ("candidate", "spend_total", "expected", "expected_source"),
    [
        pytest.param(
            {"allowed_premium_models": [FRONTIER_MODEL]},
            0.0,
            ("premium", "learned_router", "frontier"),
            "learned_router",
            id="economy-not-allowed-escalates",
        ),
        pytest.param(
            {"allowed_premium_models": ["other/model"]},
            0.0,
            ("denied", "learned_router", None),
            "learned_router",
            id="no-tier-allowed",
        ),
        pytest.param(
            {"routing_mode_default": "premium_only"},
            0.0,
            ("premium", "policy_premium_only", "frontier"),
            "heuristic",
            id="premium-only",
        ),
        pytest.param(
            {"routing_mode_default": "local_only"},
            0.0,
            ("local", "policy_local_only", "local"),
            "heuristic",
            id="local-only",
        ),
        pytest.param(
            {**HARD_BUDGET, "hard_budget_enforcement": "downgrade"},
            10.0,
            ("local", "hard_budget_downgrade", "local"),
            "learned_router",
            id="hard-budget-downgrade",
        ),
        pytest.param(
            {**HARD_BUDGET, "hard_budget_enforcement": "deny"},
            10.0,
            ("denied", "learned_router", None),
            "learned_router",
            id="hard-budget-deny",
        ),
        pytest.param(
            {"max_premium_cost_per_request": 0.000001},
            0.0,
            ("denied", "learned_router", None),
            "learned_router",
            id="per-request-cap",
        ),
    ],
)
async def test_candidate_guardrails_apply_to_learned_rows(
    candidate: dict,
    spend_total: float,
    expected: tuple[str, str, str | None],
    expected_source: str,
) -> None:
    # The row the live router writes for this prompt: economy at the 0.9 target.
    p_local, p_economy = MODEL.probabilities(ECONOMY_LEANING_VECTOR)
    policy = TenantPolicy(routing_quality_target=0.9, **candidate)
    settings = _settings()
    store = _LedgerStore([], spend_total=spend_total)
    live = await PolicyService(settings, store, PRICING).evaluate(
        request=ChatCompletionRequest(
            model="nebula-auto", messages=[{"role": "user", "content": "hi"}]
        ),
        tenant_context=_tenant_context(policy),
        router_service=RouterService(settings, learned=MODEL),
        prompt="hi",
        prompt_embedding=ECONOMY_LEANING_VECTOR,
    )
    row = _row(
        "req-learned",
        route_signals=_learned_signals(p_local, p_economy, tier="economy"),
        response_model=ECONOMY_MODEL,
        # A recorded cost no estimate reproduces, so the row shows up among the changed ones.
        estimated_cost=0.05,
    )

    response = await _simulate([row], policy, spend_total=spend_total)

    [changed] = response.changed_requests
    expected_target, expected_reason, expected_tier = expected
    live_target = "denied" if live.denied else live.route_decision.target
    assert (live_target, live.route_decision.reason) == (expected_target, expected_reason)
    assert (
        changed.simulated_route_target,
        changed.simulated_route_reason,
        changed.simulated_tier,
    ) == expected
    assert changed.decision_source == expected_source
    # A denied request costs nothing, whichever guardrail denied it.
    expected_cost = _cost(FRONTIER_MODEL) if expected_tier == "frontier" else 0.0
    assert changed.simulated_estimated_cost == pytest.approx(expected_cost)
    assert response.summary.simulated_premium_cost == pytest.approx(expected_cost)


CAP_DENIAL = "denied=Request exceeds the tenant premium spend guardrail."


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(
            # Frontier at the 0.95 target, as when it was recorded.
            _row(
                "req-learned-denied",
                route_signals=_learned_signals(0.62, 0.91),
                final_route_target="denied",
                response_model=None,
                terminal_status="policy_denied",
            ),
            id="learned-row",
        ),
        pytest.param(
            # A live denial stores no route signals; an explicit model keeps it premium.
            _row(
                "req-heuristic-denied",
                route_signals=None,
                requested_model=FRONTIER_MODEL,
                final_route_target="denied",
                response_model=None,
                route_reason="explicit_premium_model",
                terminal_status="policy_denied",
            ),
            id="heuristic-row",
        ),
    ],
)
async def test_a_row_denied_in_the_baseline_and_the_candidate_is_unchanged(
    row: UsageLedgerRecord,
) -> None:
    row = row.model_copy(update={"policy_outcome": CAP_DENIAL})
    candidate = TenantPolicy(max_premium_cost_per_request=0.000001)

    response = await _simulate([row], candidate)

    assert response.changed_requests == []
    assert response.summary.newly_denied == 0
    assert response.summary.simulated_premium_cost == 0.0
    assert response.summary.premium_cost_delta == 0.0
