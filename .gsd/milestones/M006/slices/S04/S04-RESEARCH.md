# S04 Research — Operator inspection surfaces

## Summary

S04 primarily supports **R039** and **R046**, with direct dependency on the S01/S02/S03 contracts for calibrated/degraded/null-mode routing semantics. This is **light research**: the backend/data contracts already exist, and the natural work is to extend the **existing request-detail and Observability UI surfaces** so operators can inspect calibrated-vs-heuristic state and contributing evidence **without adding new admin APIs or analytics-style views**.

The main constraint is scope discipline from the milestone context and prior slices: keep the **persisted ledger row** as the primary proof surface, use the **tenant calibration summary** as supporting context only, and reuse the existing route vocabulary from `docs/route-decision-vocabulary.md` rather than inventing new labels.

## Recommendation

Plan S04 as a **console-first slice** with bounded verification.

1. **Request-detail inspection first** in `console/src/components/ledger/ledger-request-detail.tsx`.
   - Add explicit rendering for the already-shipped routing semantics from a selected ledger row: `route_mode`, `calibrated_routing`, `degraded_routing`, `score_components`, and the existing replay-critical route signals.
   - Treat `route_mode=null` as intentional when the row is rollout-disabled or policy-forced, consistent with S03.
   - Keep the selected request row authoritative; calibration summary remains supporting tenant context.
2. **Observability composition second** in `console/src/app/(console)/observability/page.tsx`.
   - Reframe or enrich the page so operators can see the selected request evidence and the supporting calibration/runtime context together.
   - Reuse the same labels and explanation vocabulary already present in request detail and simulation preview.
   - Do not introduce a new “routing inspector” API or separate dashboard.
3. **Focused tests last**.
   - Extend the existing ledger-request-detail and Observability tests rather than creating broad new suites.
   - Assert bounded rendering, request-centric framing, and correct handling of calibrated / degraded / rollout-disabled / override rows.

The work should stay local to the console unless implementation reveals a missing typed field in `console/src/lib/admin-api.ts`. Right now the needed fields are already present on `UsageLedgerRecord.route_signals`, `CalibrationEvidenceSummary`, and simulation changed-request types.

## Implementation Landscape

### Existing backend and contract seams

- `src/nebula/models/governance.py`
  - Defines the shared types already needed by S04:
    - `UsageLedgerRecord` with `route_reason`, `policy_outcome`, `route_signals`
    - `CalibrationEvidenceSummary`
    - `PolicySimulationChangedRequest` with baseline/simulated route mode, calibrated/degraded flags, and route score
- `src/nebula/services/governance_store.py`
  - `summarize_calibration_evidence()` already classifies rows as sufficient/thin/stale and separates:
    - excluded rows (`explicit_model_override`, `policy_forced_routing`)
    - gated rows (`calibrated_routing_disabled`)
    - degraded rows (`missing_route_signals`, `degraded_replay_signals`)
  - No extra persistence or API family appears necessary.
- `src/nebula/services/policy_simulation_service.py`
  - Already converts persisted rows and simulated route decisions into a parity-friendly shape.
  - S03’s null-mode rule is explicit here: rollout-disabled rows intentionally emit `route_mode=None`.
- `src/nebula/api/routes/admin.py`
  - Existing admin endpoints are sufficient for S04:
    - `GET /v1/admin/usage/ledger`
    - `GET /v1/admin/tenants/{tenant_id}/recommendations`
    - `POST /v1/admin/tenants/{tenant_id}/policy/simulate`
  - There is **no dedicated request-detail endpoint**; the console derives detail from the selected ledger row. That matches the bounded-surface constraint.

### Existing console surfaces

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Already renders:
    - persisted request identity and route/provider/policy basics
    - tenant calibration summary as supporting context
    - budget evidence
    - a basic `Route Decision` section with `token_count`, `complexity_tier`, `keyword_match`, `model_constraint`, `budget_proximity`
  - **Current gap for S04:** it does **not** expose the richer calibrated-vs-degraded route semantics from `route_signals` such as:
    - `route_mode`
    - `calibrated_routing`
    - `degraded_routing`
    - `score_components.*`
    - total route score from `score_components.total_score`
  - This is the cleanest seam for “operators can inspect calibrated-vs-heuristic routing state and contributing evidence”.
- `console/src/app/(console)/observability/page.tsx`
  - Already composes:
    - ledger filters/table
    - request detail panel
    - recommendations card area
    - calibration summary card
    - cache/runtime summary
    - dependency health
  - The page already states that ledger/request correlation is primary and supporting cards are context only.
  - **Likely S04 work:** improve inspection composition/copy around the selected request and avoid analytics drift, not new data loading.
- `console/src/components/ledger/ledger-table.tsx`
  - Only shows broad row metadata today: timestamp, request ID, tenant, route target, provider, status, latency, cost.
  - Possible small enhancement seam if the planner wants quicker discovery of calibrated/degraded rows, but this is optional. The title/roadmap language points more strongly to request detail and Observability than table redesign.
