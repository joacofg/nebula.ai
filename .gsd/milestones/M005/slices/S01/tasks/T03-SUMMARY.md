---
id: T03
parent: S01
milestone: M005
provides: []
requires: []
affects: []
key_files: ["console/src/lib/admin-api.ts", "console/src/components/ledger/ledger-request-detail.tsx", "console/src/components/ledger/ledger-request-detail.test.tsx", "docs/route-decision-vocabulary.md", ".gsd/milestones/M005/slices/S01/tasks/T03-SUMMARY.md"]
key_decisions: ["Rendered route_signals through explicit plain-language DetailRow mappings instead of exposing raw JSON blobs so operator inspection stays stable as the backend vocabulary evolves."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Verified the drawer behavior with `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`, which passed with all five tests green, including the new Route Decision coverage. Verified the documentation artifact exists with `test -f docs/route-decision-vocabulary.md`. Also ran `npm --prefix console run build`, which completed successfully and confirmed the console compiles cleanly after the type and UI changes."
completed_at: 2026-03-28T02:53:50.699Z
blocker_discovered: false
---

# T03: Added route-signal visibility to the observability drawer and documented the stable route-decision vocabulary.

> Added route-signal visibility to the observability drawer and documented the stable route-decision vocabulary.

## What Happened
---
id: T03
parent: S01
milestone: M005
key_files:
  - console/src/lib/admin-api.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - docs/route-decision-vocabulary.md
  - .gsd/milestones/M005/slices/S01/tasks/T03-SUMMARY.md
key_decisions:
  - Rendered route_signals through explicit plain-language DetailRow mappings instead of exposing raw JSON blobs so operator inspection stays stable as the backend vocabulary evolves.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T02:53:50.700Z
blocker_discovered: false
---

# T03: Added route-signal visibility to the observability drawer and documented the stable route-decision vocabulary.

**Added route-signal visibility to the observability drawer and documented the stable route-decision vocabulary.**

## What Happened

Extended the console admin usage-ledger contract with `route_signals`, added a conditional "Route Decision" section to the request-detail drawer that maps known signal keys to plain-language labels, and kept the section absent when no signals are present. Added focused Vitest coverage for both the positive and negative render paths and wrote `docs/route-decision-vocabulary.md` to document the signal keys, score semantics, and stable reason-code vocabulary confirmed from the router implementation. During verification, I fixed a JSX corruption introduced during editing, corrected the boolean signal label helper to return `yes`/`no` as intended, and adjusted one existing test assertion to match the component’s real structure where the request ID is intentionally shown both in the header and in the details grid.

## Verification

Verified the drawer behavior with `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`, which passed with all five tests green, including the new Route Decision coverage. Verified the documentation artifact exists with `test -f docs/route-decision-vocabulary.md`. Also ran `npm --prefix console run build`, which completed successfully and confirmed the console compiles cleanly after the type and UI changes.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 1 | ❌ fail | 763ms |
| 2 | `npm --prefix console run build` | 1 | ❌ fail | 0ms |
| 3 | `grep -n "route_signals" console/src/lib/admin-api.ts && grep -n "Route Decision" console/src/components/ledger/ledger-request-detail.tsx && grep -n "Token count" console/src/components/ledger/ledger-request-detail.tsx && test -f docs/route-decision-vocabulary.md && grep -n "token_complexity" docs/route-decision-vocabulary.md && grep -n "budget_proximity" docs/route-decision-vocabulary.md && grep -n "complexity_tier" docs/route-decision-vocabulary.md && wc -l docs/route-decision-vocabulary.md` | 1 | ❌ fail | 0ms |
| 4 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 1 | ❌ fail | 648ms |
| 5 | `npm --prefix console run build` | 0 | ✅ pass | 0ms |
| 6 | `grep -n "route_signals" console/src/lib/admin-api.ts && grep -n "Route Decision" console/src/components/ledger/ledger-request-detail.tsx && grep -n "Token count" console/src/components/ledger/ledger-request-detail.tsx && test -f docs/route-decision-vocabulary.md && grep -n "token_complexity" docs/route-decision-vocabulary.md && grep -n "budget_proximity" docs/route-decision-vocabulary.md && grep -n "complexity_tier" docs/route-decision-vocabulary.md && wc -l docs/route-decision-vocabulary.md` | 0 | ✅ pass | 0ms |
| 7 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 0 | ✅ pass | 600ms |
| 8 | `test -f docs/route-decision-vocabulary.md` | 0 | ✅ pass | 0ms |


## Deviations

The existing drawer renders the request ID twice—once in the header and once in the detail grid—so I updated the pre-existing assertion to use `getAllByText(...).toHaveLength(2)` instead of a singular text lookup. No slice-level replan was needed.

## Known Issues

None.

## Files Created/Modified

- `console/src/lib/admin-api.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `docs/route-decision-vocabulary.md`
- `.gsd/milestones/M005/slices/S01/tasks/T03-SUMMARY.md`


## Deviations
The existing drawer renders the request ID twice—once in the header and once in the detail grid—so I updated the pre-existing assertion to use `getAllByText(...).toHaveLength(2)` instead of a singular text lookup. No slice-level replan was needed.

## Known Issues
None.
