---
id: T03
parent: S03
milestone: M006
provides: []
requires: []
affects: []
key_files: ["console/src/components/policy/policy-form.tsx", "console/src/components/policy/policy-page.test.tsx", ".gsd/milestones/M006/slices/S03/tasks/T03-SUMMARY.md"]
key_decisions: ["Kept routing parity rendering local to the existing changed-request card and reused rollout-disabled vocabulary instead of widening the preview into a new routing-inspection surface."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused task-plan verification command `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`, and the policy preview Vitest suite passed with the new routing parity assertions."
completed_at: 2026-04-02T03:55:21.230Z
blocker_discovered: false
---

# T03: Added compact routing parity cues to policy preview changed-request cards, including explicit rollout-disabled rendering when calibrated routing is gated.

> Added compact routing parity cues to policy preview changed-request cards, including explicit rollout-disabled rendering when calibrated routing is gated.

## What Happened
---
id: T03
parent: S03
milestone: M006
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/milestones/M006/slices/S03/tasks/T03-SUMMARY.md
key_decisions:
  - Kept routing parity rendering local to the existing changed-request card and reused rollout-disabled vocabulary instead of widening the preview into a new routing-inspection surface.
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:55:21.231Z
blocker_discovered: false
---

# T03: Added compact routing parity cues to policy preview changed-request cards, including explicit rollout-disabled rendering when calibrated routing is gated.

**Added compact routing parity cues to policy preview changed-request cards, including explicit rollout-disabled rendering when calibrated routing is gated.**

## What Happened

Updated console/src/components/policy/policy-form.tsx so each changed-request sample in the existing policy preview now renders a bounded routing parity line. The line compares baseline and simulated route mode semantics using the established vocabulary, includes calibrated/degraded markers and route score when present, and renders null-mode calibrated-routing-disabled rows as an intentional rollout-disabled state instead of missing data. Extended console/src/components/policy/policy-page.test.tsx to lock both calibrated-to-degraded and degraded-to-rollout-disabled preview rendering without widening the UI into a new routing dashboard.

## Verification

Ran the focused task-plan verification command `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`, and the policy preview Vitest suite passed with the new routing parity assertions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1050ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `.gsd/milestones/M006/slices/S03/tasks/T03-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
