---
id: T02
parent: S01
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/components/ledger/ledger-request-detail.tsx", "console/src/components/ledger/ledger-request-detail.test.tsx", "console/src/components/policy/policy-form.tsx", "console/src/components/policy/policy-form.test.tsx", "console/src/components/policy/policy-page.test.tsx", ".gsd/milestones/M007/slices/S01/tasks/T02-SUMMARY.md"]
key_decisions: ["Preserved request detail as the authoritative persisted evidence seam and encoded preview-before-save boundaries with focused negative assertions instead of adding new product framing."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Focused Vitest verification passed for the request-detail and policy preview seams, and the task-plan grep check confirmed the bounded authority/preview headings remain in source. The policy preview seam that previously failed in T01 now renders rollout-disabled parity rows cleanly because undefined route scores no longer crash formatting."
completed_at: 2026-04-03T01:57:49.096Z
blocker_discovered: false
---

# T02: Locked request-detail authority copy and hardened policy preview guardrails with focused boundary tests.

> Locked request-detail authority copy and hardened policy preview guardrails with focused boundary tests.

## What Happened
---
id: T02
parent: S01
milestone: M007
key_files:
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/milestones/M007/slices/S01/tasks/T02-SUMMARY.md
key_decisions:
  - Preserved request detail as the authoritative persisted evidence seam and encoded preview-before-save boundaries with focused negative assertions instead of adding new product framing.
duration: ""
verification_result: passed
completed_at: 2026-04-03T01:57:49.097Z
blocker_discovered: false
---

# T02: Locked request-detail authority copy and hardened policy preview guardrails with focused boundary tests.

**Locked request-detail authority copy and hardened policy preview guardrails with focused boundary tests.**

## What Happened

Updated `console/src/components/ledger/ledger-request-detail.tsx` so the lead copy explicitly identifies the persisted ledger row as the authoritative evidence record for the selected request ID, while leaving calibration, budget, and routing sections as supporting context. Strengthened `console/src/components/ledger/ledger-request-detail.test.tsx` with authority and bounded-surface assertions, then hardened `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` so preview-before-save remains explicit across happy-path, zero-row, and error states and rejects dashboard / routing-studio / analytics-product drift. While verifying the planned seams, fixed the existing local preview crash in `console/src/components/policy/policy-form.tsx` by making `formatRouteScore` handle undefined route scores as well as null, which keeps rollout-disabled parity rows renderable.

## Verification

Focused Vitest verification passed for the request-detail and policy preview seams, and the task-plan grep check confirmed the bounded authority/preview headings remain in source. The policy preview seam that previously failed in T01 now renders rollout-disabled parity rows cleanly because undefined route scores no longer crash formatting.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1650ms |
| 2 | `rg -n "Preview before save|Save remains explicit|Request detail|Calibration evidence|Routing inspection" console/src/components/ledger/ledger-request-detail.tsx console/src/components/policy/policy-form.tsx` | 0 | ✅ pass | 3500ms |


## Deviations

The task plan referenced `console/src/app/(console)/policy/page.test.tsx`, but this worktree uses `console/src/components/policy/policy-page.test.tsx` for the page-level policy seam. I adapted to the real file rather than creating a parallel test path.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `.gsd/milestones/M007/slices/S01/tasks/T02-SUMMARY.md`


## Deviations
The task plan referenced `console/src/app/(console)/policy/page.test.tsx`, but this worktree uses `console/src/components/policy/policy-page.test.tsx` for the page-level policy seam. I adapted to the real file rather than creating a parallel test path.

## Known Issues
None.
