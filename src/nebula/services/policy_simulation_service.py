from __future__ import annotations

from dataclasses import dataclass

from nebula.models.governance import (
    PolicySimulationChangedRequest,
    PolicySimulationOutcomeCounts,
    PolicySimulationRequest,
    PolicySimulationResponse,
    PolicySimulationWindow,
    UsageLedgerRecord,
)
from nebula.models.openai import ChatCompletionRequest
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyEvaluation, PolicyService
from nebula.services.router_service import ReplayRouteContext, RouteDecision, RouterService


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
    Token-count and keyword-match route signals from the original decision are reused when present;
    otherwise a synthetic prompt based on token volume is used to approximate complexity routing.
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
        records = list(reversed(records))

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

        simulation_context = AuthenticatedTenantContext(
            tenant=tenant_context.tenant,
            api_key=tenant_context.api_key,
            policy=payload.candidate_policy,
        )

        for replay_input in replay_inputs:
            evaluated_count += 1
            baseline_target = self._baseline_target(replay_input.record)
            baseline_denied = replay_input.record.terminal_status == "policy_denied"
            baseline_cost = replay_input.baseline_cost
            baseline_premium_cost_total += baseline_cost

            evaluation = await self.policy_service.evaluate(
                request=replay_input.request,
                tenant_context=simulation_context,
                router_service=self.router_service,
                replay_context=replay_input.replay_context,
                before_timestamp=replay_input.record.timestamp,
                evidence_summary_override=calibration_summary,
            )

            simulated_target = self._simulation_target(evaluation)
            simulated_denied = evaluation.denied
            simulated_cost = evaluation.projected_premium_cost or 0.0
            simulated_premium_cost_total += simulated_cost

            if baseline_target != simulated_target:
                changed_routes += 1
            if not baseline_denied and simulated_denied:
                newly_denied += 1

            if self._record_changed(replay_input.record, evaluation, simulated_target):
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
                    )
                )

        sampled_changed = changed[: payload.changed_sample_limit]
        window = self._build_window(payload, records)
        return PolicySimulationResponse(
            tenant_id=tenant_context.tenant.id,
            candidate_policy=payload.candidate_policy,
            approximation_notes=[
                "Replay uses persisted ledger request metadata and route signals instead of raw prompt text.",
                "When route signals are incomplete, prompt complexity is approximated from stored token counts.",
                "Projected premium cost is estimated with current pricing rules and no provider call is executed.",
            ],
            window=window,
            summary=PolicySimulationOutcomeCounts(
                evaluated_rows=evaluated_count,
                changed_routes=changed_routes,
                newly_denied=newly_denied,
                baseline_premium_cost=round(baseline_premium_cost_total, 8),
                simulated_premium_cost=round(simulated_premium_cost_total, 8),
                premium_cost_delta=round(simulated_premium_cost_total - baseline_premium_cost_total, 8),
            ),
            calibration_summary=calibration_summary,
            changed_requests=sampled_changed,
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

    def _record_changed(
        self,
        record: UsageLedgerRecord,
        evaluation: PolicyEvaluation,
        simulated_target: str,
    ) -> bool:
        baseline_target = self._baseline_target(record)
        if baseline_target != simulated_target:
            return True
        if (record.policy_outcome or "") != evaluation.policy_outcome:
            return True
        baseline_cost = (record.estimated_cost or 0.0) if baseline_target == "premium" else 0.0
        simulated_cost = evaluation.projected_premium_cost or 0.0
        if round(baseline_cost, 8) != round(simulated_cost, 8):
            return True
        return False

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
