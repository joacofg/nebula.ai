# S02 Research — Ledger-backed calibration evidence

## Summary

S02 primarily advances **R039** and directly supports **R045**, **R046**, and **R047**. The core need is not a new routing algorithm; S01 already shipped the shared calibrated/degraded route contract. The gap is that runtime and replay currently only persist **per-request** `route_signals`, while this slice needs a **tenant-scoped, bounded summary** derived from existing usage-ledger metadata that can say whether calibration evidence is **sufficient, stale, or thin**.

The natural implementation seam is to add a new typed calibration-summary contract in the governance/admin layer, derive it from existing `UsageLedgerRecord` rows, and then reuse that summary in simulation and Observability. Do not widen persistence, do not add raw payload capture, and do not create a parallel analytics surface. That matches the milestone scope and the existing product pattern of bounded, ledger-backed operator evidence.

Two loaded rules matter here:
- From the GSD execution rules: prefer existing seams and keep verification tied to the real failure/diagnostic surface.
- From project knowledge: keep Observability as the **persisted explanation surface**, not a new dashboard; derive operator wording from runtime/admin truth instead of inventing new entities.

## Recommendation

Build S02 around a **shared backend calibration-summary service/output type** that:
1. reads recent tenant-scoped usage-ledger rows,
2. derives deterministic evidence-window metrics from existing metadata (`route_reason`, `policy_outcome`, `route_signals`, timestamps, terminal status, route target),
3. emits a bounded summary with explicit evidence state markers like **sufficient / stale / thin**, and
4. is reused by both policy simulation preview and Observability request/detail surfaces.

Start in the backend model/service layer, not the UI. The riskiest part is defining a summary shape that is stable, bounded, and replay-friendly without drifting into analytics. Once that contract exists, API/UI/test work is straightforward.

## Implementation Landscape

### Existing seams that already fit S02

- `src/nebula/services/router_service.py`
  - S01’s calibrated contract already emits the replay-critical per-request fields:
    - `token_count`
    - `complexity_tier`
    - `keyword_match`
    - `route_mode`
    - `calibrated_routing`
    - `degraded_routing`
    - `score_components`
    - `replay`
  - Important constraint from knowledge: explicit overrides and policy-forced routes intentionally keep `route_signals={}` and `route_score=0.0`. Any summary logic must treat those as **out of calibration evidence scope**, not as missing-data failures.

- `src/nebula/services/policy_service.py`
  - This is where router output becomes final policy-aligned evidence.
  - `calibrated_routing_enabled=False` currently rewrites `token_complexity` decisions to `RouteDecision(target="local", reason="calibrated_routing_disabled", signals={}, score=0.0)`.
  - That means S02 summary logic cannot rely on live requests always retaining calibrated per-request signal payloads after gating; it needs to reason from persisted ledger patterns, including gated and degraded paths.

- `src/nebula/services/governance_store.py`
  - Existing ledger persistence/readback is already sufficient for S02 inputs:
    - `route_reason`
    - `policy_outcome`
    - `route_signals`
    - timestamps
    - route target / terminal status / estimated cost
  - There is no tenant-level calibration summary method yet. This is the likely insertion point for a new aggregation method.
  - Project knowledge rule from M005 still applies: if `UsageLedgerRecord` changes, update both `record_usage()` and `_usage_from_model()` together.

- `src/nebula/models/governance.py`
  - Good place for a new typed summary model because policy simulation, admin API, and console already mirror types from here.
  - Current contracts stop at raw ledger rows plus policy simulation response; there is no typed calibration-summary output yet.

- `src/nebula/services/policy_simulation_service.py`
  - Replay already depends on ledger-backed evidence and intentionally works oldest-first for deterministic sampling.
  - S02 should probably expose calibration sufficiency/staleness for the replay window here rather than recomputing similar logic only in the UI.
  - The `approximation_notes` pattern is already established and is a good fit for bounded explanation of degraded/thin/stale evidence.

- `src/nebula/api/routes/admin.py`
  - Current admin seams are:
    - `/admin/usage/ledger`
    - `/admin/tenants/{tenant_id}/policy/simulate`
    - `/admin/tenants/{tenant_id}/recommendations`
  - S02 can extend an existing route response or add one narrow tenant-scoped admin endpoint, but should avoid a broad new API family.

- `console/src/lib/admin-api.ts`
  - Any new summary/preview fields need mirrored TS types here first.

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Currently renders bounded per-request evidence from `route_signals` and structured `policy_outcome` parsing.
  - Good fit for showing a compact “calibration evidence state” block tied to the selected request’s tenant/window, but not for rendering charts or broad analytics.

- `console/src/app/(console)/observability/page.tsx`
  - Already frames the page correctly: persisted ledger first, recommendations and dependency health second.
  - This is the right place to show tenant-scoped calibration summary context as supporting evidence, as long as the ledger remains primary.

- `console/src/components/policy/policy-form.tsx` and policy preview tests
  - The preview-before-save pattern is already explicit and non-mutating.
  - S02 can safely add calibration evidence status to preview results without changing the UI philosophy.

### Natural task seams

1. **Define the calibration summary contract**
   - Files: `src/nebula/models/governance.py`
   - Output: typed summary models for evidence sufficiency/staleness/thinness and bounded supporting counts/fields.
   - This should happen first because downstream API/UI/tests need a stable shape.

2. **Derive tenant-scoped summary from ledger rows**
   - Files: `src/nebula/services/governance_store.py` or a new focused backend service under `src/nebula/services/`
   - Inputs should stay limited to existing ledger metadata.
   - Determinism matters more than sophistication.

