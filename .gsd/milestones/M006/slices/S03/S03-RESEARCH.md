# S03 Research — Runtime / simulation parity

## Summary
- S03 primarily advances active requirement **R039** and directly supports **R048**. The missing work is not new routing logic; it is proof and exposure that **live runtime and replay tell the same calibrated-vs-degraded story for the same tenant traffic class**.
- The backend already shares the routing core through `RouterService` and already reuses `PolicyService.evaluate()` inside replay. The current drift is at the **simulation contract surface**: `PolicySimulationChangedRequest` reports route target / status / policy / cost changes, but **does not carry baseline-vs-simulated calibrated semantics** (`route_mode`, calibrated/degraded flags, score) that runtime already emits in headers and ledger signals.
- Natural seam: extend the **existing simulation response** and **existing policy preview UI**. Do not add a new admin endpoint, new persistence, or a new observability destination.
- Relevant loaded-skill rule: from **debug-like-expert** / prior slice guidance, parity must be **verified, not assumed**. S03 should lock explicit runtime-vs-replay equivalence in focused tests rather than rely on “both paths call the same service” as proof.

## Recommendation
1. **Start in shared backend models and simulation service.** Add parity fields to the simulation changed-request contract so replay can report the same calibrated/degraded semantics already present in runtime headers and ledger rows.
2. **Then prove parity in backend tests** using real runtime requests plus replay over the same ledger window. The highest-value assertions are: same route target, same route reason, same route mode, and preserved degraded/gated semantics where applicable.
3. **Only after the contract is stable, wire the policy preview UI** to render bounded parity cues in the existing changed-request sample. Keep it compact and operator-readable.
4. Reuse the established vocabulary from S01/S02: `route_mode`, `calibrated_routing`, `degraded_routing`, `calibrated_routing_disabled`, `degraded_replay_signals`. Do not invent alternate labels.

## Implementation Landscape

### Backend runtime/replay seam
- `src/nebula/services/router_service.py`
  - This is already the shared routing core.
  - Live path: `_build_live_breakdown(..., route_mode="calibrated")`
  - Replay path: `_build_replay_breakdown(...)` marks `route_mode="degraded"` when `complexity_tier` or `keyword_match` are missing.
  - `RouteDecision.signals` already contains the parity-critical fields:
    - `route_mode`
    - `calibrated_routing`
    - `degraded_routing`
    - `score_components`
    - `replay`
- `src/nebula/services/policy_service.py`
  - Runtime and replay both flow through `evaluate(...)`.
  - Replay is triggered when `replay_context` is provided.
  - Gating behavior is centralized here: when `calibrated_routing_enabled` is false and route reason is `token_complexity`, evaluation rewrites the decision to:
    - `target="local"`
    - `reason="calibrated_routing_disabled"`
    - `signals={}`
    - `score=0.0`
  - This means S03 parity tests must cover both:
    - **calibrated/degraded** routes with route signals present
    - **gated** routes where route signals are intentionally absent
- `src/nebula/services/policy_simulation_service.py`
  - Replay already uses `policy_service.evaluate(...)`, so the decision semantics are shared.
  - Current gap: `PolicySimulationChangedRequest` only returns:
    - baseline/simulated route target
    - baseline/simulated terminal status
    - baseline/simulated policy outcome
    - baseline/simulated route reason
    - baseline/simulated estimated cost
  - It does **not** expose baseline vs simulated route mode, score, or replay degradation markers.
  - `_build_replay_input(...)` reconstructs replay from `UsageLedgerRecord.route_signals`; if those are partial, replay degrades exactly as S01 intended.
  - `approximation_notes` already provide the right bounded framing for replay uncertainty; S03 should reuse this pattern rather than add explanatory APIs.

### Persisted truth surface
- `src/nebula/models/governance.py`
  - `UsageLedgerRecord.route_signals` remains the persisted source of truth for live route semantics.
  - `PolicySimulationChangedRequest` and `PolicySimulationResponse` are the model seam to extend for parity.
  - `CalibrationEvidenceSummary` from S02 already covers tenant-window readiness, but not per-request parity details.
- `src/nebula/services/governance_store.py`
  - S02 summary derivation classifies degraded rows using `route_signals.route_mode`.
  - No new persistence is needed for S03. This file matters mainly as a constraint: **do not widen ledger schema**.

### API surface
- `src/nebula/api/routes/admin.py`
  - `/v1/admin/tenants/{tenant_id}/policy/simulate` already returns `PolicySimulationResponse`.
  - This is the correct place to surface parity fields once the response model is extended.
  - No new route should be introduced.

### Console seam
- `console/src/lib/admin-api.ts`
  - Mirrors `PolicySimulationChangedRequest` and `PolicySimulationResponse` types.
  - Any backend contract extension must land here as well.
- `console/src/components/policy/policy-form.tsx`
  - Existing “Preview before save” panel is the natural operator surface for S03.
  - It already renders a bounded “Changed request sample” list from `simulationResult.changed_requests`.
  - This is where parity cues can be added without broadening Observability.
  - Good place for compact text like baseline vs simulated route mode, or a concise parity summary in the changed item rendering.
- `console/src/app/(console)/policy/page.tsx`
  - Orchestration only. Likely unchanged except for type propagation.

### Existing tests that define the current boundary
- `tests/test_router_signals.py`
  - Already proves router semantics for:
    - live calibrated path
    - replay calibrated path when all persisted signals exist
    - replay degraded path when signals are missing
  - This remains the canonical unit-level contract for route-mode semantics.
