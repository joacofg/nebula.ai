---
id: T02
parent: S02
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/components/policy/policy-form.tsx", "console/src/components/policy/policy-form.test.tsx", "console/src/components/policy/policy-page.test.tsx", "console/src/app/(console)/observability/page.tsx", "console/src/app/(console)/observability/page.test.tsx", "console/src/app/(console)/observability/observability-page.test.tsx", "console/src/components/ledger/ledger-request-detail.tsx", "console/src/components/ledger/ledger-request-detail.test.tsx", ".gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md"]
key_decisions: ["Kept policy preview comparison-first by tightening existing copy and tests around baseline-vs-draft evidence rather than adding new preview surfaces or aggregates.", "Kept Observability request-first by making supporting recommendation, calibration, cache, and dependency sections explicitly subordinate to the selected ledger row in both UI copy and scoped Vitest assertions."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the slice verification command from the task plan and confirmed all targeted console tests passed: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx"
completed_at: 2026-04-03T02:19:16.763Z
blocker_discovered: false
---

# T02: Tightened policy preview comparison wording and request-first Observability seams with scoped console tests.

> Tightened policy preview comparison wording and request-first Observability seams with scoped console tests.

## What Happened
---
id: T02
parent: S02
milestone: M007
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - .gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md
key_decisions:
  - Kept policy preview comparison-first by tightening existing copy and tests around baseline-vs-draft evidence rather than adding new preview surfaces or aggregates.
  - Kept Observability request-first by making supporting recommendation, calibration, cache, and dependency sections explicitly subordinate to the selected ledger row in both UI copy and scoped Vitest assertions.
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:19:16.764Z
blocker_discovered: false
---

# T02: Tightened policy preview comparison wording and request-first Observability seams with scoped console tests.

**Tightened policy preview comparison wording and request-first Observability seams with scoped console tests.**

## What Happened

Updated the console policy editor so preview copy reads as a baseline-vs-draft comparison over recent persisted requests, with bounded changed-request wording and explicit save separation. Tightened Observability supporting-context copy so recommendation, calibration, cache, and dependency cards point back to the selected request investigation while keeping LedgerRequestDetail authoritative. Strengthened the focused Vitest coverage with DOM-order and scoped assertions so future drift is localized to preview framing, request-detail hierarchy, or supporting-card wording.

## Verification

Ran the slice verification command from the task plan and confirmed all targeted console tests passed: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1330ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `.gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
