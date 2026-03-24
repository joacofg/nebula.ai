---
id: T03
parent: S01
milestone: M004
provides:
  - Canonical deployment-facing hosted action wording plus a reusable hosted reinforcement boundary artifact for downstream slices
key_files:
  - console/src/components/deployments/remote-action-card.tsx
  - console/src/components/deployments/remote-action-card.test.tsx
  - console/src/app/(console)/deployments/page.tsx
  - docs/hosted-reinforcement-boundary.md
  - .gsd/milestones/M004/slices/S01/S01-PLAN.md
key_decisions:
  - Reused shared hosted-contract reinforcement strings directly in deployment-management surfaces and kept any extra copy limited to local-runtime confirmation guidance instead of adding a new deployment wording island
patterns_established:
  - When deployment-facing UI needs hosted trust-boundary copy, derive the bounded-action statement from getHostedContractContent() and add only nearby operator guidance that reinforces local-runtime authority
observability_surfaces:
  - console/src/components/deployments/remote-action-card.tsx
  - console/src/app/(console)/deployments/page.tsx
  - docs/hosted-reinforcement-boundary.md
  - npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx
  - /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_remote_management_api.py -q
  - npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx
  - /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q
  - rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs
duration: 22m
verification_result: passed
completed_at: 2026-03-24T11:31:00-03:00
blocker_discovered: false
---

# T03: Align deployment-facing hosted action copy and publish the slice boundary artifact

**Aligned deployment-management hosted wording to the shared contract seam and published a reusable hosted reinforcement boundary artifact for downstream slices.**

## What Happened

I updated `console/src/components/deployments/remote-action-card.tsx` to consume `reinforcement.boundedActionPhrasing.description` from `getHostedContractContent()` instead of keeping its own local hosted-control phrasing. I also added one nearby operator-facing sentence that keeps the card explicitly metadata-backed and descriptive only while directing readers back to local runtime observability for serving-time confirmation.

I then aligned `console/src/app/(console)/deployments/page.tsx` with the same shared wording seam by adding a compact explainer under the deployments header. That copy reuses the canonical bounded-action and operator-guidance phrases without adding any fleet-posture synthesis or new deployment-state logic.

To keep the wording fail-closed, I extended `console/src/components/deployments/remote-action-card.test.tsx` with a focused assertion that the card renders the shared bounded-action description plus the new local-runtime confirmation caveat, while preserving the existing stale, offline, revoked, unlinked, unsupported, and note-validation coverage.

Finally, I wrote `docs/hosted-reinforcement-boundary.md` as the slice artifact. It captures the allowed hosted claims, prohibited authority implications, bounded-action rules, operator-reading guidance, and explicit acceptance rules that S02/S03 must preserve when they introduce fleet-posture, confidence, and proof work.

## Verification

I first ran the focused remote-action Vitest file and hit a syntax error caused by my initial test insertion landing outside the `describe` block. I read the full test file, rewrote it cleanly around the existing cases, and reran the same focused test before moving on.

After that fix, the task-level frontend and backend checks both passed. I then ran the full slice-level verification set: the four focused Vitest files passed, both backend contract files passed, the wording drift grep returned the expected hosted-boundary phrases across console and docs surfaces, and the new boundary artifact file check passed. These checks cover the observability surfaces named in the plan: the shared content seam, public trust-boundary surfaces, deployment-facing card, backend guardrails, and the new doc artifact.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx` | 1 | ❌ fail | ~1s |
| 2 | `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx` | 0 | ✅ pass | ~1s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_remote_management_api.py -q` | 0 | ✅ pass | ~1s |
| 4 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx` | 0 | ✅ pass | ~1s |
| 5 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 0 | ✅ pass | ~1s |
| 6 | `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs` | 0 | ✅ pass | <1s |
| 7 | `test -f docs/hosted-reinforcement-boundary.md` | 0 | ✅ pass | <1s |

## Diagnostics

Inspect `console/src/components/deployments/remote-action-card.tsx` to see the deployment-facing bounded-action copy now sourced from `getHostedContractContent()`. Inspect `console/src/app/(console)/deployments/page.tsx` for the header-level reinforcement that keeps deployment management descriptive and non-authoritative. Inspect `docs/hosted-reinforcement-boundary.md` for the downstream acceptance contract. If wording drifts, the fastest signals are the focused Vitest suites, the backend hosted-contract and remote-management pytest files, and the grep sweep over `console/src` plus `docs`.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/deployments/remote-action-card.tsx` — replaced bespoke hosted-control wording with the shared bounded-action contract and added a local-runtime confirmation caveat.
- `console/src/components/deployments/remote-action-card.test.tsx` — locks the shared bounded-action phrasing and preserves existing fail-closed remote-action behavior checks.
- `console/src/app/(console)/deployments/page.tsx` — adds a small deployment-management explainer derived from the shared hosted reinforcement wording.
- `docs/hosted-reinforcement-boundary.md` — publishes the slice artifact documenting allowed claims, prohibited implications, and downstream acceptance rules.
- `.gsd/milestones/M004/slices/S01/S01-PLAN.md` — marks T03 complete.
