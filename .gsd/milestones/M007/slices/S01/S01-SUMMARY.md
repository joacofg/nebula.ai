---
id: S01
parent: M007
milestone: M007
provides:
  - An explicit operator-surface model for M007: Observability leads with selected-request investigation, request detail is authoritative persisted evidence, and policy preview is replay-before-save decision review.
  - A reusable test guardrail pattern that catches page-role drift through section order and negative boundary assertions.
  - Stable rendering of preview parity rows even when route score is absent, which keeps later policy-preview work testable.
requires:
  []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/PROJECT.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Encoded the request-first operator-surface contract with DOM-order assertions in focused and integrated Observability tests instead of relying on copy-only checks.
  - Preserved request detail as the authoritative persisted evidence seam and encoded preview-before-save boundaries with focused negative assertions instead of adding new product framing.
  - Handled undefined preview route scores in `formatRouteScore` so rollout-disabled parity rows remain renderable during policy preview verification.
patterns_established:
  - Use DOM-order assertions plus scoped negative wording checks to lock page identity and evidence hierarchy, not just headline presence.
  - Treat the selected persisted ledger row as the lead evidence object; calibration, cache, recommendation, budget, and dependency surfaces may explain it but must stay visibly secondary.
  - Keep policy preview read-only and comparison-oriented until save is explicitly chosen, and render rollout-disabled or unscored parity states as first-class preview output rather than missing data.
observability_surfaces:
  - Focused Vitest coverage for Observability section order and subordinate framing.
  - Focused Vitest coverage for request-detail authority and bounded supporting interpretation.
  - Focused Vitest coverage for policy preview-before-save semantics and rollout-disabled parity rendering.
drill_down_paths:
  - .gsd/milestones/M007/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S01/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:00:04.231Z
blocker_discovered: false
---

# S01: Define page roles and evidence boundaries

**Locked Nebula’s operator-surface role contract so Observability is request-investigation-first, request detail remains the authoritative persisted evidence seam, and policy preview stays explicitly preview-before-save.**

## What Happened

S01 turned the M007 product thesis into an explicit operator-surface contract instead of leaving page identity implicit in copy. Observability now leads with the selected-request investigation section immediately after filters, and its supporting recommendation, calibration, cache, and dependency sections are framed as subordinate context for the same request-level investigation. `LedgerRequestDetail` now states plainly that the persisted ledger row is the authoritative evidence record for the selected request ID, with calibration, budget, and routing explanation panels kept as supporting interpretation rather than a replacement evidence surface. On the policy side, preview remains explicitly a replay-before-save comparison surface, with guardrails that reject dashboard, routing-studio, and analytics-product framing. While verifying that seam, the slice fixed an existing preview crash by making route-score formatting tolerate undefined preview values, which keeps rollout-disabled parity rows renderable instead of failing the page. The lasting output of the slice is not only the copy and ordering changes but the focused test pattern that locks section order, authority hierarchy, and negative boundary language across the three operator surfaces.

## Verification

Slice-level verification passed with `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` (5 files, 32 tests). The run confirmed Observability section order, request-detail authority copy and bounded interpretation, policy preview-before-save semantics, negative assertions against dashboard/routing-studio/analytics drift, and the route-score formatting fix that keeps rollout-disabled parity rows renderable.

## Requirements Advanced

- R044 — S01 materially strengthens the operator-decision clarity milestone by defining one explicit evidence hierarchy across Observability, request detail, and policy preview without widening scope into a dashboard or analytics surface.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

T02 adapted the page-level policy seam to the real test path `console/src/components/policy/policy-page.test.tsx` instead of the plan’s outdated `console/src/app/(console)/policy/page.test.tsx`. No product-scope deviation was introduced.

## Known Limitations

This slice defines role boundaries and test guardrails but does not yet simplify the underlying supporting-context density on Observability or restructure the policy workflow itself. Recommendations, calibration, cache, and dependency sections still coexist on the page; later slices need to refine how those supporting seams read without breaking the request-first contract established here.

## Follow-ups

S02 should tighten only the supporting evidence seams needed by this contract: request-investigation-first Observability is already set, so later work should feed clearer secondary context into that structure rather than reshuffling page identity again. S03 and S04 should preserve the explicit role split established here when reworking investigation and policy-preview flows.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx` — Reordered the page so selected-request investigation leads after filters and supporting context remains explicitly subordinate.
- `console/src/app/(console)/observability/page.test.tsx` — Locked focused Observability hierarchy assertions around request-first framing, subordinate supporting context, and no dashboard drift.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Locked integrated Observability section order, scoped supporting context assertions, and duplicate-label-safe request-first inspection coverage.
- `console/src/components/ledger/ledger-request-detail.tsx` — Tightened request-detail lead copy so the persisted ledger row is explicitly the authoritative evidence seam.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Added authority, bounded-surface, calibrated/degraded/rollout-disabled, and budget evidence assertions for request detail.
- `console/src/components/policy/policy-form.tsx` — Fixed preview rendering so undefined route scores no longer crash parity rows and kept preview-before-save framing explicit.
- `console/src/components/policy/policy-form.test.tsx` — Added preview-before-save guardrails, bounded negative assertions, and runtime-control boundary coverage.
- `console/src/components/policy/policy-page.test.tsx` — Verified page-level policy preview framing, changed-request parity rows, and explicit non-saving semantics.
- `.gsd/PROJECT.md` — Updated project current-state summary to reflect the completed M007/S01 operator-surface contract.
- `.gsd/KNOWLEDGE.md` — Recorded the new page-identity testing pattern for future slices.
