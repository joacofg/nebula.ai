---
id: S03
parent: M010
milestone: M010
provides:
  - Operator-visible dependency degradation and recovery truth on existing console surfaces for use in S04 recovery proof.
  - A shared console resilience typing path that preserves runtime health metadata across proxy and UI seams.
requires:
  - slice: S01
    provides: Dependency-state vocabulary and degraded-mode invariants used by console operator surfaces.
  - slice: S02
    provides: Outage-path evidence and degraded runtime behavior examples reused in request-first observability proofs.
affects:
  []
key_files:
  - console/src/lib/admin-api.ts
  - console/src/components/health/runtime-health-cards.tsx
  - console/src/components/health/runtime-health-cards.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/e2e/observability.spec.ts
  - console/src/app/api/runtime/health/route.ts
key_decisions:
  - Kept console Observability and runtime health surfaces on the shared `RuntimeHealthDependency` contract so additive resilience metadata survives the typing seam end to end.
  - Preserved the existing request-first operator workflow and dependency-health section instead of introducing a separate resilience dashboard.
patterns_established:
  - Use additive optional fields on shared console admin/runtime contracts to preserve backward compatibility while exposing richer resilience metadata.
  - Prove operator resilience visibility with focused component and page tests that exercise fail-closed, degraded-serving, and recovering examples on existing surfaces.
observability_surfaces:
  - Console runtime health dependency cards
  - Console Observability page dependency-health section
  - Shared runtime health proxy typing through console admin/runtime API seams
drill_down_paths:
  - .gsd/milestones/M010/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M010/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-23T20:12:57.949Z
blocker_discovered: false
---

# S03: S03

**Existing console runtime health and Observability surfaces now preserve and show dependency-specific degradation and recovery metadata so operators can identify failed dependencies, serving impact, and recovery status without a new dashboard.**

## What Happened

S03 closed the operator-visible resilience leg by carrying the additive runtime health dependency contract through the console typing seam and into the existing request-first observability workflow. T01 expanded the shared console runtime health contract and updated runtime health cards to render dependency class, lifecycle state, serving effect, reason code, enabled/recovering flags, and failure/recovery timestamps while staying backward-compatible with legacy payloads. T02 then aligned the Observability page to the same shared dependency contract instead of narrowing it locally, and refreshed the existing page tests to prove operators can inspect governance fail-closed, semantic-cache degraded-serving, and recovering premium-provider examples on the current surfaces rather than a separate resilience dashboard. Together the slice keeps the selected request evidence hierarchy intact while making dependency identity, degraded mode, and recovery truth visible on existing operator surfaces.

## Verification

Verified the slice-required focused console tests now pass from the project root using closeout-safe execution: `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx` passed with 1/1 files and 3/3 tests; `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' 'src/app/(console)/observability/observability-page.test.tsx'` passed with 2/2 files and 5/5 tests. These checks prove the existing runtime health cards and request-first Observability page preserve and display resilience metadata across dependency outage and recovery examples. The refreshed Playwright proof file exists but was not part of the slice-plan verification commands and remains blocked for execution by an unrelated pre-existing console build/type issue outside this slice.

## Requirements Advanced

- R086 — advanced the milestone resilience proof by making operator-facing console truth surfaces show current dependency degradation and recovery state.
- R088 — completed operator-visible failure and recovery visibility on existing health and observability surfaces without adding a new dashboard.

## Requirements Validated

- R088 — Passing focused Vitest coverage for runtime health cards and Observability page seams proves operators can see dependency-specific degradation, serving impact, and recovery metadata on existing console surfaces.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

Playwright proof coverage was refreshed in `console/e2e/observability.spec.ts`, but execution remains outside the slice-plan verification set and is currently blocked by an unrelated pre-existing console build/type issue elsewhere in the worktree.

## Known Limitations

This slice validates operator-visible resilience truth through focused Vitest coverage of existing console surfaces; it does not prove a full compiled-browser Playwright run in the current worktree because of an unrelated console build/type blocker outside S03.

## Follow-ups

S04 should reuse these operator-visible surfaces during recovery/runbook proof and, if needed, clear the unrelated console build/type blocker before relying on Playwright-based browser evidence.

## Files Created/Modified

- `console/src/lib/admin-api.ts` — Expanded the shared runtime health dependency contract with optional resilience metadata fields for console consumers.
- `console/src/components/health/runtime-health-cards.tsx` — Rendered dependency class, lifecycle state, serving effect, reason code, recovering/enabled flags, and failure/recovery timestamps on existing runtime health cards.
- `console/src/components/health/runtime-health-cards.test.tsx` — Added focused component coverage for serving-critical, serving-optional, recovering, and legacy-compatible dependency payloads.
- `console/src/app/(console)/observability/page.tsx` — Aligned Observability page runtime-health typing to the shared richer dependency contract.
- `console/src/app/(console)/observability/page.test.tsx` — Proved the request-first Observability page still exposes resilience metadata on existing surfaces.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Added/updated request-first page assertions for governance fail-closed, semantic-cache degraded-serving, and recovery examples.
- `console/e2e/observability.spec.ts` — Refreshed browser proof stubs and assertions to reflect richer runtime health resilience metadata on existing surfaces.
- `console/src/app/api/runtime/health/route.ts` — Maintained the runtime health proxy path that preserves additive dependency metadata for console consumption.
