---
id: S04
parent: M006
milestone: M006
provides:
  - Request-level calibrated routing inspection from persisted route_signals, including explicit calibrated, degraded, rollout-disabled, and unscored states in ledger request detail.
  - A selected-request-first Observability composition that keeps tenant calibration, recommendation, cache, and dependency summaries subordinate to persisted request evidence.
  - Focused console regression coverage for duplicate-label-safe request-detail and Observability inspection flows.
requires:
  - slice: S01
    provides: Persisted calibrated/degraded route_signals vocabulary and additive score fields for routed requests.
  - slice: S02
    provides: Tenant-scoped calibration summary state and reason fields derived from existing usage-ledger metadata.
  - slice: S03
    provides: Runtime/simulation parity semantics for calibrated, degraded, and rollout-disabled routing states that the operator surfaces now explain.
affects:
  - S05
key_files:
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/app/(console)/observability/page.test.tsx
key_decisions:
  - Reused the existing calibrated/degraded/rollout-disabled/unscored vocabulary from earlier M006 work instead of inventing a new explanation language for request inspection.
  - Kept the selected persisted ledger row authoritative in Observability and treated calibration, recommendation, cache, and dependency cards as supporting context rather than a replacement evidence surface.
  - Allowed duplicate routing/calibration labels when they are intentionally repeated across bounded cards and locked that behavior with scoped test assertions rather than forcing page-wide uniqueness.
patterns_established:
  - Use the selected persisted ledger row as the authoritative operator proof surface, and compose broader tenant/runtime summaries around it as supporting context rather than peer authority.
  - When the same calibration or routing label appears intentionally in multiple bounded cards, scope UI assertions with section-level queries instead of forbidding duplicates.
observability_surfaces:
  - console/src/components/ledger/ledger-request-detail.tsx request-detail routing inspection from persisted route_signals
  - console/src/app/(console)/observability/page.tsx selected-request-first Observability framing with supporting calibration/cache/recommendation/dependency context
  - npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx
drill_down_paths:
  - .gsd/milestones/M006/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S04/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-02T04:16:31.157Z
blocker_discovered: false
---

# S04: Operator inspection surfaces

**Existing request-detail and Observability surfaces now let operators inspect calibrated-versus-heuristic routing state and supporting evidence from the selected persisted ledger row without adding a new API or analytics-style view.**

## What Happened

S04 closed the operator-surface gap for M006 by making existing request-detail and Observability views legible for calibrated routing without widening Nebula into a new inspector or analytics product. In the ledger request-detail panel, the slice added bounded routing inspection derived directly from the selected persisted row’s route_signals: route mode, calibrated/degraded markers, route score, and additive score components render when present, while rollout-disabled and other null-mode rows stay explicit instead of collapsing into generic missing data. On the Observability page, the slice rewrote the page framing so operators start with one selected request ID and its persisted ledger row, then use tenant calibration readiness, recommendations, cache posture, and dependency health as supporting context for that same routed-request investigation. Focused tests were updated to reflect the real UI contract: duplicate labels and request IDs are intentional across bounded cards, so assertions now scope to the relevant section rather than assuming whole-page uniqueness.

## Verification

Re-ran the exact slice-plan verification command in the assembled worktree: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx`. It passed cleanly with 3/3 files and 20/20 tests green, confirming the request-detail routing inspection states and the Observability selected-request-first framing work together. Also checked LSP diagnostics for the touched TypeScript files, but no language server was active in this environment.

## Requirements Advanced

- R039 — S04 made calibrated routing state and contributing evidence directly inspectable in existing operator surfaces, which strengthens the operator-visible proof needed for outcome-aware routing without widening scope into a separate analytics product.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

The slice is console-only and depends on persisted route_signals and calibration-summary metadata already assembled by S01–S03; it does not itself prove the full runtime-to-replay integrated story. TypeScript LSP diagnostics were unavailable in this worktree because no language server was active.

## Follow-ups

S05 should verify the full M006 proof path end to end: calibrated live routing evidence, replay parity evidence, degraded/rollout-disabled semantics, and these request-first operator inspection surfaces together in one integrated walkthrough.

## Files Created/Modified

- `console/src/components/ledger/ledger-request-detail.tsx` — Added bounded routing-state inspection derived from persisted route_signals, including explicit calibrated, degraded, rollout-disabled, and unscored request states plus additive score components in request detail.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Locked the request-detail routing inspection contract with focused cases for calibrated additive-score rows, degraded rows, rollout-disabled rows, unscored partial-signal rows, and intentional duplicate labels.
- `console/src/app/(console)/observability/page.tsx` — Reframed Observability around a selected-request-first flow and bounded the surrounding calibration, recommendation, cache, and dependency sections as supporting context for the same request investigation.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Added scoped Observability rendering assertions that tolerate intentional duplicate labels across request detail and supporting cards while preserving request-primary framing.
- `console/src/app/(console)/observability/page.test.tsx` — Added page-level framing assertions for selected-request-first evidence and supporting runtime context wording.
