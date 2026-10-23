from __future__ import annotations

import math
from dataclasses import dataclass

from nebula.models.governance import (
    CalibrationEvidenceSummary,
    PolicySimulationChangedRequest,
    PolicySimulationOutcomeCounts,
    PolicySimulationRequest,
    PolicySimulationResponse,
    PolicySimulationWindow,
    SimulationDecisionSource,
    TenantPolicy,
    UsageLedgerRecord,
)
from nebula.models.openai import ChatCompletionRequest
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyEvaluation, PolicyService
from nebula.services.router_service import ReplayRouteContext, RouteDecision, RouterService

TIERS = ("local", "economy", "frontier")

# (code, text): clients word the notes by code; the text stays for API clients that show it.
APPROXIMATION_NOTES = (
    (
        "ledger_metadata_replay",
        "Replay uses persisted ledger request metadata and route signals instead of raw prompt text.",
    ),
    (
        "token_count_approximation",
        "When route signals are incomplete, prompt complexity is approximated from stored token counts.",
    ),
    (
        "pricing_estimate",
        "Projected premium cost is estimated with current pricing rules and no provider call is executed.",
    ),
)
HEURISTIC_FALLBACK_NOTE = (
    "heuristic_fallback_rows",
    "Rows without stored learned-router probabilities for the loaded artifact, or that the "
    "candidate policy keeps off the learned router, are replayed with the token-complexity "
    "heuristic.",
)


@dataclass(slots=True, frozen=True)
class SimulationReplayInput:
    record: UsageLedgerRecord
    request: ChatCompletionRequest
    baseline_cost: float
    replay_context: ReplayRouteContext


