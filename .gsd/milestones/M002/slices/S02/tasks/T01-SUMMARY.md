---
id: T01
parent: S02
milestone: M002
provides:
  - Runtime-truth tenant guidance across the Tenants page shell and tenant editor drawer, plus focused regression coverage for the revised copy.
key_files:
  - console/src/app/(console)/tenants/page.tsx
  - console/src/app/(console)/tenants/page.test.tsx
  - console/src/components/tenants/tenant-editor-drawer.tsx
  - console/src/components/tenants/tenant-editor-drawer.test.tsx
  - console/src/components/tenants/tenant-table.test.tsx
key_decisions:
  - Anchored operator-facing tenant copy directly to docs/production-model.md so app/workload remain conceptual naming guidance and never appear as first-class runtime entities.
patterns_established:
  - Lock copy-heavy runtime-truth UI guidance with focused text assertions on both the page shell and the editing surface, plus a negative assertion against pseudo-entity drift in adjacent table semantics.
observability_surfaces:
  - Focused vitest assertions in console/src/app/(console)/tenants/page.test.tsx, console/src/components/tenants/tenant-editor-drawer.test.tsx, and console/src/components/tenants/tenant-table.test.tsx
duration: 25m
verification_result: passed
completed_at: 2026-03-23T21:03:40-03:00
blocker_discovered: false
---

# T01: Reframe tenant surfaces around runtime-truth app/workload guidance

**Reframed tenant page and drawer copy around tenants and API keys as the real runtime boundary, and added focused tests that guard against fake app/workload semantics.**

## What Happened

I first read the canonical runtime model in `docs/production-model.md` and the existing tenant page, drawer, and table surfaces to ground the copy changes in Nebula’s current enforcement model. Before implementation, I fixed the plan gap by adding an `## Observability Impact` section to `.gsd/milestones/M002/slices/S02/tasks/T01-PLAN.md` so future agents can see which UI signals and tests are supposed to expose regressions.

I then updated `console/src/app/(console)/tenants/page.tsx` so the header now states that tenants are the enforced runtime boundary, API keys segment callers, and app/workload names are conventions teams apply through tenant names, key names, or notes rather than first-class product objects. I also updated `console/src/components/tenants/tenant-editor-drawer.tsx` to remove the misleading “workspace” framing, describe tenant creation and updates in terms of real tenant boundaries, and explain that `metadata` is only for optional operator notes, ownership hints, or runbook context.

The local codebase differed slightly from the planner snapshot because `console/src/app/(console)/tenants/page.test.tsx` did not exist yet, so I created it as part of the task’s required verification work. I also extended `console/src/components/tenants/tenant-editor-drawer.test.tsx` to assert the new runtime-truth guidance and the absence of “workspace” language, and added a coherence guard to `console/src/components/tenants/tenant-table.test.tsx` to ensure no app/workload pseudo-entity columns appear.

## Verification

I ran the focused tenant-surface vitest suite required by the task plan and slice verification. The first run failed because the new page test over-mocked `@/lib/admin-session-provider` and removed `AdminSessionProvider`, which `renderWithProviders()` needs. I corrected that with a partial mock that preserves the provider export and reran the exact same command successfully.

Manual review also passed based on the rendered copy covered by the focused tests: the page header and drawer now explicitly describe tenants and API keys as the real boundaries while keeping app/workload guidance conceptual only.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx` | 1 | ❌ fail | 1.24s |
| 2 | `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx` | 0 | ✅ pass | 1.04s |

## Diagnostics

Inspect the runtime-truth guidance with the focused vitest files at `console/src/app/(console)/tenants/page.test.tsx`, `console/src/components/tenants/tenant-editor-drawer.test.tsx`, and `console/src/components/tenants/tenant-table.test.tsx`. If wording drifts, failures will identify whether the regression came from the page shell copy, the tenant drawer helper text, or adjacent table semantics.

## Deviations

The planner treated `console/src/app/(console)/tenants/page.test.tsx` as an existing verification surface, but the file was missing locally. I created it during execution so the task could meet the slice’s verification bar without broadening scope.

## Known Issues

None.

## Files Created/Modified

- `.gsd/milestones/M002/slices/S02/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section required by the pre-flight contract.
- `.gsd/milestones/M002/slices/S02/S02-PLAN.md` — marked T01 complete.
- `console/src/app/(console)/tenants/page.tsx` — rewrote tenant page header copy to teach the tenant/API-key runtime model without inventing app/workload objects.
- `console/src/app/(console)/tenants/page.test.tsx` — added focused coverage for the tenant page shell guidance.
- `console/src/components/tenants/tenant-editor-drawer.tsx` — replaced workspace framing with runtime-truth tenant guidance and metadata notes framing.
- `console/src/components/tenants/tenant-editor-drawer.test.tsx` — added assertions for tenant boundary guidance, metadata notes framing, and removal of workspace language.
- `console/src/components/tenants/tenant-table.test.tsx` — added a coherence assertion that the table does not grow app/workload pseudo-entity columns.
