---
id: T02
parent: S02
milestone: M004
provides:
  - Deployments-page fleet posture summary surface grounded in the shared hosted contract
key_files:
  - console/src/components/deployments/fleet-posture-summary.tsx
  - console/src/components/deployments/fleet-posture-summary.test.tsx
  - console/src/app/(console)/deployments/page.tsx
key_decisions:
  - Render hosted-contract claims as discrete summary paragraphs so trust-boundary wording stays inspectable and testable while remaining sourced from the shared seam.
patterns_established:
  - Feed page-level fleet UI from the shared posture helper and assert summary rendering separately from the pure derivation seam so count regressions and wording drift fail in different tests.
observability_surfaces:
  - console/src/components/deployments/fleet-posture-summary.tsx
  - npm --prefix console run test -- --run src/components/deployments/fleet-posture-summary.test.tsx src/lib/hosted-contract.test.ts
  - npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts
duration: 33m
verification_result: passed
completed_at: 2026-03-24T11:45:00-03:00
blocker_discovered: false
---

# T02: Add the deployments fleet posture summary surface

**Added a real deployments-page fleet posture summary that surfaces helper-derived counts and shared trust-boundary wording above the inventory table.**

## What Happened

I added `console/src/components/deployments/fleet-posture-summary.tsx` as the new page-entry summary surface for hosted fleet posture. It consumes `summarizeFleetPosture()` directly, renders compact summary cards for linked/current, pending enrollment, stale-or-offline visibility, and bounded-action-blocked deployments, and keeps the numbers visually stable with tabular numerals.

To preserve the trust boundary, the summary reuses wording from `console/src/lib/hosted-contract.ts` instead of inventing new authority-leaning copy. I rendered the shared descriptive claims and operator guidance as discrete paragraphs and callouts so both operators and tests can inspect the exact contract-backed language without ambiguity.

I then wired the component into `console/src/app/(console)/deployments/page.tsx` above the deployment table while preserving the existing React Query fetch, selection state, drawer behavior, token reveal flow, and revoke/unlink mutations. During verification I caught and fixed a JSX nesting issue in the page composition before finishing.

I also added `console/src/components/deployments/fleet-posture-summary.test.tsx` to cover mixed-fleet counts, empty-state rendering, all-pending fleets, and trust-boundary-aware copy. One test initially expected the wrong linked count for the mixed-fleet fixture; I verified the helper’s output was correct, then updated the test expectation to match the real shared posture model rather than changing working logic.

## Verification

I ran the task-level Vitest command from the plan and confirmed the new summary tests and hosted-contract tests pass. I also ran the slice-level verification command to confirm the new summary component coexists cleanly with the T01 helper tests, the existing deployment table tests, and the remote-action card tests. Finally, I ran the slice grep check to confirm the required metadata-backed, fleet-posture, local-runtime, stale/offline, pending-enrollment, and bounded wording is present in the console source.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/deployments/fleet-posture-summary.test.tsx src/lib/hosted-contract.test.ts` | 0 | ✅ pass | 1.01s |
| 2 | `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts` | 0 | ✅ pass | 1.20s |
| 3 | `rg -n "metadata-backed and descriptive only|fleet posture|local runtime|pending enrollment|stale|offline|unlinked|revoked|bounded" console/src` | 0 | ✅ pass | <0.1s |

## Diagnostics

Future agents can inspect `console/src/components/deployments/fleet-posture-summary.tsx` to see the exact page-level composition of fleet counts and hosted-contract copy, and `console/src/components/deployments/fleet-posture-summary.test.tsx` to isolate whether a failure is in summary rendering rather than the underlying helper. If regressions appear later in S02, rerun the summary-specific Vitest command first; if counts drift there too, compare against `console/src/components/deployments/fleet-posture.test.ts` to determine whether the break is in derivation or only in page composition.

## Deviations

None.

## Known Issues

LSP diagnostics were unavailable in this worktree (`No language server found`), so verification relied on direct file inspection plus Vitest coverage rather than editor diagnostics.

## Files Created/Modified

- `console/src/components/deployments/fleet-posture-summary.tsx` — New fleet posture summary component with helper-derived counts, contract-backed trust copy, and empty-state handling.
- `console/src/components/deployments/fleet-posture-summary.test.tsx` — New Vitest coverage for mixed fleets, all-pending fleets, empty state, and non-authoritative wording.
- `console/src/app/(console)/deployments/page.tsx` — Wired the new summary above the deployment table while preserving the existing drawer and mutation flow.
