# S04 Research — Rework policy preview into a comparison-and-decision flow

## Summary

S04 is targeted console work, not a backend expansion slice. The bounded replay contract already exists and matches the current product constraints: `POST /v1/admin/tenants/{tenant_id}/policy/simulate` returns baseline-versus-simulated route/status/policy/cost deltas, a bounded changed-request sample, replay notes, and calibration summary without widening into analytics payloads. The main gap is in `console/src/components/policy/policy-form.tsx`, which still renders preview results as a correct but fairly flat evidence block rather than a stronger decision-review flow that makes baseline vs draft, operator consequence, and save / don’t-save next step obvious at a glance.

Relevant requirements to target in planning:
- **R052** — policy preview must support a clear save / don’t-save workflow.
- **R053** — supporting recommendation/calibration/cache/dependency context must stay subordinate to the selected request or decision surface.
- **R054** — the next action should be legible without reading surrounding prose first.
- **R055** — avoid dashboard, routing-studio, or analytics-product drift.

The existing split is good for execution: `console/src/app/(console)/policy/page.tsx` owns query/mutation orchestration and tenant selection; `console/src/components/policy/policy-form.tsx` owns the full comparison UI and validation logic; `console/src/components/policy/policy-page.test.tsx` and `console/src/components/policy/policy-form.test.tsx` already encode the bounded-product language and anti-drift checks.

Per the loaded `react-best-practices` skill, keep the work local to existing components and avoid speculative abstraction. This slice should reuse the current page/component split, preserve explicit save mutation boundaries, and prefer render-time derivation of comparison summaries over effect-driven state.

## Recommendation

Plan S04 as primarily **console composition + test tightening** with backend reuse.

Build/prove in this order:
1. **Form-level decision flow in `policy-form.tsx`**
   - Strengthen the comparison surface so operators can scan baseline vs draft outcomes and know whether they should save, keep iterating, or stop.
   - Keep preview read-only and explicit that save remains separate.
   - If adding new derived UI states, compute them from `simulationResult` during render/useMemo rather than introducing new persisted client state.
2. **Page-level framing in `app/(console)/policy/page.tsx`**
   - Keep this thin. Only adjust top-level framing if the form-level decision flow creates a mismatch with the current page intro or mutation lifecycle.
   - Preserve the current mutation contract: preview via `simulateTenantPolicy`, save via `updateTenantPolicy`, clear preview on tenant change and on save success.
3. **Focused Vitest updates**
   - Use `policy-form.test.tsx` for most decision-flow assertions.
   - Use `policy-page.test.tsx` only for orchestration, tenant-level framing, and ensuring preview remains non-saving.

Unless implementation reveals a real gap, do **not** widen the backend response model. The current `PolicySimulationResponse` already contains the needed primitives to derive better decision UI locally.

## Implementation Landscape

### Files that matter

- `console/src/app/(console)/policy/page.tsx`
  - Single policy route.
  - Owns tenant selection, React Query reads, save mutation, simulate mutation, and `latestSimulation` state.
  - Clears simulation state on tenant switch and after successful save.
  - Hard-codes preview request bounds today: `limit: 50`, `changed_sample_limit: 5`.
  - Natural seam for page framing only; avoid pushing decision logic down here.

- `console/src/components/policy/policy-form.tsx`
  - Main slice file.
  - Owns form state, validation, preview panel, runtime-enforced controls, soft-budget advisory section, and deferred capture section.
  - Existing helper seams:
    - `toFormState()` / `toPolicyPayload()` for state ↔ payload conversion.
    - `formatUsd()`, `formatRouteScore()`, `formatRoutingState()`.
    - `renderChangedRequestSummary()` and `renderChangedRequestParity()` for preview rows.
  - Existing preview section already shows:
    - summary cards: evaluated rows, changed routes, newly denied, premium cost delta
    - bounded changed request sample
    - replay notes
    - zero-result and error states
  - This is the right place to add stronger decision-review structure, derived verdict language, and clearer baseline-vs-draft comparison hierarchy.

- `console/src/components/policy/policy-form.test.tsx`
  - Best place to lock the new decision semantics.
  - Already verifies:
    - preview is distinct from save
    - preview aggregate cards and changed request sample render
    - empty/error states
    - runtime-enforced controls remain separate from advisory/deferred sections
    - anti-drift negative assertions against dashboard/routing-studio/analytics wording
  - Natural place to add assertions for decision outcome framing and next-action cues.