class PolicySimulationService:
    """Replay recent ledger rows against a candidate policy without mutating runtime state.

    The simulation is signal-driven: prompt text is unavailable in usage ledger rows, so replay
    reconstructs a narrow ChatCompletionRequest from persisted request metadata and router signals.
    A row the learned router decided keeps its two probabilities, so the learned router re-decides
    it exactly under the candidate quality target. Every other row is replayed with the heuristic:
    token-count and keyword-match route signals from the original decision are reused when present;
    otherwise a synthetic prompt based on token volume is used to approximate complexity routing.
    A row the cache answered stays a cache hit while the candidate keeps the cache on (the replay
    cannot know the cache would miss); with the cache off it is re-decided like any other row.
    No provider execution, policy writes, or usage writes occur during simulation.
    """

    def __init__(
        self,
        *,
        governance_store: GovernanceStore,
        router_service: RouterService,
        policy_service: PolicyService,
    ) -> None:
        self.governance_store = governance_store
        self.router_service = router_service
        self.policy_service = policy_service

    async def simulate(
        self,
        *,
        tenant_context: AuthenticatedTenantContext,
        payload: PolicySimulationRequest,
    ) -> PolicySimulationResponse:
        records = self.governance_store.list_usage_records(
            tenant_id=tenant_context.tenant.id,
            from_timestamp=payload.from_timestamp,
            to_timestamp=payload.to_timestamp,
            limit=payload.limit,
        )
        # Store returns newest first; replay oldest-first for deterministic windows and sampling.
        # Rate-limited rows never ran, so replaying them would invent traffic.
        records = [r for r in reversed(records) if r.terminal_status != "rate_limited"]

        replay_inputs = [self._build_replay_input(record) for record in records]
        calibration_summary = self.governance_store.summarize_calibration_evidence(
            tenant_id=tenant_context.tenant.id,
            from_timestamp=payload.from_timestamp,
            to_timestamp=payload.to_timestamp,
            limit=payload.limit,
        )
        changed: list[PolicySimulationChangedRequest] = []
        evaluated_count = 0
        changed_routes = 0
        newly_denied = 0
        baseline_premium_cost_total = 0.0
        simulated_premium_cost_total = 0.0
        baseline_tier_counts = dict.fromkeys(TIERS, 0)
        simulated_tier_counts = dict.fromkeys(TIERS, 0)
        decision_source_counts: dict[SimulationDecisionSource, int] = {
            "learned_router": 0,
            "heuristic": 0,
        }
        cache_rows = 0

        simulation_context = AuthenticatedTenantContext(
            tenant=tenant_context.tenant,
            api_key=tenant_context.api_key,
            policy=payload.candidate_policy,
        )

        for replay_input in replay_inputs:
            evaluated_count += 1
            if self._held_by_cache(replay_input.record, payload.candidate_policy):
                # The replay cannot tell whether the cache would answer again, and the live
                # gateway serves a stored answer before routing: the row stays a cache hit, with
                # no tier and no cost on either side, and is not a change.
                cache_rows += 1
                continue
            baseline_target = self._baseline_target(replay_input.record)
            baseline_denied = replay_input.record.terminal_status == "policy_denied"
            baseline_cost = replay_input.baseline_cost
            baseline_premium_cost_total += baseline_cost

            learned_decision = self._learned_replay_decision(
                replay_input, payload.candidate_policy, calibration_summary
            )
            decision_source: SimulationDecisionSource
            if learned_decision is not None:
                decision_source = "learned_router"
                evaluation = self.policy_service.evaluate_decision(
                    request=replay_input.request,
                    tenant_context=simulation_context,
                    route_decision=learned_decision,
                    before_timestamp=replay_input.record.timestamp,
                    evidence_summary=calibration_summary,
                )
            else:
                decision_source = "heuristic"
                evaluation = await self.policy_service.evaluate(
                    request=replay_input.request,
                    tenant_context=simulation_context,
                    router_service=self.router_service,
                    replay_context=replay_input.replay_context,
                    before_timestamp=replay_input.record.timestamp,
                    evidence_summary_override=calibration_summary,
                )
            decision_source_counts[decision_source] += 1

            simulated_target = self._simulation_target(evaluation)
            simulated_denied = evaluation.denied
            simulated_cost = self._simulated_cost(evaluation)
            simulated_premium_cost_total += simulated_cost
            baseline_tier = self._baseline_tier(replay_input.record)
            simulated_tier = self._simulated_tier(evaluation)
            if baseline_tier is not None:
                baseline_tier_counts[baseline_tier] += 1
            if simulated_tier is not None:
                simulated_tier_counts[simulated_tier] += 1

            if baseline_target != simulated_target:
                changed_routes += 1
            if not baseline_denied and simulated_denied:
                newly_denied += 1

            if baseline_tier != simulated_tier or self._record_changed(
                replay_input.record, evaluation, simulated_target
            ):
                baseline_parity = self._route_parity_from_record(replay_input.record)
                simulated_parity = self._route_parity_from_decision(evaluation.route_decision)
                changed.append(
                    PolicySimulationChangedRequest(
                        request_id=replay_input.record.request_id,
                        timestamp=replay_input.record.timestamp,
                        requested_model=replay_input.record.requested_model,
                        baseline_route_target=baseline_target,
                        simulated_route_target=simulated_target,
                        baseline_terminal_status=replay_input.record.terminal_status,
                        simulated_terminal_status=(
                            "policy_denied" if simulated_denied else replay_input.record.terminal_status
                        ),
                        baseline_policy_outcome=replay_input.record.policy_outcome,
                        simulated_policy_outcome=evaluation.policy_outcome,
                        baseline_route_reason=replay_input.record.route_reason,
                        simulated_route_reason=evaluation.route_decision.reason,
                        baseline_route_mode=baseline_parity["route_mode"],
                        simulated_route_mode=simulated_parity["route_mode"],
                        baseline_calibrated_routing=baseline_parity["calibrated_routing"],
                        simulated_calibrated_routing=simulated_parity["calibrated_routing"],
                        baseline_degraded_routing=baseline_parity["degraded_routing"],
                        simulated_degraded_routing=simulated_parity["degraded_routing"],
                        baseline_route_score=baseline_parity["route_score"],
                        simulated_route_score=simulated_parity["route_score"],
                        baseline_estimated_cost=baseline_cost,
                        simulated_estimated_cost=simulated_cost,
                        baseline_tier=baseline_tier,
                        simulated_tier=simulated_tier,
                        decision_source=decision_source,
                    )
                )

        sampled_changed = changed[: payload.changed_sample_limit]
        window = self._build_window(payload, records)
        notes = list(APPROXIMATION_NOTES)
        if decision_source_counts["heuristic"] > 0:
            notes.append(HEURISTIC_FALLBACK_NOTE)
        return PolicySimulationResponse(
            tenant_id=tenant_context.tenant.id,
            candidate_policy=payload.candidate_policy,
            approximation_notes=[text for _, text in notes],
            approximation_note_codes=[code for code, _ in notes],
            window=window,
            summary=PolicySimulationOutcomeCounts(
                evaluated_rows=evaluated_count,
                changed_routes=changed_routes,
                newly_denied=newly_denied,
                baseline_premium_cost=round(baseline_premium_cost_total, 8),
                simulated_premium_cost=round(simulated_premium_cost_total, 8),
                premium_cost_delta=round(simulated_premium_cost_total - baseline_premium_cost_total, 8),
                baseline_tier_counts=baseline_tier_counts,
                simulated_tier_counts=simulated_tier_counts,
                learned_router_rows=decision_source_counts["learned_router"],
                heuristic_rows=decision_source_counts["heuristic"],
                cache_rows=cache_rows,
            ),
            calibration_summary=calibration_summary,
            changed_requests=sampled_changed,
        )

    def _learned_replay_decision(
        self,
        replay_input: SimulationReplayInput,
        policy: TenantPolicy,
        evidence_summary: CalibrationEvidenceSummary,
    ) -> RouteDecision | None:
        """The learned router's re-decision of the row under `policy`, when it can make one.

        Only a row the loaded artifact decided carries probabilities that artifact's operating
        points apply to, and only an auto-routed `nebula-auto` request under a candidate that
        keeps the router on would reach the learned router live. Every other row: None.
        """
        record = replay_input.record
        learned = self.router_service.learned
        if (
            learned is None
            or not policy.calibrated_routing_enabled
            or policy.routing_mode_default != "auto"
            or record.requested_model != self.router_service.settings.default_model
        ):
            return None
        route_signals = record.route_signals or {}
        p_local = route_signals.get("p_local")
        p_economy = route_signals.get("p_economy")
        if (
            route_signals.get("learned_router") != learned.version
            or not self._is_probability(p_local)
            or not self._is_probability(p_economy)
        ):
            return None
        return self.router_service.choose_target_for_learned_replay(
            float(p_local),
            float(p_economy),
            policy,
            request=replay_input.request,
            replay_context=replay_input.replay_context,
            evidence_summary=evidence_summary,
        )

    @staticmethod
    def _held_by_cache(record: UsageLedgerRecord, policy: TenantPolicy) -> bool:
        """A row the cache answered stays a cache hit unless the candidate turns the cache off."""
        return record.final_route_target == "cache" and policy.semantic_cache_enabled

    @staticmethod
    def _is_probability(value: object) -> bool:
        # Rows recorded before the probabilities were stored unrounded hold four decimals:
        # still numbers, still re-decided. Outside [0, 1] the stored value is corrupt.
        return (
            isinstance(value, int | float)
            and not isinstance(value, bool)
            and math.isfinite(value)
            and 0.0 <= value <= 1.0
        )

    def _build_replay_input(self, record: UsageLedgerRecord) -> SimulationReplayInput:
        metadata = {"simulation": {"request_id": record.request_id}}
        route_signals = record.route_signals or {}
        replay_context = ReplayRouteContext(
            token_count=route_signals.get("token_count"),
            keyword_match=route_signals.get("keyword_match"),
            complexity_tier=route_signals.get("complexity_tier"),
        )
        synthetic_prompt = self._build_prompt_from_signals(route_signals, record)
        max_tokens = record.completion_tokens or None
        request = ChatCompletionRequest(
            model=record.requested_model,
            messages=[{"role": "user", "content": synthetic_prompt}],
            max_tokens=max_tokens,
            metadata=metadata,
        )
        return SimulationReplayInput(
            record=record,
            request=request,
            baseline_cost=(record.estimated_cost or 0.0) if record.final_route_target == "premium" else 0.0,
            replay_context=replay_context,
        )

    def _build_prompt_from_signals(self, route_signals: dict, record: UsageLedgerRecord) -> str:
        keyword_match = bool(route_signals.get("keyword_match"))
        token_count = int(route_signals.get("token_count") or record.prompt_tokens or record.total_tokens or 1)
        repeated = "x" * max(1, min(token_count * 4, 12000))
        prefix = "analyze architecture " if keyword_match else ""
        return f"{prefix}{repeated}"

    def _build_window(
        self,
        payload: PolicySimulationRequest,
        records: list[UsageLedgerRecord],
    ) -> PolicySimulationWindow:
        first_timestamp = records[0].timestamp if records else None
        last_timestamp = records[-1].timestamp if records else None
        return PolicySimulationWindow(
            requested_from=payload.from_timestamp,
            requested_to=payload.to_timestamp,
            evaluated_from=first_timestamp,
            evaluated_to=last_timestamp,
            requested_limit=payload.limit,
            changed_sample_limit=payload.changed_sample_limit,
            returned_rows=len(records),
        )

    def _baseline_target(self, record: UsageLedgerRecord) -> str:
        if record.terminal_status == "policy_denied":
            return "denied"
        return record.final_route_target

    def _simulation_target(self, evaluation: PolicyEvaluation) -> str:
        if evaluation.denied:
            return "denied"
        return evaluation.route_decision.target

    def _baseline_tier(self, record: UsageLedgerRecord) -> str | None:
        """The tier that served the row: None when it was denied or answered from the cache."""
        if record.terminal_status == "policy_denied":
            return None
        if record.final_route_target == "local":
            return "local"
        if record.final_route_target != "premium":
            return None
        tier = (record.route_signals or {}).get("tier")
        if tier in ("economy", "frontier"):
            return tier
        # No premium tier recorded (a heuristic decision, signals minimized away, or a fallback
        # from a local decision): the model that answered tells.
        return self._premium_tier(record.response_model)

    def _simulated_tier(self, evaluation: PolicyEvaluation) -> str | None:
        if evaluation.denied:
            return None
        decision = evaluation.route_decision
        if decision.target == "local":
            # A hard-budget downgrade keeps the premium decision's signals, tier included.
            return "local"
        tier = decision.signals.get("tier")
        if tier in ("economy", "frontier"):
            return tier
        return self._premium_tier(decision.model)

    def _premium_tier(self, model: str | None) -> str:
        economy_model = self.router_service.settings.economy_model
        return "economy" if economy_model and model == economy_model else "frontier"

    @staticmethod
    def _simulated_cost(evaluation: PolicyEvaluation) -> float:
        # The per-request cap and a hard-budget deny keep the projected cost they denied for;
        # a denied request runs nowhere and costs nothing.
        if evaluation.denied:
            return 0.0
        return evaluation.projected_premium_cost or 0.0

    def _record_changed(
        self,
        record: UsageLedgerRecord,
        evaluation: PolicyEvaluation,
        simulated_target: str,
    ) -> bool:
        baseline_target = self._baseline_target(record)
        if baseline_target != simulated_target:
            return True
        if self._policy_outcome_without_evidence(
            record.policy_outcome or ""
        ) != self._policy_outcome_without_evidence(evaluation.policy_outcome):
            return True
        baseline_cost = (record.estimated_cost or 0.0) if baseline_target == "premium" else 0.0
        simulated_cost = self._simulated_cost(evaluation)
        if round(baseline_cost, 8) != round(simulated_cost, 8):
            return True
        return False

    @staticmethod
    def _policy_outcome_without_evidence(policy_outcome: str) -> str:
        """Drop the outcome_evidence segment before diffing two policy outcomes.

        Simulation answers "would this candidate policy have routed differently".
        The evidence summary is recomputed from the tenant's *current* window at
        replay time, so it never matches the segment persisted on a historical
        ledger row. Leaving it in the comparison flags rows whose route, mode,
        and cost are identical, which is noise the operator cannot act on.
        """
        if not policy_outcome:
            return ""
        remaining = ";".join(
            part
            for part in policy_outcome.split(";")
            if part and not part.startswith("outcome_evidence=")
        )
        # PolicyService only falls back to the "default" sentinel when nothing else
        # was annotated, and it applies that fallback *after* attaching evidence. So
        # a live evaluation with no policy action reads "outcome_evidence=..." while
        # the historical row for the same non-action reads "default". Collapsing an
        # evidence-only outcome back to the sentinel keeps those two comparable.
        return remaining or "default"

    def _route_parity_from_record(self, record: UsageLedgerRecord) -> dict[str, str | bool | float | None]:
        route_signals = record.route_signals or {}
        inferred_route_mode = self._infer_route_mode_from_record(record)
        return {
            "route_mode": inferred_route_mode,
            "calibrated_routing": self._as_bool(route_signals.get("calibrated_routing"), default=(True if inferred_route_mode == "calibrated" else False if inferred_route_mode == "degraded" else None)),
            "degraded_routing": self._as_bool(route_signals.get("degraded_routing"), default=(True if inferred_route_mode == "degraded" else False if inferred_route_mode == "calibrated" else None)),
            "route_score": self._baseline_route_score(record, inferred_route_mode),
        }

    def _route_parity_from_decision(self, decision: RouteDecision) -> dict[str, str | bool | float | None]:
        route_signals = decision.signals or {}
        route_mode = self._as_route_mode(route_signals.get("route_mode"))
        return {
            "route_mode": route_mode,
            "calibrated_routing": self._as_bool(route_signals.get("calibrated_routing")),
            "degraded_routing": self._as_bool(route_signals.get("degraded_routing")),
            "route_score": self._decision_route_score(decision),
        }

    def _baseline_route_score(self, record: UsageLedgerRecord, route_mode: str | None) -> float | None:
        route_signals = record.route_signals or {}
        if route_mode is None:
            return None
        p_local = route_signals.get("p_local")
        if self._is_probability(p_local):
            # The learned router decided the row: its score was 1 - p_local, not the total of
            # the heuristic breakdown stored beside it.
            return round(1.0 - float(p_local), 4)
        score_components = route_signals.get("score_components")
        if isinstance(score_components, dict):
            total_score = score_components.get("total_score")
            if isinstance(total_score, int | float):
                return float(total_score)
        token_count = route_signals.get("token_count")
        keyword_match = route_signals.get("keyword_match")
        model_constraint = route_signals.get("model_constraint")
        if isinstance(token_count, int) and isinstance(keyword_match, bool):
            token_score = min(token_count / 500, 1.0)
            keyword_bonus = 0.2 if keyword_match else 0.0
            policy_bonus = 0.1 if model_constraint is True else 0.0
            return round(min(max(token_score + keyword_bonus + policy_bonus, 0.0), 1.0), 4)
        return None

    def _infer_route_mode_from_record(self, record: UsageLedgerRecord) -> str | None:
        route_signals = record.route_signals or {}
        explicit_route_mode = self._as_route_mode(route_signals.get("route_mode"))
        if explicit_route_mode is not None:
            return explicit_route_mode
        if record.route_reason == "calibrated_routing_disabled":
            return None
        token_count = route_signals.get("token_count")
        complexity_tier = route_signals.get("complexity_tier")
        keyword_match = route_signals.get("keyword_match")
        if isinstance(token_count, int) and isinstance(keyword_match, bool):
            if isinstance(complexity_tier, str):
                return "calibrated"
            return "degraded"
        return None

    def _decision_route_score(self, decision: RouteDecision) -> float | None:
        route_mode = self._as_route_mode((decision.signals or {}).get("route_mode"))
        if route_mode is None:
            return None
        return float(decision.score)

    def _as_route_mode(self, value: object) -> str | None:
        return value if isinstance(value, str) else None

    def _as_bool(self, value: object, default: bool | None = None) -> bool | None:
        if isinstance(value, bool):
            return value
        return default
