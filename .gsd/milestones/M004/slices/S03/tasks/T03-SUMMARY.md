---
id: T03
parent: S03
milestone: M004
provides:
  - Browser-level proof that walks from the public hosted trust-boundary page into the deployments console and asserts mixed-fleet posture plus bounded-action trust wording in the real UI
key_files:
  - console/e2e/deployments-proof.spec.ts
  - console/src/lib/hosted-contract.ts
  - .gsd/milestones/M004/slices/S03/tasks/T03-SUMMARY.md
key_decisions:
  - Reused `getHostedContractContent()` inside the Playwright spec so the browser proof locks to the shared hosted contract wording instead of duplicating fragile page-local prose
  - Kept the browser walkthrough backend-decoupled by mocking only `/api/admin/session`, `/api/admin/deployments`, and deployment remote-action history while still exercising the real authenticated route flow and drawer interaction
  - Fixed the hosted-contract non-empty assertions with a helper that remains valid under tuple inference so the Playwright web-server build can compile deterministically
patterns_established:
  - For hosted walkthrough E2E coverage, prove the public trust-boundary page first, then sign in and continue into the authenticated deployments flow rather than testing the console in isolation
  - When Next/Vitest route-group paths contain parentheses, quote those arguments in shell verification commands to avoid false shell syntax failures
observability_surfaces:
  - npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts
  - /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q
  - console/e2e/deployments-proof.spec.ts
  - console/src/lib/hosted-contract.ts
duration: 1h
verification_result: passed
completed_at: 2026-03-24T12:12:00-03:00
blocker_discovered: false
---

# T03: Add browser proof for the hosted trust walkthrough

**Added a narrow Playwright walkthrough that proves the hosted trust path from the public boundary page into mixed-fleet deployments stays descriptive, bounded, and secondary to local runtime authority.**

## What Happened

I started by verifying the task-plan inputs locally instead of assuming the planner snapshot was still exact. The trust-boundary page, deployments page, fleet summary, deployment table, detail drawer, and remote-action card already exposed the right seams for the proof, so I avoided product-surface churn and focused on wiring one deterministic browser walkthrough through those existing surfaces.

I created `console/e2e/deployments-proof.spec.ts` as the narrow browser proof for the hosted walkthrough. The spec first uses the public login page link to enter `/trust-boundary` and assert the pre-auth trust framing, then signs into the console through the real UI, navigates to `/deployments`, verifies mixed fleet posture counts and row-level stale/offline cues, opens a real deployment detail drawer, and asserts the embedded trust-boundary disclosure plus bounded hosted-action wording that redirects serving-time confirmation back to local runtime observability.

To keep the flow deterministic and backend-decoupled, the spec mocks only the hosted-console dependencies it actually needs: `/api/admin/session`, `/api/admin/deployments`, and per-deployment remote-action history. The mocked fleet intentionally covers one linked/current deployment, one pending enrollment deployment, one stale deployment, and one offline deployment so the browser proof can show mixed-fleet interpretation without broadening into unrelated dashboard coverage.

During verification, Playwright initially failed before running the tests because Next.js would not compile `console/src/lib/hosted-contract.ts`. The failure came from tuple-length narrowing on the shared reinforcement arrays, matching the stale compile issue already mentioned in prior task context. I fixed that by replacing the direct `length === 0` guards with a small `assertNonEmptyArray()` helper, which preserves the runtime intent without tripping TypeScript’s literal-length analysis. After that change, the Playwright proof passed cleanly.

I also ran the rest of the slice verification bar. The backend contract tests passed unchanged. The slice Vitest command passed once rerun with the route-group path safely quoted, because the unquoted shell command treated `src/app/(console)/deployments/page.test.tsx` as a subshell token rather than a file path. The wording grep and walkthrough-doc presence check also passed.

## Verification

I verified the new browser proof with the exact Playwright command specified by the task plan, covering both `console/e2e/trust-boundary.spec.ts` and the new `console/e2e/deployments-proof.spec.ts`. That run passed all three browser tests after the compile fix. I then ran the required backend contract tests, the slice Vitest command covering hosted-contract/trust-boundary/deployments-focused files, and the wording/document-presence grep from the slice plan. All required verification checks are now green.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts` | 0 | ✅ pass | 15.5s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 0 | ✅ pass | 1.07s |
| 3 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'` | 0 | ✅ pass | 1.91s |
| 4 | `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md` | 0 | ✅ pass | <1s |

## Diagnostics

Future agents can inspect the browser-level proof by rerunning `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`. Failures now localize by step inside `console/e2e/deployments-proof.spec.ts`: public trust-boundary entry, authenticated deployments navigation, mixed-fleet summary/table cues, and drawer-level trust/bounded-action wording. If the console stops compiling before Playwright boots, `console/src/lib/hosted-contract.ts` is now a known inspection seam because the build previously failed there due to tuple-length narrowing. Backend trust-boundary and fail-closed remote-management drift remains covered by `tests/test_hosted_contract.py` and `tests/test_remote_management_api.py`.

## Deviations

- I modified `console/src/lib/hosted-contract.ts` even though it was not an expected-output file in the task plan, because the real verification environment exposed a compile blocker there before the browser proof could run.
- I reran the slice Vitest command with shell-safe quoting for `src/app/(console)/deployments/page.test.tsx`; this was a command-invocation correction, not a product change.

## Known Issues

- The Playwright web-server logs still show an unrelated server-side `fetch failed` / `ECONNREFUSED 127.0.0.1:8000` message during the E2E run, but it did not break the targeted hosted trust proof and all browser assertions still passed. No task-plan requirement depended on fixing that broader runtime coupling in this task.

## Files Created/Modified

- `console/e2e/deployments-proof.spec.ts` — new deterministic browser proof for the hosted trust walkthrough across trust-boundary entry, deployments fleet posture, and drawer-level bounded-action guidance
- `console/src/lib/hosted-contract.ts` — replaced tuple-length empty checks with a helper so the shared hosted contract compiles under the Playwright production build
- `.gsd/milestones/M004/slices/S03/tasks/T03-SUMMARY.md` — recorded execution narrative, diagnostics, and verification evidence for T03
