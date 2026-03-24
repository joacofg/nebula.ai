---
id: T03
parent: S02
milestone: M004
provides:
  - Deployment inventory table scan-time posture and bounded-action legibility grounded in the shared fleet helper
key_files:
  - console/src/components/deployments/deployment-table.tsx
  - console/src/components/deployments/deployment-table.test.tsx
  - .gsd/milestones/M004/slices/S02/tasks/T03-PLAN.md
key_decisions:
  - Kept the table compact by adding a single posture column that composes existing status/freshness badges with helper-derived posture and bounded-action summaries instead of duplicating drawer detail.
patterns_established:
  - When a scan surface needs deployment state semantics, derive copy from `getDeploymentPostureDetails()` and assert the rendered row cues separately from the pure helper tests so semantic drift and rendering drift fail in different places.
observability_surfaces:
  - console/src/components/deployments/deployment-table.tsx
  - console/src/components/deployments/deployment-table.test.tsx
  - npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts
  - rg -n "Pending enrollment|Revoked|Unlinked|Stale|Offline|blocked|available" console/src/components/deployments/deployment-table.tsx console/src/components/deployments/deployment-table.test.tsx
duration: 34m
verification_result: passed
completed_at: 2026-03-24T11:48:00-03:00
blocker_discovered: false
---

# T03: Make deployment scan-time state legible in the inventory table

**Added helper-driven posture cues to the deployments table so operators can scan pending, linked, stale/offline, revoked/unlinked, and bounded-action states without opening the drawer.**

## What Happened

I upgraded `console/src/components/deployments/deployment-table.tsx` from an inventory-only table into a compact scan surface with a dedicated Posture column. Each row now reuses the existing `DeploymentStatusBadge`, conditionally keeps the `FreshnessBadge` for active deployments, and renders helper-derived posture labels/details plus a short bounded-action summary (`Rotation available`, `Rotation blocked`, or `Rotation unavailable`) from `getDeploymentPostureDetails()`.

That keeps the row semantics aligned with the shared derivation seam introduced in T01 and the hosted trust-boundary language introduced in T02, while avoiding a noisy dashboard-style expansion. I kept the existing click-to-select behavior intact and did not change the page-level drawer workflow because the table can derive everything it needs locally from the existing `DeploymentRecord` input.

I expanded `console/src/components/deployments/deployment-table.test.tsx` to cover the required scan-time states: active linked rows, pending enrollment, revoked, unlinked, stale visibility, offline visibility, bounded-action blocked/unavailable messaging, preserved row selection, and the empty state. During verification I hit a test-only issue where some states intentionally render both a badge label and a posture heading with the same text; I verified the UI was correct, then updated those assertions to accept multiple matches rather than weakening the component.

Per the pre-flight requirement, I also added an `## Observability Impact` section to `.gsd/milestones/M004/slices/S02/tasks/T03-PLAN.md` so future agents can see which row-level signals and test seams this task changes.

## Verification

I ran the slice verification Vitest command covering the helper seam, fleet summary, deployment table, remote-action card, and hosted-contract wording, and all five test files passed. I also ran the task-level `rg` check from the plan to confirm the new table and tests explicitly include the required pending/revoked/unlinked/stale/offline/blocked/available vocabulary.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts` | 0 | ✅ pass | 0.83s |
| 2 | `rg -n "Pending enrollment|Revoked|Unlinked|Stale|Offline|blocked|available" console/src/components/deployments/deployment-table.tsx console/src/components/deployments/deployment-table.test.tsx` | 0 | ✅ pass | <0.1s |

## Diagnostics

Future agents can inspect `console/src/components/deployments/deployment-table.tsx` to see the exact scan-time composition of badge reuse plus helper-derived posture/action summaries, and `console/src/components/deployments/deployment-table.test.tsx` to determine whether a regression is in row rendering rather than the underlying derivation seam. If later slice work breaks posture wording or action-state cues, rerun the table-specific suite together with `fleet-posture.test.ts` first to separate helper drift from presentation drift.

## Deviations

None.

## Known Issues

LSP diagnostics were unavailable in this worktree, so verification relied on direct file inspection plus the focused Vitest suite.

## Files Created/Modified

- `console/src/components/deployments/deployment-table.tsx` — Added a compact posture column with shared status/freshness badges, helper-derived row explanations, and bounded-action summaries while preserving click selection.
- `console/src/components/deployments/deployment-table.test.tsx` — Expanded coverage for pending, linked, revoked, unlinked, stale/offline, blocked/unavailable, selection, and empty-state behavior.
- `.gsd/milestones/M004/slices/S02/tasks/T03-PLAN.md` — Added the missing Observability Impact section required by the task pre-flight check.
