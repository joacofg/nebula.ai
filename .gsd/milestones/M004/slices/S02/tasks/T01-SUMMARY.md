---
id: T01
parent: S02
milestone: M004
provides:
  - Shared fleet posture and bounded-action derivation for deployment metadata
key_files:
  - console/src/components/deployments/fleet-posture.ts
  - console/src/components/deployments/fleet-posture.test.ts
  - console/src/components/deployments/remote-action-card.tsx
  - console/src/components/deployments/remote-action-card.test.tsx
key_decisions:
  - Centralized bounded-action availability and deployment posture classification in a pure helper module so future summary and table surfaces reuse one fail-closed truth source.
patterns_established:
  - Derive hosted fleet scan-state from DeploymentRecord facts in pure functions first, then consume that seam from UI components and assert the seam separately in focused Vitest coverage.
observability_surfaces:
  - console/src/components/deployments/fleet-posture.ts
  - npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/remote-action-card.test.tsx
duration: 27m
verification_result: passed
completed_at: 2026-03-24T11:42:00-03:00
blocker_discovered: false
---

# T01: Extract shared fleet posture and bounded-action derivation

**Added a shared deployment posture helper and moved remote-action blocked-state semantics onto that single fail-closed seam.**

## What Happened

I added `console/src/components/deployments/fleet-posture.ts` as the shared pure derivation layer for S02. It classifies deployments into pending enrollment, linked, stale, offline, revoked, and unlinked posture states using only existing `DeploymentRecord` fields, and it also exposes bounded-action availability with shared disabled reasons for credential rotation.

I then removed the duplicated disabled-reason branching from `console/src/components/deployments/remote-action-card.tsx` and switched the card to consume `getBoundedActionAvailability()`. That keeps the current card wording intact while making later summary and table work consume the same truth source.

To lock the seam, I added focused helper tests covering mixed-fleet counts, pending-plus-null-freshness handling, distinct stale versus offline posture grouping, and fail-closed bounded-action behavior for pending, stale, offline, revoked, unlinked, and unsupported deployments. I also updated the remote-action card test to assert that the card renders the same shared blocked reasons supplied by the new helper.

## Verification

I ran the task-level Vitest command from the plan and confirmed both the helper tests and the existing card tests pass. I also ran the task-level grep check to confirm the expected bounded-action and posture wording is present in the deployments component area.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/remote-action-card.test.tsx` | 0 | ✅ pass | 1.20s |
| 2 | `rg -n "Rotation is blocked|Rotation is unavailable|pending enrollment|stale|offline" console/src/components/deployments` | 0 | ✅ pass | <0.1s |

## Diagnostics

Future agents can inspect `console/src/components/deployments/fleet-posture.ts` to see the canonical posture and bounded-action derivation logic. If regressions appear later in the slice, run `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/remote-action-card.test.tsx` first to isolate whether the failure is in the pure derivation seam or only in rendering.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/deployments/fleet-posture.ts` — New pure helper module for deployment posture classification, fleet counts, and bounded-action availability.
- `console/src/components/deployments/fleet-posture.test.ts` — Focused Vitest coverage for fleet posture derivation and fail-closed bounded-action behavior.
- `console/src/components/deployments/remote-action-card.tsx` — Updated to consume the shared bounded-action helper instead of duplicating blocked-state logic.
- `console/src/components/deployments/remote-action-card.test.tsx` — Updated to prove the card renders the shared helper’s blocked reasons.