- `console/src/components/policy/policy-page.test.tsx`
  - Integration test for `PolicyPage` orchestration.
  - Already verifies `simulateTenantPolicy` payload shape, non-saving preview, tenant intro copy, and zero/error states.
  - Keep it focused on mutation wiring and top-level copy, not every form detail.

- `console/src/lib/admin-api.ts`
  - Frontend contract already includes all simulation fields currently used in the page and tests.
  - No obvious missing type for S04 at research time.

- `src/nebula/models/governance.py`
  - Canonical backend response model for simulation.
  - Bounded by design: changed sample, summary counts, window, replay notes, calibration summary.
  - `changed_sample_limit` server max is 50.

- `src/nebula/services/policy_simulation_service.py`
  - Replays oldest-first from newest-first store rows for deterministic windows/samples.
  - Change detection counts route/status/policy/cost deltas; not route-target-only.
  - Always returns three approximation notes today.
  - Existing response is deliberately signal-driven and metadata-only.

- `tests/test_governance_api.py`
  - Confirms the bounded replay/admin contract.
  - Important behavior for UI interpretation:
    - simulation can produce `simulated_route_target = "denied"`
    - `simulated_route_mode`, calibrated/degraded flags, and route score can be `null`
    - `calibrated_routing_disabled` maps to explicit unscored/rollout-disabled semantics

### Natural seams for tasking

1. **Decision-review UI task**
   - `console/src/components/policy/policy-form.tsx`
   - `console/src/components/policy/policy-form.test.tsx`
   - Highest-value unit. Most requirement movement comes from this seam.

2. **Page orchestration / framing task**
   - `console/src/app/(console)/policy/page.tsx`
   - `console/src/components/policy/policy-page.test.tsx`
   - Only if needed after the form flow settles.

3. **Backend contract task**
   - Probably unnecessary for this slice.
   - Only open if the planner can name a specific missing field that cannot be derived client-side.

### Existing behavior/constraints to preserve

- Preview and save are separate mutations in `page.tsx`; preserve this split.
- `latestSimulation` resets on tenant change and save success; keep that behavior unless the slice explicitly needs stale-preview messaging.
- Validation for allowlist, cache threshold, and cache max age is duplicated for save and preview in `policy-form.tsx`; any rework must keep both paths fail-safe.
- `formatRoutingState()` already handles rollout-disabled/unscored cases; reuse it instead of inventing parallel rendering logic.
- Negative anti-drift assertions already exist across policy tests; keep or strengthen them rather than replacing them with softer copy-only checks.

## Verification

Primary slice verification should stay focused and local:

```bash
npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
```

If implementation touches shared policy wording or neighboring operator framing, expand to the established M007 policy/observability bundle:

```bash
npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
```

Optional backend confirmation only if the executor changes admin contracts:

```bash
./.venv/bin/pytest tests/test_governance_api.py -k "simulation or policy_options" -x
./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x
```

## Skill Discovery

Installed relevant skill already present in the environment:
- `react-best-practices` — directly relevant for keeping this React/Next work local, render-derived, and non-speculative.

Promising external skills discovered but **not installed**:
- `wshobson/agents@nextjs-app-router-patterns` — install with `npx skills add wshobson/agents@nextjs-app-router-patterns`
- `wshobson/agents@fastapi-templates` — install with `npx skills add wshobson/agents@fastapi-templates`

These are only relevant if execution unexpectedly widens into App Router structure changes or backend API reshaping. Based on current research, S04 should not need them.

## Risks / Watchpoints

- The easiest failure mode is copy-only improvement that leaves the operator still scanning a flat preview block. The slice needs stronger structure and next-action readability, not just better sentences.
- A second failure mode is overcorrecting into dashboard semantics (aggregate verdict panels, analytics language, or broad posture framing). Keep the unit of review as **current baseline vs current draft over bounded recent persisted traffic**.
- Be careful with request rows where route parity is `null`/rollout-disabled. S01 already fixed undefined route-score rendering; S04 should continue to treat those as first-class comparison output, not missing data.
- No TS LSP was available in this environment. Execution should rely on focused Vitest feedback rather than planning around semantic editor tooling.
