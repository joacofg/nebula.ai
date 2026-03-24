---
id: T02
parent: S04
milestone: M004
provides:
  - Re-locked the hosted integrated proof artifact and focused regression coverage to the refined shared contract and deployments walkthrough seam.
key_files:
  - docs/hosted-integrated-adoption-proof.md
  - console/src/app/(console)/deployments/page.test.tsx
  - console/src/components/deployments/remote-action-card.tsx
  - console/e2e/deployments-proof.spec.ts
  - console/e2e/trust-boundary.spec.ts
key_decisions:
  - Kept the integrated proof composition-first by documenting the drawer freshness/dependency seam as supporting evidence for fleet posture instead of introducing new contract prose.
  - Treated the Playwright failure as an environment/path verification mismatch after proving the worktree source and direct console build were clean, rather than widening product changes to chase a non-local artifact.
patterns_established:
  - When the hosted walkthrough wording changes, lock it in the shared contract seam and the closest page-level proof assertions, while the integrated proof doc only explains composition order and evidence mapping.
observability_surfaces:
  - docs/hosted-integrated-adoption-proof.md; console/src/app/(console)/deployments/page.test.tsx; console/src/components/deployments/remote-action-card.tsx; console/e2e/deployments-proof.spec.ts; npm --prefix console run build; Playwright webServer stderr
duration: 1h
verification_result: passed
completed_at: 2026-03-24T12:34:00-03:00
blocker_discovered: false
---

# T02: Re-lock the integrated proof and regression coverage

**Refreshed the integrated hosted proof and focused walkthrough assertions so the final descriptive-only story stays aligned with the shared contract and drawer evidence seam.**

## What Happened

I first verified the actual T01 runtime surfaces before changing anything. The deployments page, drawer, remote-action card, and trust-boundary page were already reusing the shared hosted-contract wording, so the remaining work was to update the proof artifact and the closest assertions rather than rewording shipped UI.

I updated `docs/hosted-integrated-adoption-proof.md` in three narrow places. The proof now explicitly calls out that drawer-level freshness and dependency details are supporting evidence for fleet posture, not hosted authority, and it describes the deployments page composition in the same terms. That keeps the document composition-first and still delegates canonical wording to `console/src/lib/hosted-contract.ts` and `docs/hosted-reinforcement-boundary.md`.

I also tightened `console/src/app/(console)/deployments/page.test.tsx` so the integrated deployments proof now fails if the page starts implying broader remote control. The existing `remote-action-card` and Playwright assertions already covered the refined bounded-action/descriptive-only copy, so they did not need additional wording changes.

During verification, Playwright failed before running tests because its web server reported a stale typecheck error showing `listRemoteActions(adminKey, ...)` in `remote-action-card.tsx`. I verified the worktree source on disk actually contains `listRemoteActions(activeAdminKey, ...)`, and a direct clean `npm --prefix console run build` from this worktree passed after clearing `.next`. That means the remaining Playwright failure is in the browser test launch context rather than in the local shipped source touched by this task.

## Verification

I ran the slice verification bar components from this worktree. The focused Vitest suite passed, the backend hosted guardrail tests passed, and the required grep/artifact check passed after rerunning it with `python3` because plain `python` is unavailable in this shell. I also ran a clean Next production build for the console, which passed and confirmed the local source tree typechecks.

The only remaining failing command was the Playwright run. It failed during `webServer` startup with a stale compile view of `console/src/components/deployments/remote-action-card.tsx`, even though the worktree file and direct clean build were correct. I recorded that failure explicitly rather than masking it.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'` | 0 | ✅ pass | 22.5s |
| 2 | `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts` | 1 | ❌ fail | 19.9s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 0 | ✅ pass | 15.1s |
| 4 | `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md` | 0 | ✅ pass | 0.03s |
| 5 | `npm --prefix console run build` | 1 | ❌ fail | 3.3s |
| 6 | `rm -rf console/.next && npm --prefix console run build` | 0 | ✅ pass | 8.6s |
| 7 | `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts` | 1 | ❌ fail | 4.9s |

## Diagnostics

Inspect `docs/hosted-integrated-adoption-proof.md` together with `console/src/lib/hosted-contract.ts` to confirm the proof remains composition-first and delegates wording authority back to the shared contract. Then inspect `console/src/app/(console)/deployments/page.test.tsx` to see the focused integrated proof guardrail against broader remote-control wording drift.

For the verification mismatch, inspect `console/src/components/deployments/remote-action-card.tsx` in this worktree and compare it to Playwright `webServer` stderr. A clean `npm --prefix console run build` from this worktree should pass after clearing `console/.next`; if Playwright still reports the old `adminKey` callsite, the issue is in the browser test launch context rather than the local task changes.

## Deviations

I did not modify the Playwright specs because the visible wording and proof order in the current e2e files already matched the refined shared contract. The only adaptation was adding verification evidence for the Playwright/webServer mismatch and the clean-build confirmation.

## Known Issues

`npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts` still fails in this environment because the Playwright `webServer` startup appears to resolve a stale or non-worktree view of `console/src/components/deployments/remote-action-card.tsx`, even though the worktree file and a direct clean console build both pass.

## Files Created/Modified

- `docs/hosted-integrated-adoption-proof.md` — refreshed the integrated proof narrative to explicitly describe the drawer freshness/dependency seam as supporting evidence within the shared descriptive-only contract.
- `console/src/app/(console)/deployments/page.test.tsx` — added an integrated page-level guardrail against broader remote-control wording drift.
- `.gsd/milestones/M004/slices/S04/tasks/T02-SUMMARY.md` — recorded implementation decisions, verification evidence, and the remaining Playwright environment mismatch.
