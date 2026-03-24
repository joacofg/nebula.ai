---
id: T01
parent: S03
milestone: M004
provides:
  - Canonical hosted integrated proof walkthrough that composes the public trust-boundary page and deployments console without redefining hosted authority
key_files:
  - docs/hosted-integrated-adoption-proof.md
  - docs/hosted-reinforcement-boundary.md
  - .gsd/milestones/M004/slices/S03/tasks/T01-PLAN.md
  - console/src/components/deployments/remote-action-card.tsx
key_decisions:
  - Kept the walkthrough composition-first by referencing hosted-contract and hosted-reinforcement-boundary as canonical seams instead of duplicating page-local contract wording
  - Added only a minimal cross-link in the boundary doc for discoverability rather than changing trust-boundary or deployments page copy
patterns_established:
  - Hosted proof artifacts should start at the public trust-boundary entrypoint, move into fleet posture surfaces, and end by redirecting serving-time truth back to local runtime observability
  - When task plans are missing runtime-relevant observability notes, patch the plan first so downstream execution and summaries have explicit inspection guidance
observability_surfaces:
  - docs/hosted-integrated-adoption-proof.md
  - docs/hosted-reinforcement-boundary.md
  - console/src/lib/hosted-contract.ts
  - console/src/components/deployments/remote-action-card.tsx
duration: 50m
verification_result: passed
completed_at: 2026-03-24T12:01:00-03:00
blocker_discovered: false
---

# T01: Author the canonical hosted integrated proof walkthrough

**Added the canonical hosted integrated proof walkthrough and linked it back to the shared hosted boundary contract.**

## What Happened

I read the existing integrated adoption proof and the hosted boundary/copy seams, then authored `docs/hosted-integrated-adoption-proof.md` in the same composition-first style. The new document walks evaluators from the public trust-boundary page into the real deployments page, fleet posture summary, deployment table, detail drawer, and bounded remote-action card while repeatedly preserving the same conclusion: hosted remains metadata-backed and descriptive only, and local runtime authority stays authoritative for serving-time behavior even when hosted freshness is stale or offline.

To avoid creating a second wording seam, the walkthrough points back to `docs/hosted-reinforcement-boundary.md` and `console/src/lib/hosted-contract.ts` as the canonical contract sources instead of restating new product language. I added one small discoverability link in `docs/hosted-reinforcement-boundary.md` so future readers can find the integrated proof from the boundary document.

The task plan was missing an `## Observability Impact` section even though the task is runtime-relevant, so I patched `.gsd/milestones/M004/slices/S03/tasks/T01-PLAN.md` before implementation. During slice verification, Playwright surfaced a pre-existing TypeScript narrowing issue in `console/src/components/deployments/remote-action-card.tsx`; I fixed the component by capturing a non-null local `activeAdminKey` after the early return. Vitest then passed, but Playwright continued reporting the stale pre-fix compile location in its web-server startup path, so I recorded that slice-level verification as still failing in this task summary rather than overstating completion.

## Verification

I ran the task-level file existence and wording grep checks for the new doc, and both passed. I also ran the slice-level verification commands required by the slice plan: the focused backend pytest contract suite passed, the focused console Vitest suite passed after correcting the shell quoting for the path containing parentheses, and the broad `rg`/file existence slice check passed. The Playwright E2E command still failed during Next.js web-server compilation with a stale report against `console/src/components/deployments/remote-action-card.tsx`, even after the on-disk source was verified and the type-narrowing fix was applied.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/hosted-integrated-adoption-proof.md` | 0 | ✅ pass | <1s |
| 2 | `rg -n "trust boundary|fleet posture|local runtime|request-serving path|bounded operational assistance|credential rotation|stale|offline" docs/hosted-integrated-adoption-proof.md docs/hosted-reinforcement-boundary.md` | 0 | ✅ pass | <1s |
| 3 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'` | 0 | ✅ pass | 20.4s |
| 4 | `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts` | 1 | ❌ fail | 17.1s |
| 5 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 0 | ✅ pass | 10.5s |
| 6 | `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md` | 0 | ✅ pass | <1s |

## Diagnostics

Inspect `docs/hosted-integrated-adoption-proof.md` first to verify the evaluator flow still goes trust-boundary page → deployments page → fleet posture summary → deployment table → detail drawer → bounded remote action while preserving local runtime authority language. Cross-check contract wording against `docs/hosted-reinforcement-boundary.md` and `console/src/lib/hosted-contract.ts` if the doc ever drifts.

For runtime/UI verification, the primary diagnostic surfaces remain `console/src/lib/hosted-contract.ts`, `console/src/components/deployments/fleet-posture.ts`, `console/src/components/deployments/deployment-detail-drawer.tsx`, and `console/src/components/deployments/remote-action-card.tsx`. The current unresolved failure visibility is the Playwright web-server compile step, which still reports a stale `adminKey` narrowing error in `console/src/components/deployments/remote-action-card.tsx` despite the updated source on disk.

## Deviations

- I updated `.gsd/milestones/M004/slices/S03/tasks/T01-PLAN.md` to add the missing `## Observability Impact` section called out by the pre-flight instructions.
- I made a narrow TypeScript fix in `console/src/components/deployments/remote-action-card.tsx` because slice-level verification exposed a compile-time issue unrelated to the documentation changes.

## Known Issues

- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts` still fails during Playwright's Next.js web-server startup with a stale compile error pointing at the old `listRemoteActions(adminKey, deployment.id)` call site in `console/src/components/deployments/remote-action-card.tsx`. The file on disk contains the fix, so the next task should verify whether Playwright/Next is reading cached build state or another environment-specific artifact.
- Because this is the first task in the slice, slice-level verification is only partially green so far; the browser proof remains for downstream work.

## Files Created/Modified

- `docs/hosted-integrated-adoption-proof.md` — new canonical hosted integrated walkthrough from public trust-boundary framing through deployments proof surfaces
- `docs/hosted-reinforcement-boundary.md` — added a minimal cross-link to the canonical integrated walkthrough for discoverability
- `.gsd/milestones/M004/slices/S03/tasks/T01-PLAN.md` — added the missing observability section required by the task pre-flight checks
- `console/src/components/deployments/remote-action-card.tsx` — narrowed `adminKey` to a non-null local constant to satisfy compile-time expectations surfaced during verification
