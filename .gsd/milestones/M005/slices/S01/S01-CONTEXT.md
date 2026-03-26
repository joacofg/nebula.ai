# S01: Adaptive routing model — Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

S01 delivers an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current prompt-length-plus-keyword heuristic. The new model is entirely internal — no new public API endpoints. The slice proves the routing decision model is materially better through unit tests on the scoring logic and an integration test proving the full chat-completions path uses the new signals.

</domain>

<decisions>
## Implementation Decisions

### Routing Signal Architecture
- Primary new signals: token estimate (replaces char count) + policy-context signals (budget proximity, model constraints from `TenantPolicy`)
- Policy fields (`soft_budget_usd`, `max_premium_cost_per_request`, `allowed_premium_models`) are inputs to the decision model — prevents misrouting near budget limits or with model restrictions
- Signal model is fixed (not operator-configurable) — interpretability requires a stable, understandable model before operator tuning (operator configurability deferred to S04)
- Signal count: 3-4 total (token estimate, complexity tier, policy context, model preference) — small enough to explain in one sentence, clearly beats current heuristic

### Decision Recording & Representation
- `RouteDecision` enriched with `signals: dict[str, Any]` and `score: float` fields — keeps existing frozen dataclass interface stable, adds inspectable signal payload
- Reason codes are structured with signal metadata payload — e.g., `reason="token_complexity"` + `signals={"token_count": 842, "threshold": 500, "complexity_tier": "medium"}`
- Usage ledger gets a `route_signals` JSON column — enables S02 simulation to replay decisions against real request history
- Existing `X-Nebula-Route` header extended with reason + top signal summary — keeps header count stable

### Operator Visibility Surface
- Route decision details exposed via Observability request detail drawer — add "Route Decision" section showing signals, score, and reason with plain-language labels (e.g., "Token count: 842 (above 500 threshold → premium)")
- Signal display uses plain-language labels, not raw JSON
- S01 includes route-decision vocabulary and signal reference in `docs/` — required before S02 simulation can reference stable decision model
- Test strategy: unit tests for signal scoring logic + integration test proving full request path uses new signals

### Claude's Discretion
- Exact token estimation approach (heuristic vs. tiktoken-style estimation) — keep it simple and fast, avoid heavy tokenizer dependency
- Complexity tier thresholds and exact scoring formula — should be defensible but tunable internally
- Specific doc filename and structure for route-decision vocabulary reference
- Console component placement within Observability drawer

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/nebula/services/router_service.py` — current `RouterService.choose_target_with_reason()` and `RouteDecision` dataclass are the extension points
- `src/nebula/models/governance.py` — `TenantPolicy` already has `routing_mode_default`, `max_premium_cost_per_request`, `soft_budget_usd`, `allowed_premium_models` — these become signal inputs
- `src/nebula/services/governance_store.py` — ledger recording path for adding `route_signals` column
- `console/src/app/(console)/observability/` — existing Observability request detail for drawer extension

### Established Patterns
- Frozen dataclasses for value objects (`RouteDecision`) — extend not replace
- `RoutingMode` Literal type for routing modes
- Async-first for all I/O in service layer
- Alembic migrations for schema changes
- Pydantic models for all API/ledger schemas

### Integration Points
- `chat_service.py` calls `router_service.choose_target_with_reason()` — the RouteDecision it returns feeds into ledger recording
- Ledger recording in `governance_store.py` — where `route_signals` column gets populated
- `api/routes/chat.py` — where `X-Nebula-Route` header is set from RouteDecision
- Observability console page and request-detail drawer — where route signals become visible to operators

</code_context>

<specifics>
## Specific Ideas

- Token estimate as primary complexity signal replaces raw char count — materially better proxy for model load
- Policy-aware routing: if `soft_budget_usd` is set and tenant ledger shows high recent spend, that's a signal to prefer local; if `allowed_premium_models` restricts to specific models, that's a routing constraint signal
- `route_signals` in the ledger as a JSON blob — same column supports S02 simulation replay without schema redesign
- "Route Decision" subsection in Observability drawer next to the existing Route section — not a new page, extends existing surface

</specifics>

<deferred>
## Deferred Ideas

- Operator-configurable signal weights — deferred to S04 recommendations surface
- Semantic embedding as routing signal — too complex for S01, revisit if token+policy proves insufficient
- Historical outcome signals (past latency/cost per route) — S02 simulation produces this data; S04 can feed it back
- Dedicated "Routing" console page — S01 extends Observability drawer; a dedicated page deferred to S04 if needed

</deferred>