3. **Thread summary into replay/simulation**
   - Files: `src/nebula/services/policy_simulation_service.py`, `src/nebula/api/routes/admin.py`
   - Best use is likely window-level evidence status plus bounded notes; avoid per-request duplication beyond what already exists in `changed_requests`.

4. **Expose summary to Observability/operator surfaces**
   - Files: `console/src/lib/admin-api.ts`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`
   - Keep the UI compact and explanatory.

5. **Proof coverage**
   - Backend: `tests/test_service_flows.py`, `tests/test_router_signals.py`, possibly focused admin API tests.
   - Console: `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, maybe `console/src/components/policy/policy-page.test.tsx`.

## What to build or prove first

1. **First prove the evidence contract**
   - Decide exactly what “sufficient”, “stale”, and “thin” mean using bounded deterministic inputs.
   - Likely dimensions available today:
     - row count in window,
     - recency from timestamps,
     - fraction/count of rows with usable calibrated signals,
     - fraction/count of degraded replay markers,
     - count of gated rows (`route_reason="calibrated_routing_disabled"`),
     - maybe split by `token_complexity` vs explicit/policy-forced requests.
   - Do not depend on prompt text, raw payloads, or any new persisted fields.

2. **Then prove replay can consume the same summary semantics**
   - S03 depends on parity, so S02 should avoid inventing UI-only evidence logic.
   - The same backend summary should be available to simulation preview.

3. **Then prove operator rendering stays bounded**
   - Observability and request detail should explain the evidence state in one screenful.
   - Avoid charts, percentages without explanation, or anything that reads like an analytics product.

## Constraints and risks

### Constraint: evidence scope must exclude override traffic

From S01 and knowledge, explicit override/policy-forced routes intentionally have empty `route_signals`. If S02 counts those rows as “missing calibration evidence”, it will incorrectly mark healthy traffic as degraded/thin. Summary derivation should either:
- filter to `route_reason == "token_complexity"`, or
- explicitly separate “eligible for calibration evidence” from “outside calibration scope”.

### Constraint: gated traffic is meaningful, not noise

`PolicyService` rewrites auto-routed token-complexity requests to `reason="calibrated_routing_disabled"` with empty signals when the tenant rollout valve is off. That likely needs to appear in the summary as an intentional operator-controlled state, not as accidental evidence loss.

### Constraint: replay already degrades deterministically

`PolicySimulationService` reconstructs replay from ledger rows and sets `route_mode="degraded"` when key replay fields are missing. S02 should not invent a second degraded vocabulary. Reuse the existing calibrated/degraded markers and approximation-note pattern.

### Risk: analytics drift

The tempting implementation is to compute lots of aggregates. That would violate R049 and the milestone context. Keep the summary narrow:
- evidence state,
- why it has that state,
- a handful of counts/recency indicators,
- maybe one or two operator-readable supporting facts.

### Risk: contract drift across Python and TS

Any new admin response field must be mirrored in `console/src/lib/admin-api.ts`, then rendered/tests updated. This repo already relies on shared naming consistency across backend and console.

## Verification plan

### Backend

Primary focused verification targets:
- `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x`
- `./.venv/bin/pytest tests/test_router_signals.py -x`
- `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or route_reason or policy_options" -x`

Add focused cases that prove:
- tenant-scoped summary classifies **sufficient** when recent eligible ledger rows contain enough calibrated fields,
- summary classifies **thin** when too few eligible rows exist,
- summary classifies **stale** when the window exists but is too old,
- explicit override rows do not poison sufficiency math,
- gated rows are surfaced distinctly from accidental missing evidence,
- simulation preview returns or references the same evidence-state semantics as the summary source.

### Console

Primary focused verification targets:
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`
- If preview is extended: `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`

Add focused cases that prove:
- Observability copy keeps the ledger as the persisted explanation surface,
- calibration summary is rendered as bounded operator evidence, not analytics,
- request detail gracefully handles sufficient/stale/thin states,
- gated/disabled calibration messaging is explicit and non-alarmist.

## Suggested skill discovery notes

Directly relevant installed skills already present in this environment:
- `react-best-practices` — relevant if S02 touches `console/src/app/(console)/observability/page.tsx` or ledger detail rendering.

Promising external skills discovered but not needed unless the planner wants extra framework-specific guardrails:
- FastAPI: `npx skills add wshobson/agents@fastapi-templates`
- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns`
- SQLAlchemy: `npx skills add bobmatnyc/claude-mpm-skills@sqlalchemy-orm`

## File-by-file notes for the planner

- `src/nebula/models/governance.py`
  - Add new typed calibration-summary models here first.

- `src/nebula/services/governance_store.py`
  - Best place to add tenant/window ledger aggregation unless a new dedicated calibration-summary service is cleaner.
  - Keep raw-row mapping untouched unless the summary genuinely requires new fields.

- `src/nebula/services/policy_simulation_service.py`
  - Best place to attach summary/evidence-state to replay results because it already owns replay window semantics and approximation notes.

- `src/nebula/api/routes/admin.py`
  - Thread new response fields or add one narrow tenant-scoped summary endpoint.

- `console/src/lib/admin-api.ts`
  - Mirror any new backend models exactly.

- `console/src/app/(console)/observability/page.tsx`
  - Likely landing zone for tenant-scoped calibration evidence summary.

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Best place for bounded request-adjacent calibration explanation.

- `tests/test_service_flows.py`
  - Best backend file for summary derivation and replay-window parity tests.

- `console/src/components/ledger/ledger-request-detail.test.tsx`
  - Best UI file for evidence-state rendering tests.

## Bottom line

This slice is **targeted**, not deep-R&D. The architecture is already in place. The real work is to define one disciplined ledger-derived calibration-summary contract, make it deterministic, and reuse it across replay and Observability without turning Nebula into an analytics product.