- `console/src/components/policy/policy-form.tsx`
  - Already renders S03 preview parity lines through `renderChangedRequestParity()`.
  - This is a useful reference implementation for S04 UI wording:
    - `calibrated (...)`
    - `degraded (...)`
    - `rollout disabled`
    - `unscored`
  - Reuse this vocabulary or extract a shared formatter if duplication becomes real.

### Existing tests that should be extended

- `console/src/components/ledger/ledger-request-detail.test.tsx`
  - Already locks:
    - selected-row framing
    - no-payload-leak behavior
    - basic route decision rendering
    - calibration summary states
    - budget evidence states
  - Best place to add calibrated/degraded/rollout-disabled route-inspection assertions.
- `console/src/app/(console)/observability/observability-page.test.tsx`
  - Already verifies the integrated page framing and scoped assertions with `within(...)`.
  - Extend this instead of inventing broader UI tests.
- `console/src/app/(console)/observability/page.test.tsx`
  - Already checks the higher-level request-evidence framing.
- `console/src/components/policy/policy-page.test.tsx`
  - Useful as vocabulary reference for parity wording; probably no direct S04 edit unless copy is intentionally unified.
- `console/src/components/ledger/ledger-table.test.tsx`
  - Small focused table test exists if quick scan affordances are added.

## Natural task seams

### Task seam 1 — request-detail routing inspection

**Primary files**
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`

**Goal**
Render bounded operator-readable inspection of the selected request’s routing evidence using the existing `route_signals` contract.

**Likely implementation details**
- Add a small helper layer to parse route signals safely.
- Surface:
  - route mode (`calibrated`, `degraded`, or intentional null/unscored state)
  - calibrated/degraded booleans
  - additive score components and total score
  - maybe whether the row is replay-derived vs live if `replay` exists in the signal payload
- Keep labels aligned to `docs/route-decision-vocabulary.md`.
- Preserve current “primary proof = persisted row” framing.

**Risk**
Low-medium. Mostly UI composition and wording discipline.

### Task seam 2 — observability composition and bounded operator framing

**Primary files**
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- possibly `console/src/app/(console)/observability/page.test.tsx`

**Goal**
Make the page read as a coherent operator inspection surface for one selected request plus supporting context, without drifting into analytics.

**Likely implementation details**
- Strengthen copy/layout around how selected request detail, tenant calibration summary, and dependency/runtime context relate.
- If needed, pass additional selected-row context or add small visual grouping — but stay inside the existing page structure.
- Reuse the S03 null-mode semantics and S02 scoped-label testing pattern.

**Risk**
Low. Mostly copy/composition and test updates.

### Task seam 3 — optional shared route-state formatter

**Primary files**
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/policy/policy-form.tsx`
- maybe a new tiny helper under `console/src/lib/` or `console/src/components/ledger/`

**Goal**
If the planner sees duplication risk, extract a small formatter for route-state labels so request detail and policy preview tell the same story.

**Notes**
- This is only worthwhile if it stays tiny and local.
- Don’t force abstraction if request detail can just follow the same wording without complicated sharing.

## Constraints and rules to carry forward

- From milestone context and prior slices:
  - **Do not add a new admin API family or analytics dashboard.**
  - **Do not displace the ledger row as primary proof.** Calibration summary and runtime context stay supporting surfaces.
  - **Reuse existing vocabulary** from `docs/route-decision-vocabulary.md` and S03 parity fields.
- From S02 forward intelligence:
  - Shared labels can appear in multiple cards; tests should use scoped assertions with `within(...)` rather than assume page-wide uniqueness.
- From S03 forward intelligence:
  - Reuse parity fields directly; do not re-derive semantics differently in UI.
  - Treat `route_mode=null` as intentional for rollout-disabled/policy-forced rows.
- From the loaded `react-best-practices` skill:
  - Keep UI work local and avoid speculative abstraction.
  - Prefer direct imports / simple helpers over new broad indirection.
  - Preserve server/client data flow simplicity; this page is already client-driven and should stay explicit.

## Verification

Use the existing focused console suites; no backend runner appears necessary unless implementation unexpectedly touches contracts.

Primary commands:

- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`
- `npm --prefix console run test -- --run src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx`

If the planner touches shared wording/helpers used by policy preview:

- `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`

## Skill discovery

Installed relevant skill already available:
- `react-best-practices` — sufficient for this slice’s React/Next console work.

Promising external skill, not installed:
- `wshobson/agents@nextjs-app-router-patterns` — install with `npx skills add wshobson/agents@nextjs-app-router-patterns`
  - Why it may help: highest-install Next.js/App Router skill surfaced by `npx skills find "Next.js"`, relevant if the user wants deeper App Router review beyond this slice’s local component work.

## Files the planner should expect to touch

Most likely:
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`

Possible but optional:
- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/lib/admin-api.ts` (only if a missing frontend type turns up during implementation)

## Bottom line

S04 should be planned as **bounded console inspection work**, not new backend architecture. The route semantics are already shipped and typed; the missing piece is to make the **selected persisted request** clearly explain calibrated vs degraded vs rollout-disabled routing and its contributing evidence inside the existing **request detail + Observability** surfaces, then lock that behavior with the existing focused Vitest suites.
