---
estimated_steps: 4
estimated_files: 6
skills_used:
  - react-best-practices
---

# T02: Lock integrated hosted trust and evidence mapping in focused tests

**Slice:** S03 — Confidence proof and trust walkthrough
**Milestone:** M004

## Description

Add or extend focused Vitest coverage so the hosted integrated walkthrough is mechanically enforced in code. This task should verify that the public trust-boundary page, deployments entrypoint, fleet summary, and bounded-action detail story all stay aligned with the shared hosted contract and helper-derived posture semantics. Keep assertions narrow and meaningful: prefer semantic reuse and evidence mapping checks over snapshots.

## Steps

1. Add a deployments-page test file at `console/src/app/(console)/deployments/page.test.tsx` if it does not exist, or extend it if it already exists, to verify the page composes the fleet summary and deployment detail workflow with shared trust-boundary framing.
2. Extend focused component/page tests as needed in `console/src/components/deployments/fleet-posture-summary.test.tsx`, `console/src/components/deployments/remote-action-card.test.tsx`, and `console/src/app/trust-boundary/page.test.tsx` so the integrated story explicitly covers mixed fleet interpretation, bounded-action wording, stale/offline caveats, and local-runtime confirmation guidance.
3. Keep wording assertions anchored to `console/src/lib/hosted-contract.ts` and semantic assertions anchored to `console/src/components/deployments/fleet-posture.ts`; do not duplicate logic in tests or introduce brittle whole-tree snapshots.
4. Run the focused verification suite and fix any drift until the integrated hosted story is locked at the test layer.

## Must-Haves

- [ ] `console/src/app/(console)/deployments/page.test.tsx` proves the real deployments entrypoint participates in the hosted trust walkthrough rather than leaving proof only at subcomponent level.
- [ ] Focused tests fail if hosted wording drifts away from `console/src/lib/hosted-contract.ts` or if bounded-action semantics drift away from `console/src/components/deployments/fleet-posture.ts`.
- [ ] The assertions preserve the rule that hosted surfaces are descriptive and metadata-backed, with local runtime confirmation still required for serving-time behavior.

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/app/(console)/deployments/page.test.tsx`
- `rg -n "metadata-backed and descriptive only|local runtime|bounded operational assistance|fleet posture" console/src/app/(console)/deployments/page.test.tsx console/src/components/deployments/fleet-posture-summary.test.tsx console/src/components/deployments/remote-action-card.test.tsx console/src/app/trust-boundary/page.test.tsx`

## Observability Impact

- Signals added/changed: stronger test-level failure signals for hosted wording drift, mixed-fleet posture drift, and drawer-level bounded-action/trust-boundary composition drift
- How a future agent inspects this: run the focused Vitest command and read failures in `console/src/app/(console)/deployments/page.test.tsx` and the targeted component/page tests
- Failure state exposed: missing trust-boundary copy reuse, missing stale/offline caveats, or deployments-page composition drift becomes explicit instead of inferred from UI behavior

## Inputs

- `docs/hosted-integrated-adoption-proof.md` — canonical hosted walkthrough that test coverage should reinforce
- `console/src/lib/hosted-contract.ts` — wording seam tests must bind to
- `console/src/components/deployments/fleet-posture.ts` — derivation seam tests must trust for posture/action meaning
- `console/src/app/(console)/deployments/page.tsx` — real hosted fleet posture entrypoint under test
- `console/src/components/deployments/fleet-posture-summary.test.tsx` — existing focused summary coverage to extend
- `console/src/components/deployments/remote-action-card.test.tsx` — existing bounded-action coverage to extend
- `console/src/app/trust-boundary/page.test.tsx` — existing public trust-boundary coverage to extend

## Expected Output

- `console/src/app/(console)/deployments/page.test.tsx` — focused entrypoint-level hosted walkthrough coverage
- `console/src/components/deployments/fleet-posture-summary.test.tsx` — updated summary assertions for integrated confidence story
- `console/src/components/deployments/remote-action-card.test.tsx` — updated bounded-action/trust assertions
- `console/src/app/trust-boundary/page.test.tsx` — updated public trust-boundary assertions tied to S03 proof needs
- `console/src/lib/hosted-contract.ts` — optional minimal wording/export adjustment only if the testable canonical seam needs tightening
- `console/src/components/deployments/fleet-posture.ts` — optional minimal semantic adjustment only if tests expose real drift
