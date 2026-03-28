---
id: T03
parent: S02
milestone: M005
provides: []
requires: []
affects: []
key_files: ["console/src/lib/admin-api.ts", "console/src/app/(console)/policy/page.tsx", "console/src/components/policy/policy-form.tsx", "console/src/components/policy/policy-form.test.tsx", "console/src/components/policy/policy-page.test.tsx", ".gsd/milestones/M005/slices/S02/tasks/T03-SUMMARY.md"]
key_decisions: ["Kept simulation mutation state owned by the page while the form stays responsible for draft serialization and preview rendering, so preview and save remain separate operator actions.", "Rendered changed-request samples for any outcome delta (route, terminal status, policy outcome, or projected cost) to stay faithful to the backend replay contract instead of implying previews only matter when route targets flip."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` twice. The first run failed because the page test assumed browser `localStorage.clear()` support even though the current harness provides session state through `AdminSessionProvider`; after updating the tests to inject `adminKey` through `renderWithProviders`, the second run passed all ten focused tests, confirming draft simulation payloads, non-saving preview behavior, explicit empty/error preview messaging, and grouped policy editor rendering."
completed_at: 2026-03-28T03:17:16.891Z
blocker_discovered: false
---

# T03: Added preview-before-save policy simulation to the console policy editor with explicit non-save feedback and changed-request replay summaries.

> Added preview-before-save policy simulation to the console policy editor with explicit non-save feedback and changed-request replay summaries.

## What Happened
---
id: T03
parent: S02
milestone: M005
key_files:
  - console/src/lib/admin-api.ts
  - console/src/app/(console)/policy/page.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/milestones/M005/slices/S02/tasks/T03-SUMMARY.md
key_decisions:
  - Kept simulation mutation state owned by the page while the form stays responsible for draft serialization and preview rendering, so preview and save remain separate operator actions.
  - Rendered changed-request samples for any outcome delta (route, terminal status, policy outcome, or projected cost) to stay faithful to the backend replay contract instead of implying previews only matter when route targets flip.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T03:17:16.891Z
blocker_discovered: false
---

# T03: Added preview-before-save policy simulation to the console policy editor with explicit non-save feedback and changed-request replay summaries.

**Added preview-before-save policy simulation to the console policy editor with explicit non-save feedback and changed-request replay summaries.**

## What Happened

Extended the console admin client with typed policy simulation request/response models and a helper for the new tenant policy simulation endpoint. Updated the policy page to own a dedicated simulation mutation alongside the existing save mutation, resetting stale preview state on tenant changes and after successful saves so replay output never implies persistence. Expanded the policy form with a separate preview action that reuses the existing draft-to-policy serialization, shows loading/error/empty states inline, renders aggregate replay counters and premium cost deltas, and presents a compact changed-request sample plus approximation notes while clearly stating that the preview did not save the policy. Added focused Vitest coverage proving draft values are sent to simulation, preview output renders without invoking save, save remains explicit, and empty/error preview states are legible.

## Verification

Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` twice. The first run failed because the page test assumed browser `localStorage.clear()` support even though the current harness provides session state through `AdminSessionProvider`; after updating the tests to inject `adminKey` through `renderWithProviders`, the second run passed all ten focused tests, confirming draft simulation payloads, non-saving preview behavior, explicit empty/error preview messaging, and grouped policy editor rendering.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 1 | ❌ fail | 1250ms |
| 2 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 881ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/lib/admin-api.ts`
- `console/src/app/(console)/policy/page.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `.gsd/milestones/M005/slices/S02/tasks/T03-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
