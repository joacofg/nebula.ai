# Research — M009/S01: Outcome evidence contract

## Summary
- S01 directly owns **R077** and supports **R073, R074, R078**. The slice is the contract lock: if outcome evidence semantics drift here, runtime/replay/operator work in S02-S04 will fork immediately.
- The codebase already has a strong predecessor seam under the name **calibration**: `RouterService` emits typed additive `route_signals`, `GovernanceStore.summarize_calibration_evidence()` derives tenant-scoped sufficiency/thin/stale summaries from the usage ledger, and `PolicySimulationService` reconstructs replay from persisted route signals.
- The main gap is semantic, not infrastructural: current types and store logic only model `sufficient | thin | stale` plus replay degradation, while M009 requires a shared **outcome evidence** contract with explicit **sufficient/thin/stale/degraded** states and deterministic windowing. That means S01 should evolve the existing calibrated contract rather than invent a parallel subsystem.

## Recommendation
- Implement S01 by **renaming/extending the existing calibration evidence seam** into an outcome-evidence seam shared by router, governance store, replay, and later UI payloads. Follow the prior shared-contract pattern captured in memory `MEM034`/`MEM049`: contract first, propagation later.
- Build in this order:
  1. **Typed contract first** in `src/nebula/models/governance.py` and router types.
  2. **Deterministic ledger summarization logic** in `src/nebula/services/governance_store.py` with explicit degraded-state rules.
  3. **Focused backend tests** for state transitions and bounded windows before any live routing changes.
- Keep the S01 output narrow: do **not** change route choice semantics yet. The slice should deliver a backend artifact and proofs that S02/S03 can consume.

## Requirements Coverage
- **R077 (primary owner):** `GovernanceStore.summarize_calibration_evidence()` is the existing fail-safe truth seam. Today it degrades only at per-row reason level, not summary-state level.
- **R073 (supporting):** `RouterService` currently uses prompt heuristics plus additive calibrated score only; no tenant outcome summary participates in live choice yet.
- **R074 (supporting):** `PolicySimulationService` already depends on persisted `route_signals` and inferred route mode, so whatever contract S01 defines must be replay-friendly and reconstructible from stored ledger metadata.
- **R078 (supporting):** Existing request-first and hosted-boundary decisions are already encoded in the data model and tests; extending current types preserves scope discipline better than introducing analytics-style aggregates.

## Implementation Landscape

### `src/nebula/models/governance.py`
- Current core types:
  - `CalibrationEvidenceState = Literal["sufficient", "thin", "stale"]`
  - `CalibrationDegradedReason = Literal["missing_route_signals", "degraded_replay_signals"]`
  - `CalibrationEvidenceSummary` with counts for eligible/sufficient/excluded/gated/degraded rows and thresholds.
- This is the natural home for the S01 contract. The planner should expect this file to absorb:
  - renamed/generalized evidence-state vocabulary,
  - degraded summary-state inclusion,
  - possibly new outcome reason literals and/or factor summary fields.
- Important constraint: these Pydantic models are already consumed by backend responses and console types, so shape changes here will ripple broadly. For S01, prefer **additive/backward-compatible** evolution where possible.

### `src/nebula/services/governance_store.py`
- This is the current deterministic derivation seam.
- `summarize_calibration_evidence()`:
  - reads bounded recent ledger rows via `list_usage_records(... limit=200)`,
  - classifies each row into excluded / gated / eligible,
  - classifies eligible rows into degraded vs sufficient based on `route_signals` and `route_mode`,
  - derives summary state via `_calibration_state()`.
- Current degraded logic is row-local only:
  - missing `route_signals` → `missing_route_signals`
  - `route_mode == "degraded"` → `degraded_replay_signals`
  - any non-`calibrated` route mode → `missing_route_signals`
- Current state derivation ignores degraded counts entirely:
  - `0 sufficient` → `thin`
  - `< threshold` → `thin`
  - stale timestamp → `stale`
  - else `sufficient`
- This is the highest-value S01 file. If M009 needs explicit summary-level `degraded`, this function and `_calibration_state()` are where that rule must be made precise.

### `src/nebula/services/router_service.py`
- Existing shared additive contract is already strong:
  - `CalibratedScoreBreakdown`
  - `RouteDecision(signals, score)`
  - route-mode literals: `"calibrated" | "heuristic_override" | "degraded"`
- Live routing is still prompt-derived only (`_build_live_breakdown` from prompt token/keyword complexity).
- Replay already supports degradation when persisted replay inputs are incomplete.
- S01 likely should **not** change route choice here yet, but it may need to add typed factor vocabulary that S02 will later populate from outcome evidence.

### `src/nebula/services/policy_simulation_service.py`
- Replay is already designed around persisted metadata instead of raw prompts.
- It reconstructs `ReplayRouteContext` from stored `route_signals`, and it infers baseline parity from persisted `route_mode`, `calibrated_routing`, `degraded_routing`, and score components.
- This means S01’s contract must remain:
  - serializable into `UsageLedgerRecord.route_signals`,
  - reconstructible without provider calls,
  - deterministic under oldest-first replay ordering.
- Any outcome evidence summary that cannot be derived from stored ledger rows will violate the replay parity direction established in S03.

