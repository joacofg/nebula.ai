---
estimated_steps: 47
estimated_files: 2
skills_used: []
---

# T01: Restructure policy preview into a baseline-versus-draft decision review

---
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

## Inputs

- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``

## Expected Output

- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``

## Verification

npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx

## Observability Impact

Focused form-level Vitest failures become the inspection surface for lost decision hierarchy, broken next-step cues, or preview-state regressions.
