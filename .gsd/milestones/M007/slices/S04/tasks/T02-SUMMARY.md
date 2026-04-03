---
id: T02
parent: S04
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/app/(console)/policy/page.tsx", "console/src/components/policy/policy-page.test.tsx", ".gsd/milestones/M007/slices/S04/tasks/T02-SUMMARY.md"]
key_decisions: ["Kept the existing preview/save mutation split and reset wiring because the page orchestration already matched the decision-flow contract; tightened the page entrypoint with copy and tests instead of adding new state.", "Extended page-level coverage at the real route entrypoint to prove stale preview evidence clears on tenant switch and save success rather than widening the component contract."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused Vitest bundle twice with npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx. Both runs passed. The suite proved the bounded simulate payload, explicit non-saving preview semantics, and reset behavior after save and tenant change at the real page entrypoint."
completed_at: 2026-04-03T02:47:36.314Z
blocker_discovered: false
---

# T02: Locked the policy page into a compare-before-save flow with baseline-versus-draft framing and page-level reset tests.

> Locked the policy page into a compare-before-save flow with baseline-versus-draft framing and page-level reset tests.

## What Happened
---
id: T02
parent: S04
milestone: M007
key_files:
  - console/src/app/(console)/policy/page.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/milestones/M007/slices/S04/tasks/T02-SUMMARY.md
key_decisions:
  - Kept the existing preview/save mutation split and reset wiring because the page orchestration already matched the decision-flow contract; tightened the page entrypoint with copy and tests instead of adding new state.
  - Extended page-level coverage at the real route entrypoint to prove stale preview evidence clears on tenant switch and save success rather than widening the component contract.
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:47:36.315Z
blocker_discovered: false
---

# T02: Locked the policy page into a compare-before-save flow with baseline-versus-draft framing and page-level reset tests.

**Locked the policy page into a compare-before-save flow with baseline-versus-draft framing and page-level reset tests.**

## What Happened

Reviewed console/src/app/(console)/policy/page.tsx against the new form-level decision flow and found the existing orchestration already preserved the required split: preview and save are separate mutations, the simulate payload remains bounded at limit 50 with changed_sample_limit 5, tenant changes clear stale preview state, and save success clears the last simulation before refetching policy data. Kept that runtime wiring intact and tightened only the page intro copy so the route entrypoint explicitly reads as current baseline versus candidate draft comparison before save. Expanded console/src/components/policy/policy-page.test.tsx to cover unchanged previews staying explicitly non-saving, preview errors remaining isolated from save, save success clearing stale preview evidence, and tenant switching dropping prior comparison evidence before the next tenant policy loads. The test fixture now includes two tenants so stale-preview carryover is exercised directly rather than assumed.

## Verification

Ran the focused Vitest bundle twice with npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx. Both runs passed. The suite proved the bounded simulate payload, explicit non-saving preview semantics, and reset behavior after save and tenant change at the real page entrypoint.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1420ms |
| 2 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1480ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/app/(console)/policy/page.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `.gsd/milestones/M007/slices/S04/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