### `src/nebula/services/policy_service.py`
- Policy currently has one important gating hook: if `calibrated_routing_enabled` is false and route reason was `token_complexity`, it forcibly returns local with reason `calibrated_routing_disabled` and empty signals.
- This creates a “gated but unscored” path already treated specially by store and tests.
- S01 should preserve this separation:
  - **excluded** = explicit override / forced routing,
  - **gated** = policy disabled,
  - **degraded** = evidence or replay precision incomplete.

### `src/nebula/services/chat_service.py`
- Persists the authoritative request row through `_record_usage(...)` with `route_signals=policy_resolution.route_decision.signals or None`.
- Emits `X-Nebula-Route-Mode` header only when present.
- This is the persistence seam S02 will rely on; S01 should only note that route-signal truth already exists and is bounded by governance minimization (`strict` can suppress route signals entirely).

### `src/nebula/db/models.py`
- `UsageLedgerModel.route_signals` is JSON and nullable. Good fit for incremental factor vocabulary extension.
- No dedicated outcome-summary table exists; that strongly suggests S01 should keep evidence derived-on-read from ledger rows rather than inventing a second persistence path.

## Existing Verification / Prior Art
- `tests/test_router_signals.py`
  - proves live calibrated signals, replay degraded signals, header propagation, and ledger persistence for route signals.
- `tests/test_governance_api.py`
  - already proves policy simulation parity against persisted route mode / score,
  - proves `calibration_summary` counts and state in admin responses,
  - proves rollout-disabled rows persist `route_signals is None` and reason `calibrated_routing_disabled`.
- There are **no direct unit tests** for `GovernanceStore.summarize_calibration_evidence()` state transitions independent of HTTP flows. That is likely the cleanest missing proof to add in S01.

## Natural Seams for Planning
1. **Contract/types seam**
   - Files: `src/nebula/models/governance.py`, possibly router type aliases in `src/nebula/services/router_service.py`.
   - Output: explicit outcome evidence summary vocabulary and typed reasons/factors.
2. **Derivation seam**
   - File: `src/nebula/services/governance_store.py`.
   - Output: deterministic bounded recent-window summarization with explicit sufficient/thin/stale/degraded rules.
3. **Proof seam**
   - Files: likely `tests/test_governance_api.py` plus a new focused backend test module or direct store-level tests.
   - Output: stable transition proofs for no evidence, thin evidence, stale evidence, degraded eligible evidence, sufficient fresh evidence.

## What To Build or Prove First
- First prove the **state machine** for the summary contract in isolation. This is the riskiest ambiguity in the milestone brief.
- Specifically resolve and encode:
  - When does the **summary state** become `degraded` rather than `thin`?
  - Does degraded outrank stale, or does stale outrank degraded when the newest eligible evidence is too old?
  - Are rows with suppressed `route_signals` due to strict governance treated as degraded eligible evidence or as unavailable evidence? Current code counts them as degraded via `missing_route_signals` if they are otherwise eligible.
- The planner should force these semantics into tests before any runtime routing behavior changes.

## Risks / Unknowns
- **State precedence is currently underspecified.** The milestone context requires explicit sufficient/thin/stale/degraded states, but the existing code only exposes degraded as a count/reason, never as the summary state. This is the main design ambiguity.
- **Naming drift risk.** The code and UI are built around “calibration” language. Renaming every surface to “outcome evidence” in S01 could create churn across backend/UI/tests before any behavior changes. Safer plan: extend backend types first, then migrate terminology in later slices only where needed.
- **Governance minimization interaction.** `metadata_minimization_level="strict"` strips `route_signals`. That means request rows can become replay-degraded by policy, not system failure. Tests should make this explicit so S03 can degrade honestly.
- **Limit/window semantics are bounded but simplistic.** `summarize_calibration_evidence()` uses `list_usage_records(... limit=200)` newest-first and then derives latest timestamps from that bounded set. If M009 wants a more explicit recent evidence window, S01 may need to add/clarify time-window inputs rather than only a record cap.

## Skill / Rule Notes
- Relevant installed skills already present: `api-design` (for contract-shape discipline), `tdd` and `verify-before-complete` (useful for forcing test-first state-machine proof), `observability` (if factor vocabulary later needs durable diagnostics).
- No installed FastAPI/SQLAlchemy-specific skill exists. Promising external skills if the user wants them later:
  - `npx skills add wshobson/agents@fastapi-templates` (highest-install FastAPI result)
  - `npx skills add bobmatnyc/claude-mpm-skills@sqlalchemy-orm`
  - `npx skills add bobmatnyc/claude-mpm-skills@pydantic`
- Most relevant rule from loaded skills/context: the existing request-first / shared-contract posture means **don’t hand-roll a second evidence subsystem** when `governance_store + route_signals + simulation replay` already form the authoritative seam.

## Verification Recommendations
- Prefer focused pytest targets over full suite first:
  - `pytest tests/test_router_signals.py -k degraded`
  - `pytest tests/test_governance_api.py -k calibration_summary`
  - add a new focused store/contract test target if created, e.g. `pytest tests/test_outcome_evidence_contract.py`
- The S01 verification bar should include:
  1. deterministic state transitions across no evidence / thin / stale / degraded / sufficient,
  2. tenant scoping and bounded window behavior,
  3. governance suppression causing honest degraded behavior,
  4. replay-facing artifacts still serializable through `route_signals` and `CalibrationEvidenceSummary` successor types.

## Sources
- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/router_service.py`
- `src/nebula/services/policy_service.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/services/chat_service.py`
- `src/nebula/db/models.py`
- `tests/test_router_signals.py`
- `tests/test_governance_api.py`
