---
id: S04
parent: M007
milestone: M007
provides:
  - A compare-before-save policy preview flow where operators can read baseline-versus-draft consequences first, inspect bounded supporting replay evidence second, and trust that preview state is cleared when tenant context or saved policy changes.
requires:
  - slice: S01
    provides: The explicit operator-surface role contract that defines policy preview as a save/don’t-save decision-review surface rather than a blended admin panel.
  - slice: S02
    provides: The bounded policy-options and simulation seams needed to keep comparison evidence narrow and runtime-aligned while rewriting the preview hierarchy.
affects:
  - S05
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/app/(console)/policy/page.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/PROJECT.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Derived preview decision summaries at render time from `simulationResult` instead of adding client state or widening the simulation payload.
  - Kept the existing preview/save mutation split and reset wiring because the page orchestration already matched the compare-before-save contract.
  - Kept changed-request evidence and replay notes explicitly subordinate to the decision summary so the page does not drift into dashboard or analytics framing.
patterns_established:
  - For policy-preview work, derive baseline-vs-draft decision summaries from the bounded simulation payload at render time instead of storing parallel UI state.
  - When the page-level contract is already correct, tighten route-entry framing and tests rather than adding new orchestration state.
  - Use focused negative assertions against terms like dashboard, routing studio, and analytics product to lock page identity in operator-surface refinement work.
observability_surfaces:
  - Focused Vitest coverage in `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` now acts as the durable diagnostic surface for preview/save separation, bounded replay framing, and stale-preview reset behavior.
drill_down_paths:
  - .gsd/milestones/M007/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S04/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:49:48.794Z
blocker_discovered: false
---

# S04: Rework policy preview into a comparison-and-decision flow

**Reworked the policy editor into a compare-before-save decision flow that leads with baseline-versus-draft consequences, keeps supporting replay evidence bounded, and clears stale preview state on tenant changes or save.**

## What Happened

S04 tightened Nebula’s policy surface into an explicit decision-review flow rather than a blended editor-plus-analytics page. In `console/src/components/policy/policy-form.tsx`, the preview section now derives its decision summary directly from `simulationResult` at render time instead of introducing new client state or widening the admin payload contract. The preview leads with one bounded baseline-versus-draft summary card, explicit preview-only/save-stays-separate wording, consequence text, and next-step guidance for changed, unchanged, and no-comparison-window states. Supporting replay evidence remains subordinate: the bounded changed-request sample stays capped to the existing replay limits, replay notes remain secondary, and null or rollout-disabled routing parity still renders without crashing.

At the page entrypoint in `console/src/app/(console)/policy/page.tsx`, the existing mutation wiring already matched the intended contract, so the slice preserved it rather than adding orchestration state. Preview and save remain separate mutations, the simulate request stays bounded at `limit: 50` and `changed_sample_limit: 5`, tenant changes clear stale preview evidence, and successful saves clear the last preview before policy refetch. Page copy was tightened so the overall route reads as load baseline → compare draft → decide whether to save.

Focused Vitest coverage now locks the decision hierarchy and anti-drift boundary at both levels. `policy-form.test.tsx` proves decision-first ordering, explicit non-saving semantics, bounded changed-request framing, unchanged/empty/loading/error states, malformed/null routing parity rendering, and negative assertions against dashboard/routing-studio/analytics language. `policy-page.test.tsx` proves the real route entrypoint keeps the bounded simulate payload, preserves preview/save separation, clears stale preview evidence on tenant switch and save success, and keeps the compare-before-save framing intact.

## Verification

Ran the slice verification bundle defined in the plan: `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`. It passed with 2 test files and 16 assertions green. This reverified the assembled compare-before-save flow, bounded simulate payload shape, explicit preview-only wording, null and rollout-disabled routing parity rendering, and reset behavior after tenant switches and successful saves.

## Requirements Advanced

- R049 — Strengthened the bounded operator-surface contract by making policy preview an explicit decision-review surface with anti-drift tests against dashboard/analytics framing, which advances the milestone’s scope-discipline proof ahead of integrated close-out.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

This slice is intentionally artifact-driven console work; it does not add new backend simulation fields or runtime behavior. TypeScript LSP diagnostics were unavailable in the environment during task execution, so focused Vitest coverage remains the authoritative verification surface for the changed console seams.

## Follow-ups

S05 should assemble this policy decision surface with the selected-request-first Observability flow into one integrated operator proof, making the handoff between request investigation and compare-before-save policy action explicit without duplicating contract semantics.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx` — Reworked the preview section into a decision-first baseline-versus-draft summary with explicit next-step wording and subordinate bounded replay evidence.
- `console/src/components/policy/policy-form.test.tsx` — Locked the preview hierarchy, explicit non-saving semantics, null/rollout-disabled parity rendering, and anti-drift wording with focused Vitest coverage.
- `console/src/app/(console)/policy/page.tsx` — Kept preview/save mutation separation intact while tightening page framing around load baseline → compare draft → decide whether to save.
- `console/src/components/policy/policy-page.test.tsx` — Verified the real route entrypoint preserves bounded simulate payloads and clears stale preview evidence on tenant switch and save success.
- `.gsd/PROJECT.md` — Updated current-state project context to reflect that M007 S04 is complete and policy preview now ships as a compare-before-save decision surface.
- `.gsd/KNOWLEDGE.md` — Recorded the policy preview decision-flow pattern so future slices preserve render-time derivation and reset verification at the page entrypoint.
