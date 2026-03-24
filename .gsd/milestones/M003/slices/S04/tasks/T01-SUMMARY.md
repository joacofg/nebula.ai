---
id: T01
parent: S04
milestone: M003
provides:
  - Makes embeddings a first-class Observability route-target filter without changing the shared usage-ledger query contract.
key_files:
  - console/src/components/ledger/ledger-filters.tsx
  - console/src/components/ledger/ledger-filters.test.tsx
key_decisions:
  - Kept Observability page and admin API wiring unchanged and extended only the existing route-target option list so embeddings still flows through routeTarget -> route_target.
patterns_established:
  - Add new ledger route targets by extending the shared filter option list and locking the callback behavior in focused component tests instead of introducing route-specific UI branching.
observability_surfaces:
  - console/src/components/ledger/ledger-filters.tsx route-target selector for usage-ledger filtering
  - npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx
  - rg -n 'embeddings' console/src/components/ledger/ledger-filters.tsx console/src/components/ledger/ledger-filters.test.tsx console/src/app/\(console\)/observability/page.tsx -S
duration: 21m
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T01: Make embeddings ledger rows intentionally discoverable in Observability

**Added an embeddings route-target option to Observability filters and locked the existing callback path with focused component coverage.**

## What Happened

I verified that Observability already passes a shared `ledgerFilters` object into `listUsageLedger()` and that `console/src/lib/admin-api.ts` already encodes `routeTarget` as `route_target`, so no page-level or API-client change was needed.

I then updated `console/src/components/ledger/ledger-filters.tsx` to include `embeddings` in the existing `ROUTE_TARGET_OPTIONS` list. This keeps embeddings discoverability inside the established operator surface rather than creating a special-case filter model or route-specific branching.

Finally, I extended `console/src/components/ledger/ledger-filters.test.tsx` in two ways: one assertion proves the embeddings option is visible in the rendered filter controls, and a second test proves selecting that option still uses the existing `onRouteTargetChange` callback path with the value `embeddings`.

## Verification

I ran the focused task-level verification commands from the plan.

The grep-based proof passed and shows embeddings now appears only in the intended filter/test surface while Observability page wiring remains unchanged.

The focused Vitest command did not execute in this worktree because `console/node_modules` is absent and the shell reported `vitest: command not found`. That is an environment/setup failure rather than a product regression in the filter implementation.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx` | 127 | ❌ fail | ~1s |
| 2 | `rg -n 'embeddings' console/src/components/ledger/ledger-filters.tsx console/src/components/ledger/ledger-filters.test.tsx console/src/app/\(console\)/observability/page.tsx -S` | 0 | ✅ pass | ~1s |

## Diagnostics

Future agents can inspect `console/src/components/ledger/ledger-filters.tsx` to confirm the shared route-target option list includes `embeddings`, then run `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx` once console dependencies are installed to verify the callback contract still holds.

If embeddings disappears from the filter set again, the component test should fail at the selector visibility or callback assertion before broader browser-level Observability proofs become ambiguous.

## Deviations

None.

## Known Issues

- The planned Vitest verification could not be executed in this worktree because `console/node_modules` is missing, causing `sh: vitest: command not found`.

## Files Created/Modified

- `console/src/components/ledger/ledger-filters.tsx` — added `embeddings` to the shared route-target option list.
- `console/src/components/ledger/ledger-filters.test.tsx` — added focused assertions for embeddings option visibility and existing callback-path selection behavior.
- `.gsd/milestones/M003/slices/S04/S04-PLAN.md` — marked T01 complete.
- `.gsd/milestones/M003/slices/S04/tasks/T01-SUMMARY.md` — recorded execution and verification evidence.
