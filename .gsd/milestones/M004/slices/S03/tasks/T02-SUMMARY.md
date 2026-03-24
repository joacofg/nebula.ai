---
id: T02
parent: S03
milestone: M004
provides:
  - Focused Vitest coverage that locks the hosted trust walkthrough to the shared hosted contract and fleet-posture semantics at page and component level
key_files:
  - console/src/app/(console)/deployments/page.test.tsx
  - console/src/app/trust-boundary/page.test.tsx
  - console/src/components/deployments/fleet-posture-summary.test.tsx
  - console/src/components/deployments/remote-action-card.test.tsx
key_decisions:
  - Bound new assertions to `getHostedContractContent()` and `getBoundedActionAvailability()` seams instead of duplicating page-local wording or posture logic
  - Tested the real deployments entrypoint through its rendered summary, table row selection, drawer disclosure, and bounded-action composition rather than mocking subcomponents away
patterns_established:
  - For hosted trust walkthrough tests, assert shared contract exports and helper-derived posture outcomes instead of brittle full-tree snapshots or copied prose
  - When table rows are the actual interaction affordance, prefer accessible row-name assertions plus click-through verification over assuming button semantics
observability_surfaces:
  - npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/app/(console)/deployments/page.test.tsx
  - console/src/app/(console)/deployments/page.test.tsx
  - console/src/components/deployments/fleet-posture-summary.test.tsx
  - console/src/components/deployments/remote-action-card.test.tsx
duration: 55m
verification_result: passed
completed_at: 2026-03-24T12:07:00-03:00
blocker_discovered: false
---

# T02: Lock integrated hosted trust and evidence mapping in focused tests

**Added focused hosted walkthrough tests that pin deployments and trust-boundary UI to the shared contract and fleet-posture semantics.**

## What Happened

I verified the local hosted trust seams first: `console/src/lib/hosted-contract.ts` already held the canonical wording, `console/src/components/deployments/fleet-posture.ts` already held the posture and bounded-action semantics, and the missing gap was entrypoint-level proof coverage. I added `console/src/app/(console)/deployments/page.test.tsx` to exercise the real deployments page as the authenticated walkthrough entrypoint, asserting that it renders the fleet summary with shared hosted contract wording, exposes mixed fleet posture through the real table, and composes the deployment detail drawer with the embedded trust-boundary disclosure plus bounded remote-action guidance.

I then tightened the existing focused tests instead of changing runtime code unnecessarily. `console/src/app/trust-boundary/page.test.tsx` now anchors its copy assertions to `getHostedContractContent()` and also verifies the public proof order from intro framing into the shared disclosure card and follow-on guidance sections. `console/src/components/deployments/fleet-posture-summary.test.tsx` now proves the summary uses shared descriptive claims and preserves stale/offline interpretation guidance. `console/src/components/deployments/remote-action-card.test.tsx` now checks bounded-action wording against the shared contract while also asserting helper-derived fail-closed statuses for stale, offline, revoked, unlinked, and unsupported deployments.

During verification I found two test-assumption mismatches, not product defects: the deployments table uses clickable rows rather than buttons, and the create drawer copy is different from the phrase I initially expected. I corrected the tests to match the real UI affordances without weakening the contract-level assertions.

## Verification

I ran the focused Vitest suite required by the task plan and slice plan, including the new deployments page test file. The suite passed with all 48 targeted tests green. I also ran the required wording grep over the updated test files to confirm the hosted trust walkthrough evidence is explicitly present where this task was supposed to lock it.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'` | 0 | ✅ pass | 1.99s |
| 2 | `rg -n "metadata-backed and descriptive only|local runtime|bounded operational assistance|fleet posture" 'console/src/app/(console)/deployments/page.test.tsx' console/src/components/deployments/fleet-posture-summary.test.tsx console/src/components/deployments/remote-action-card.test.tsx console/src/app/trust-boundary/page.test.tsx` | 0 | ✅ pass | <1s |

## Diagnostics

Future agents can inspect the same focused failure surfaces by rerunning the Vitest command above. If hosted wording drifts, failures will localize to `console/src/app/trust-boundary/page.test.tsx`, `console/src/components/deployments/fleet-posture-summary.test.tsx`, or `console/src/app/(console)/deployments/page.test.tsx` because those assertions now pull directly from `getHostedContractContent()`. If bounded-action or mixed-fleet semantics drift, failures will localize to `console/src/components/deployments/remote-action-card.test.tsx` and `console/src/components/deployments/fleet-posture-summary.test.tsx`, both of which now rely on `getBoundedActionAvailability()` / shared posture outcomes instead of duplicated expected logic.

## Deviations

- I added one new test file because `console/src/app/(console)/deployments/page.test.tsx` did not exist locally even though the plan treated it as a possible extension target.
- I adapted the deployments-page test to the actual DOM affordances by asserting clickable table rows instead of nonexistent row buttons.

## Known Issues

- None for this task. The focused verification bar defined in T02 is green.

## Files Created/Modified

- `console/src/app/(console)/deployments/page.test.tsx` — new entrypoint-level hosted walkthrough coverage for fleet summary, mixed posture table, and drawer composition
- `console/src/app/trust-boundary/page.test.tsx` — tied public trust-boundary assertions to shared hosted contract exports and proof-order expectations
- `console/src/components/deployments/fleet-posture-summary.test.tsx` — extended summary coverage for mixed-fleet interpretation and stale/offline guidance
- `console/src/components/deployments/remote-action-card.test.tsx` — strengthened bounded-action wording and fail-closed semantic assertions
- `.gsd/milestones/M004/slices/S03/S03-PLAN.md` — marked T02 complete
