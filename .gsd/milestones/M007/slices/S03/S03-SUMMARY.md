---
id: S03
parent: M007
milestone: M007
provides:
  - A selected-request-first Observability investigation flow with clear subordinate supporting context and bounded request-selection cues that downstream policy-preview work can build on.
requires:
  - slice: S01
    provides: The explicit operator-surface role contract that made selected-request evidence primary and kept request detail authoritative.
  - slice: S02
    provides: Truthful supporting seams for policy options, bounded preview comparison data, and subordinate Observability supporting cards that S03 could recompose without widening scope.
affects:
  - S04
  - S05
key_files:
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/ledger/ledger-table.tsx
  - console/src/components/ledger/ledger-table.test.tsx
  - .gsd/PROJECT.md
key_decisions:
  - Grouped calibration, recommendations, cache posture, and dependency health under a policy-preview follow-up track so Observability reads as one request-led investigation instead of parallel dashboard cards.
  - Kept `LedgerRequestDetail` unchanged as the authoritative persisted-evidence seam and fixed hierarchy drift through page composition and scoped tests rather than widening shared contracts.
  - Strengthened request selection inside `LedgerTable` with explicit selector semantics and bounded copy (`aria-selected`, pressed button state, `Current investigation`) instead of widening the table into a second detail surface.
patterns_established:
  - For page-identity work in Observability, lead with one selected persisted request and treat all other cards as supporting context tied to that same investigation.
  - Lock operator-surface hierarchy with DOM-order and scoped `within(...)` assertions rather than copy-only tests, especially when duplicate request IDs or labels are expected across bounded cards.
  - When request selection needs to feel stronger, improve the bounded `LedgerTable` selector seam rather than adding another explainer layer above the authoritative request detail.
observability_surfaces:
  - Focused Vitest assertions now expose hierarchy drift, duplicate-label scoping mistakes, and selection-affordance regressions in `src/app/(console)/observability/page.test.tsx`, `src/app/(console)/observability/observability-page.test.tsx`, and `src/components/ledger/ledger-table.test.tsx`.
  - The page itself now exposes a clearer investigation signal: one selected request leads, with policy-preview follow-up cues and supporting runtime-context cards rendered in a subordinate column.
drill_down_paths:
  - .gsd/milestones/M007/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:37:40.383Z
blocker_discovered: false
---

# S03: Rework Observability around a primary investigation flow

**Reworked Observability so one selected request is the clear primary investigation object, with request detail authoritative and all supporting cards framed as follow-up context toward policy preview.**

## What Happened

S03 assembled the Observability page around one request-led investigation flow instead of a set of parallel dashboard cards. T01 recomposed `console/src/app/(console)/observability/page.tsx` so operators first encounter a selected persisted ledger row, then read recommendations, calibration evidence, cache posture, and dependency health as subordinate context for that same request and its next likely action. The page now explicitly treats policy preview as the follow-up comparison surface rather than letting supporting cards read like separate authorities. `LedgerRequestDetail` was intentionally kept stable as the authoritative persisted-evidence seam.

T02 strengthened the selector seam without widening scope. `console/src/components/ledger/ledger-table.tsx` now makes the active request obvious through bounded row affordances: `aria-selected`, a pressed request button, a `Current investigation` badge, and short supporting copy that promotes a row into the primary detail view. Unselected rows keep a lighter `Select request` cue so the table remains a bounded request selector rather than becoming a second detail surface or a broader explorer.

Across both tasks, the slice locked the new hierarchy with focused Vitest coverage instead of relying on prose-only expectations. The tests now assert DOM order, scoped hierarchy, duplicate-label/request-ID handling, selection semantics, and negative guards against dashboard, routing-studio, or analytics-product drift. The resulting page reads as one investigation with one next-step column rather than a collection of loosely related proof surfaces.

## Verification

Ran the full slice-level focused Vitest suite defined by the plan: `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx src/components/ledger/ledger-table.test.tsx`. All 5 test files passed (24/24 tests). This revalidated the selected-request-first page composition, request-detail authority, supporting-card hierarchy, policy-preview follow-up cues, dependency-health support role, and strengthened ledger-table selection affordances.

## Requirements Advanced

- R049 — Further reinforced the no-dashboard/no-analytics-sprawl boundary in operator surfaces by restructuring Observability around one bounded request investigation instead of widening it into a broader explorer.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

Observability is still an inspection surface only. Operators are pointed toward policy preview for comparison work, but S03 does not yet rework the policy-preview page itself into the full comparison-and-decision flow planned for S04. The page also remains intentionally tenant-scoped and bounded; it does not become a broader analytics explorer or multi-request investigation workspace.

## Follow-ups

S04 should preserve the new request-led hierarchy by making policy preview feel like the natural next step from the selected-request investigation, not a separate analytics/editor hybrid. If future Observability refinements need stronger cues, continue to extend the bounded `LedgerTable` selector seam instead of adding page-level explainers or duplicating request detail.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx` — Recomposed Observability around a selected-request-first investigation flow with supporting context grouped into a policy-preview follow-up column.
- `console/src/app/(console)/observability/page.test.tsx` — Locked focused page-level order, selected-request-first framing, and anti-drift assertions.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Added integrated hierarchy and scoped supporting-card assertions for the reworked investigation flow.
- `console/src/components/ledger/ledger-table.tsx` — Strengthened bounded selected-row affordances with explicit selector semantics and current-investigation cues.
- `console/src/components/ledger/ledger-table.test.tsx` — Proved selected and unselected row semantics without weakening bounded-selector behavior.
- `.gsd/PROJECT.md` — Updated current project state to reflect M007/S03 completion and the new Observability investigation flow.