- `tests/test_service_flows.py`
  - Best backend service-level seam for S03.
  - Already contains simulation tests and fake store support.
  - Existing parity-adjacent tests cover calibration summary and replay ordering, but not explicit baseline-vs-simulated route-mode parity in the simulation output.
- `tests/test_governance_api.py`
  - Best end-to-end API seam for S03.
  - Already has a useful runtime+simulate test: `test_admin_policy_simulation_can_disable_calibrated_routing_for_runtime_and_replay()`.
  - Also has a tenant-window replay test asserting summary counts and changed routes.
  - Missing assertions are around **parity fields themselves**.
- `console/src/components/policy/policy-page.test.tsx`
  - Current UI tests only assert route/status/outcome/cost preview behavior.
  - This is the right place to lock any new parity rendering.

## What exists vs. what is missing

### Already exists
- One shared routing core for live and replay (`RouterService`)
- One shared policy evaluator for live and replay (`PolicyService.evaluate`)
- Persisted live route semantics in ledger `route_signals`
- Tenant-window calibration summary (`CalibrationEvidenceSummary`)
- Existing simulation endpoint and existing policy preview UI

### Missing for S03
- A **simulation response field set** that exposes route-mode parity explicitly enough to prove R048/R039
- Focused tests proving that replay returns the same calibrated/degraded/gated semantics as the live request that produced the ledger row
- Bounded UI rendering of those parity semantics in the existing policy preview flow

## Natural task seams

### Seam 1 — Shared response contract
Likely files:
- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `console/src/lib/admin-api.ts`

This is the smallest backend-first slice of work:
- extend `PolicySimulationChangedRequest` with parity fields derived from:
  - baseline ledger row (`route_signals`, `route_reason`, maybe `estimated_cost`)
  - simulated `PolicyEvaluation.route_decision`
- keep the naming aligned to current vocabulary instead of adding a second representation

Likely useful fields:
- `baseline_route_mode: str | null`
- `simulated_route_mode: str | null`
- `baseline_route_score: float`
- `simulated_route_score: float`
- optionally baseline/simulated calibrated/degraded booleans if UI needs them, though `route_mode` may be enough

Note: gated rows intentionally have `route_signals is None` and no route mode. That should stay explicit as `null`, not synthesized.

### Seam 2 — Backend parity proof
Likely files:
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`
- possibly small support updates in test helpers only if needed

Highest-value scenarios:
1. **Live calibrated request → replay under same policy**
   - runtime emits `X-Nebula-Route-Mode=calibrated`
   - ledger row has `route_signals.route_mode == calibrated`
   - simulation changed-request (or unchanged sample, if contract supports it) preserves calibrated semantics
2. **Live degraded replay evidence path**
   - create a row with partial route signals or a realistic runtime row plus replay context missing fields
   - prove simulation reports degraded semantics instead of silently flattening to target-only parity
3. **Calibrated-routing-disabled gate**
   - runtime gated request has no route mode header and `route_reason=calibrated_routing_disabled`
   - simulation of the same policy change yields the same gated reason and null route mode

Current caveat: the simulation API only returns `changed_requests`, not unchanged sampled requests. If parity proof needs showing “same semantics when nothing changed,” planner may need to decide between:
- extending changed-request entries only, using scenarios where the candidate policy intentionally changes something but parity semantics remain inspectable, or
- widening the response slightly with a bounded inspected-request sample

The first option is smaller and more likely in-scope.

### Seam 3 — Policy preview rendering
Likely files:
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`

Bounded UX addition only:
- enrich each changed-request card with parity cues from the new fields
- keep the current compact style; do not turn this into a routing dashboard
- good fit for a short line under the route transition, e.g. baseline/simulated route mode or “degraded replay” marker

## Risks / constraints
- **Do not add new persistence.** S02 already established that calibration evidence must come from existing ledger metadata.
- **Do not invent a second degraded vocabulary.** Use `route_mode`, `calibrated_routing_disabled`, and `degraded_replay_signals` consistently.
- **Preserve bounded UI scope.** S04 is operator inspection surfaces; S03 should only use the existing preview surface enough to prove parity, not redesign it.
- **Watch the gated path carefully.** In gated cases, route mode is absent by design because `PolicyService` rewrites the decision with empty signals. A null mode is part of the contract, not a bug.
- **Simulation is oldest-first.** Existing replay ordering is deliberate; assertions should match that deterministic chronology.

## Skill discovery
Installed skills already relevant:
- `react-best-practices` — relevant if the planner wants tighter React/Next rendering guidance for the policy preview UI.
- `debug-like-expert` — relevant rule already applies here: prove parity with focused evidence, don’t infer it from architecture.

Promising external skills not installed:
- FastAPI: `npx skills add wshobson/agents@fastapi-templates`
- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns`
- Pydantic: `npx skills add bobmatnyc/claude-mpm-skills@pydantic`

These are optional. The current codebase patterns are already sufficient for S03.

## Verification plan
Backend-first verification should be enough to de-risk the slice before UI work:
- `./.venv/bin/pytest tests/test_router_signals.py -x`
- `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or calibration_summary" -x`
- `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x`

If the console preview changes:
- `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`
- optionally `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` if rendering logic moves downward into the form

## Recommendation to planner
Plan this slice as **two tasks, maybe three**:
1. **Backend contract + service wiring** for simulation parity fields.
2. **Focused backend verification** proving live runtime and replay semantics match across calibrated, degraded, and gated cases.
3. **Small policy preview UI update** only if the contract is operator-visible in S03; otherwise leave richer inspection for S04.

The riskiest unknown is not implementation complexity; it is choosing the smallest response extension that proves parity without accidentally creating a new analysis surface. Keep it narrow and attached to changed-request evidence.