# S04: Rework policy preview into a comparison-and-decision flow

**Goal:** Turn policy preview into a comparison-and-decision flow that makes baseline versus draft evidence, operator consequence, and save / don’t-save next steps legible without widening the page into analytics or dashboard product scope.
**Demo:** After this: After this: an operator can use policy preview to compare baseline versus simulated outcomes and decide whether to save without the page feeling like a blended editor and analytics surface.

## Tasks
- [x] **T01: Restructured the policy preview into a decision-first baseline-versus-draft review with explicit next-step guidance and bounded evidence.** — ---
estimated_steps: 5
estimated_files: 2
skills_used:
  - react-best-practices
---

# T01: Restructure policy preview into a baseline-versus-draft decision review

**Slice:** S04 — Rework policy preview into a comparison-and-decision flow
**Milestone:** M007

## Description

Rework the preview section inside `PolicyForm` so the operator sees one bounded decision surface instead of a flat evidence block. The task should derive a clear comparison hierarchy from `simulationResult` at render time, make baseline-versus-draft consequence legible, and surface explicit next-step cues such as save, keep iterating, or no change without adding persisted client state or widening the payload contract.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `simulationResult` from `simulateTenantPolicy` | Keep preview in explicit failed-preview state and preserve save as a separate action | Keep loading state scoped to preview only; no save-side mutation should fire | Render bounded fallback messaging rather than crashing on missing/null comparison fields |

## Load Profile

- **Shared resources**: React render tree for the policy form and bounded simulation payload already fetched by the page
- **Per-operation cost**: Render-only derivation over one bounded `simulationResult` object and up to five changed-request rows
- **10x breakpoint**: UI readability degrades before computation cost matters; avoid adding extra local state/effects that amplify rerenders

## Negative Tests

- **Malformed inputs**: changed-request rows with null route-mode / route-score fields still render as first-class comparison output
- **Error paths**: preview loading, preview failure, zero-row replay, and unchanged replay all keep explicit non-saving semantics
- **Boundary conditions**: zero changed requests, zero returned rows, positive deltas without route changes, and changed rows with rollout-disabled parity remain legible

## Steps

1. Inspect the existing preview section in `console/src/components/policy/policy-form.tsx` and identify where baseline-versus-draft hierarchy, operator consequence, and next-action cues can be derived directly from `simulationResult` without adding new stored client state.
2. Refactor the preview UI so it leads with a comparison-and-decision summary, keeps bounded changed-request evidence and replay notes subordinate, and preserves explicit save separation plus current validation rules.
3. Add or tighten helper logic only where needed for render-time derivation of decision summaries or labels, reusing existing formatting/parity helpers rather than inventing parallel logic.
4. Expand `console/src/components/policy/policy-form.test.tsx` to lock the new decision-review hierarchy, explicit next-step wording, unchanged/empty/error states, rollout-disabled parity handling, and negative assertions against dashboard/routing-studio/analytics drift.
5. Run the focused Vitest file and adjust until the new decision-review surface is stable and mechanically proven.

## Must-Haves

- [ ] Preview remains read-only and explicitly separate from save.
- [ ] Baseline-versus-draft comparison and next-action cues are legible before the changed-request sample.
- [ ] Supporting evidence stays bounded and subordinate to the main decision surface.
- [ ] Existing null/unscored routing parity cases remain renderable.

## Verification

- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`
- Preview tests assert explicit save/don’t-save semantics, bounded comparison wording, and anti-drift negatives without relying on prose-only inspection.

## Observability Impact

- Signals added/changed: Focused UI assertions for decision hierarchy, next-step cues, and failure/empty/unchanged preview states
- How a future agent inspects this: `src/components/policy/policy-form.test.tsx`
- Failure state exposed: Broken save/preview separation, lost comparison hierarchy, or dashboard-drift wording shows up as narrow Vitest failures

## Inputs

- `console/src/components/policy/policy-form.tsx` — existing preview composition, formatting helpers, and validation behavior
- `console/src/components/policy/policy-form.test.tsx` — existing preview, anti-drift, and runtime-control assertions

## Expected Output

- `console/src/components/policy/policy-form.tsx` — decision-review preview flow with baseline-versus-draft hierarchy and explicit next-step cues
- `console/src/components/policy/policy-form.test.tsx` — focused assertions covering the new comparison-and-decision behavior

  - Estimate: 75m
  - Files: console/src/components/policy/policy-form.tsx, console/src/components/policy/policy-form.test.tsx
  - Verify: npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx
- [x] **T02: Locked the policy page into a compare-before-save flow with baseline-versus-draft framing and page-level reset tests.** — ---
estimated_steps: 4
estimated_files: 2
skills_used:
  - react-best-practices
---

# T02: Align page framing and mutation orchestration with the new decision flow

**Slice:** S04 — Rework policy preview into a comparison-and-decision flow
**Milestone:** M007

## Description

Update the policy page wrapper only where the new form-level decision flow exposes framing or orchestration gaps. Preserve the current preview-vs-save mutation split, tenant-level reset behavior, and bounded simulate request shape, while tightening page-level copy and tests so the whole surface reads as compare → decide → save instead of a blended editor or analytics page.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `simulateTenantPolicy` / `updateTenantPolicy` mutations in `console/src/app/(console)/policy/page.tsx` | Keep preview and save errors isolated to their existing surfaces; do not let preview imply persistence | Preserve pending-state separation so preview latency does not block unrelated framing or fake a saved state | Fail through existing page/form error handling; do not widen contract assumptions beyond the current bounded response |

## Load Profile

- **Shared resources**: React Query cache entries for tenant list, policy, options, and simulation state within the policy page
- **Per-operation cost**: One tenant-policy query, one options query, and bounded preview/save mutations already present
- **10x breakpoint**: Repeated tenant switching or preview calls mainly risks stale UI messaging; keep resets explicit and local

## Negative Tests

- **Malformed inputs**: tenant switch with stale preview state does not leak old comparison evidence into the new tenant context
- **Error paths**: preview mutation failure remains non-saving and save mutation success clears obsolete preview evidence
- **Boundary conditions**: zero-result preview, unchanged preview, and null parity rows remain correctly framed at the page level

## Steps

1. Review `console/src/app/(console)/policy/page.tsx` against the new form-level decision review and adjust only the page intro, handoff props, or state-reset semantics needed to keep compare-before-save framing coherent.
2. Preserve the existing bounded simulate payload (`limit: 50`, `changed_sample_limit: 5`), tenant-change reset, and save-success reset behavior unless a real mismatch with the decision flow appears.
3. Expand `console/src/components/policy/policy-page.test.tsx` to prove the page-level framing, non-saving preview contract, reset semantics, and anti-drift boundary still hold with the new comparison-and-decision UI.
4. Run the focused policy Vitest bundle and adjust until the form/page integration is stable.

## Must-Haves

- [ ] Preview and save remain separate mutations with explicit non-saving preview semantics.
- [ ] Tenant change and save success clear obsolete preview evidence.
- [ ] Page-level copy reinforces compare-before-save framing without adding dashboard or analytics language.
- [ ] Focused integration tests cover the real page entrypoint and bounded simulate payload.

## Verification

- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
- Page tests assert preview payload shape, explicit non-saving semantics, tenant-level framing, and reset behavior after save/tenant change.

## Observability Impact

- Signals added/changed: Focused page-level Vitest assertions for mutation separation, reset semantics, and bounded framing
- How a future agent inspects this: `src/components/policy/policy-page.test.tsx`
- Failure state exposed: Stale preview carryover, incorrect mutation wiring, or page-level scope drift appears as narrow integration-test failures

## Inputs

- `console/src/app/(console)/policy/page.tsx` — current tenant selection, simulation/save mutations, and reset behavior
- `console/src/components/policy/policy-page.test.tsx` — existing page-level policy framing and orchestration assertions
- `console/src/components/policy/policy-form.tsx` — task-one comparison-and-decision UI that the page composes

## Expected Output

- `console/src/app/(console)/policy/page.tsx` — page framing and orchestration aligned to compare-before-save flow
- `console/src/components/policy/policy-page.test.tsx` — integration assertions for page-level decision-flow composition and reset semantics

  - Estimate: 45m
  - Files: console/src/app/(console)/policy/page.tsx, console/src/components/policy/policy-page.test.tsx
  - Verify: npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
