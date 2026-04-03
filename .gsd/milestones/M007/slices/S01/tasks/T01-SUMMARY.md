---
id: T01
parent: S01
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/app/(console)/observability/page.tsx", "console/src/app/(console)/observability/page.test.tsx", "console/src/app/(console)/observability/observability-page.test.tsx", ".gsd/milestones/M007/slices/S01/tasks/T01-SUMMARY.md"]
key_decisions: ["Encoded the request-first operator-surface contract with DOM-order assertions in focused and integrated Observability tests instead of relying on copy-only checks."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Task-level verification passed: `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx` completed successfully with both files passing. Copy-presence verification passed via `rg -n "Selected request evidence first|Grounded follow-up guidance for the selected request|Inspect one persisted ledger row before reading tenant context" console/src/app/'(console)'/observability/page.tsx`. Slice-level verification was run and partially passed; the Observability files plus `ledger-request-detail` and `policy-page` passed, while unrelated existing failure remains in `src/components/policy/policy-form.test.tsx` due to `formatRouteScore` calling `toFixed` on undefined preview data."
completed_at: 2026-04-03T01:52:04.464Z
blocker_discovered: false
---

# T01: Reordered Observability so selected-request investigation leads the page and added hierarchy guardrails in focused tests.

> Reordered Observability so selected-request investigation leads the page and added hierarchy guardrails in focused tests.

## What Happened
---
id: T01
parent: S01
milestone: M007
key_files:
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - .gsd/milestones/M007/slices/S01/tasks/T01-SUMMARY.md
key_decisions:
  - Encoded the request-first operator-surface contract with DOM-order assertions in focused and integrated Observability tests instead of relying on copy-only checks.
duration: ""
verification_result: mixed
completed_at: 2026-04-03T01:52:04.465Z
blocker_discovered: false
---

# T01: Reordered Observability so selected-request investigation leads the page and added hierarchy guardrails in focused tests.

**Reordered Observability so selected-request investigation leads the page and added hierarchy guardrails in focused tests.**

## What Happened

Updated `console/src/app/(console)/observability/page.tsx` so the selected request investigation is the first major evidence section after filters, with recommendations, calibration/cache context, and dependency health rendered afterward as supporting context. Preserved the existing metadata-only wording and data seams, only adjusting the stale "above and below" phrasing after the reorder. Strengthened `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` to assert top-level section order, require the selected-request section to appear before supporting guidance, and reject dashboard-style drift.

## Verification

Task-level verification passed: `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx` completed successfully with both files passing. Copy-presence verification passed via `rg -n "Selected request evidence first|Grounded follow-up guidance for the selected request|Inspect one persisted ledger row before reading tenant context" console/src/app/'(console)'/observability/page.tsx`. Slice-level verification was run and partially passed; the Observability files plus `ledger-request-detail` and `policy-page` passed, while unrelated existing failure remains in `src/components/policy/policy-form.test.tsx` due to `formatRouteScore` calling `toFixed` on undefined preview data.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx` | 0 | ✅ pass | 1270ms |
| 2 | `rg -n "Selected request evidence first|Grounded follow-up guidance for the selected request|Inspect one persisted ledger row before reading tenant context" console/src/app/'(console)'/observability/page.tsx` | 0 | ✅ pass | 4800ms |
| 3 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 1 | ❌ fail | 1580ms |


## Deviations

None.

## Known Issues

`src/components/policy/policy-form.test.tsx` still fails in untouched code because `console/src/components/policy/policy-form.tsx` does not handle an undefined route score during preview rendering. This blocks the full slice verification command but does not affect the Observability task changes.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `.gsd/milestones/M007/slices/S01/tasks/T01-SUMMARY.md`


## Deviations
None.

## Known Issues
`src/components/policy/policy-form.test.tsx` still fails in untouched code because `console/src/components/policy/policy-form.tsx` does not handle an undefined route score during preview rendering. This blocks the full slice verification command but does not affect the Observability task changes.
