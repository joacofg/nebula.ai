---
id: S04
parent: M009
milestone: M009
provides:
  - Selected-request Observability/request-detail explanation of grounded, thin, stale, degraded, rollout-disabled, and unscored outcome-informed routing using existing persisted evidence seams.
  - Request-first UI/test guardrails ensuring calibration/cache/dependency cards remain supporting context for the same selected request rather than becoming a summary-first analytics surface.
  - Repaired observability regression fixtures aligned to the current governed UsageLedgerRecord shape so downstream integrated proof can rely on stable request-detail rendering.
requires:
  - slice: S02
    provides: Persisted request-level `route_signals` and outcome-grounded route factors on the usage-ledger row for the selected request.
  - slice: S03
    provides: Replay-aligned grounded/thin/stale/degraded vocabulary carried through `calibration_summary` for supporting operator context.
affects:
  - S05
key_files:
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - .gsd/PROJECT.md
key_decisions:
  - Normalize selected-request routing language around persisted request evidence first, with grounded/degraded/rollout-disabled/unscored request states derived from `route_signals`.
  - Keep tenant `calibration_summary`, cache, and dependency cards subordinate to the selected usage-ledger row so Observability stays request-first and avoids analytics-surface drift.
  - Repair stale page-level fixtures to the current `UsageLedgerRecord` contract instead of weakening request-detail behavior or broadening null-handling in production code.
patterns_established:
  - Request-first operator surfaces should explain routing from the selected usage-ledger row first, then layer supporting summary cards underneath using the same vocabulary family.
  - Console regression suites for Observability must track the current governed UsageLedgerRecord contract, including metadata suppression fields, to keep request-detail rendering honest and safe.
observability_surfaces:
  - console/src/components/ledger/ledger-request-detail.tsx selected-request explanation copy and state mapping
  - console/src/app/(console)/observability/page.tsx request-first composition with supporting calibration/cache/dependency context
  - Focused Vitest suites that fail on wording drift, hierarchy drift, or stale fixture crashes
drill_down_paths:
  - .gsd/milestones/M009/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M009/slices/S04/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-27T21:28:42.837Z
blocker_discovered: false
---

# S04: S04

**Completed request-first operator evidence for outcome-grounded routing by making selected-request Observability surfaces explain grounded, thin, stale, degraded, rollout-disabled, and unscored states from persisted request evidence without adding a new dashboard surface.**

## What Happened

S04 closed the operator-facing gap for M009 by aligning the existing request-first Observability surfaces to the outcome-grounded routing vocabulary introduced upstream. The selected request detail now explains routing investigation in one operator language anchored to persisted `route_signals`, distinguishing grounded, degraded, rollout-disabled, and unscored request states while keeping the selected usage-ledger row authoritative. Supporting tenant `calibration_summary` copy was aligned to the same grounded/thin/stale/degraded family, but remained explicitly subordinate so operators still reason from the exact request under investigation rather than from a summary card. The slice also hardened request-detail rendering against incomplete governed metadata fixtures by tolerating missing suppression arrays and optional summary fields. At the page level, the broader Observability regression coverage was repaired to use the current `UsageLedgerRecord` contract, including governed metadata suppression fields and grounded route evidence, then tightened to prove that the selected request section appears first and that calibration, cache, and dependency cards remain supporting context for the same investigation. No new production dashboard surface or analytics layer was introduced; the slice clarified existing inspection seams only, preserving the anti-sprawl boundary for downstream S05 integrated proof work.

## Verification

Re-ran all slice-plan verification checks and they passed. `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'` passed 15/15, proving grounded/degraded/rollout-disabled/unscored selected-request wording, grounded/thin/stale/degraded supporting calibration wording, request-first hierarchy, and safe rendering with incomplete request fixtures. `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'` passed 1/1, proving the Observability page still leads with the selected request section before follow-up context. `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'` passed 4/4, proving the broader page suite now uses the current UsageLedgerRecord shape, renders governed metadata suppression safely, and keeps supporting grounded/thin/stale/rollout-disabled cards subordinate to selected-request evidence. Together these focused console suites satisfy the slice’s integration proof level and expose failure visibility through test breakage rather than silent UI drift.

## Requirements Advanced

- R076 — Completed the operator-facing request-first evidence layer so selected requests now expose grounded/thin/stale/degraded outcome-informed routing states on existing Observability surfaces.
- R078 — Preserved the anti-sprawl boundary by clarifying existing request-first surfaces instead of introducing a new dashboard or analytics product.

## Requirements Validated

- R076 — Focused console suites passed for request detail and page-level Observability, proving operators can inspect grounded/thin/stale/degraded/rollout-disabled/unscored routing states on the selected request surfaces.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

This slice proves the request-first operator explanation through focused console tests rather than a live browser walkthrough; final end-to-end proof across public request, persisted evidence, replay parity, and operator inspection remains for S05.

## Follow-ups

S05 should stitch together one happy-path and one degraded-path walkthrough showing public request -> persisted route evidence -> replay parity -> request-first operator inspection, using the vocabulary and fixture guardrails locked in here.

## Files Created/Modified

- `console/src/components/ledger/ledger-request-detail.tsx` — Aligned selected-request and supporting-summary wording to grounded/thin/stale/degraded vocabulary while preserving selected-row authority and safe rendering for incomplete fixtures.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Added focused coverage for grounded/thin/stale/degraded supporting states, rollout-disabled/unscored request states, request-first hierarchy, and incomplete-fixture safety.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Repaired broader page fixtures to the current UsageLedgerRecord contract and tightened assertions that supporting cards remain subordinate to the selected request.
- `.gsd/PROJECT.md` — Refreshed project state to mark M009/S04 complete and summarize the new request-first operator evidence capabilities.
