from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException

from nebula.models.governance import (
    PolicySimulationChangedRequest,
    PolicySimulationOutcomeCounts,
    PolicySimulationRequest,
    PolicySimulationResponse,
    PolicySimulationWindow,
    TenantPolicy,
    UsageLedgerRecord,
)
from nebula.models.openai import ChatCompletionRequest
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_service import PolicyEvaluation, PolicyService
from nebula.services.router_service import RouterService


@dataclass(slots=True, frozen=True)
class SimulationReplayInput:
    record: UsageLedgerRecord
    request: ChatCompletionRequest
    baseline_cost: float


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
            changed_requests=sampled_changed,
        )

    def _build_replay_input(self, record: UsageLedgerRecord) -> SimulationReplayInput:
        metadata = {"simulation": {"request_id": record.request_id}}
        route_signals = record.route_signals or {}
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
