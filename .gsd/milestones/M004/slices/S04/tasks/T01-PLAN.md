---
estimated_steps: 4
estimated_files: 5
skills_used:
  - react-best-practices
---

# T01: Tighten shared hosted wording and the narrowest UI seam

**Slice:** S04 — Targeted reinforcement refinements
**Milestone:** M004

## Description

Close the real wording/evidence-mapping gap exposed by the integrated hosted walkthrough without adding any new hosted behavior. Start from the shared hosted contract, then patch only the narrowest affected deployments-console seam — most likely page bridge copy, the fleet summary, the deployment drawer, or the remote-action interpretation surface. Keep the change composition-first: shared wording lives in `console/src/lib/hosted-contract.ts`, posture semantics stay in `console/src/components/deployments/fleet-posture.ts`, and the UI should only reuse those authorities.

## Steps

1. Compare the current proof path across `console/src/app/trust-boundary/page.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-table.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, and `console/src/components/deployments/remote-action-card.tsx` to identify the smallest real interpretation or wording gap.
2. If the gap is missing canonical language, add or tighten it in `console/src/lib/hosted-contract.ts` first; do not create new page-local trust wording.
3. Thread the refined wording into the narrowest affected UI seam, preferring drawer-level connective clarification for context-reading gaps and leaving `console/src/components/deployments/fleet-posture.ts` as the only posture-derivation authority.
4. Update the closest focused assertions so the affected surface fails if the descriptive-only trust boundary drifts again.

## Must-Haves

- [ ] Any new trust-boundary or operator-reading text is authored in `console/src/lib/hosted-contract.ts` and reused by consumers instead of being invented locally in a page or component.
- [ ] The refined UI still reads as metadata-backed and descriptive only, and it does not imply hosted authority over serving-time health, routing, fallback, tenant policy, or provider selection.
- [ ] The task does not add new hosted statuses, new dashboard surfaces, new remote actions, or a second semantic seam beside `console/src/components/deployments/fleet-posture.ts`.

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'`
- `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src`

## Observability Impact

- Signals added/changed: any refined descriptive-only wording or drawer/page interpretation cue becomes assertion-backed at the shared contract seam and the nearest UI seam.
- How a future agent inspects this: read `console/src/lib/hosted-contract.ts`, then inspect the updated page/summary/drawer/action component and its paired test file to localize whether drift is in wording or composition.
- Failure state exposed: test failures should show whether hosted authority language drifted in the shared contract or in one specific deployments-console consumer.

## Inputs

- `console/src/lib/hosted-contract.ts` — canonical hosted wording seam that must remain the single source of trust-boundary language
- `console/src/app/trust-boundary/page.tsx` — public proof entrypoint to compare against deployments wording
- `console/src/app/(console)/deployments/page.tsx` — authenticated hosted fleet entrypoint that may need a small bridge refinement
- `console/src/components/deployments/fleet-posture-summary.tsx` — summary-level interpretation surface that may need a wording refinement
- `console/src/components/deployments/deployment-table.tsx` — row-level interpretation surface that must stay semantically aligned
- `console/src/components/deployments/deployment-detail-drawer.tsx` — likely seam for connective context wording if the proof gap is drawer-level
- `console/src/components/deployments/remote-action-card.tsx` — bounded-action framing surface that must remain narrow and descriptive
- `console/src/app/(console)/deployments/page.test.tsx` — closest page-level regression coverage for the joined hosted walkthrough
- `console/src/components/deployments/remote-action-card.test.tsx` — closest bounded-action wording regression coverage

## Expected Output

- `console/src/lib/hosted-contract.ts` — refined shared hosted wording if the canonical contract needs a tighter phrase or connective claim
- `console/src/app/(console)/deployments/page.tsx` — updated only if the page-level hosted proof bridge needs the refinement
- `console/src/components/deployments/fleet-posture-summary.tsx` — updated only if the summary is the narrowest gap seam
- `console/src/components/deployments/deployment-detail-drawer.tsx` — updated only if the drawer needs explicit context-not-authority connective copy
- `console/src/components/deployments/remote-action-card.tsx` — updated only if bounded-action interpretation wording needs a narrow refinement
- `console/src/app/(console)/deployments/page.test.tsx` — focused page-level assertions aligned with the refined walkthrough wording
- `console/src/components/deployments/remote-action-card.test.tsx` — focused bounded-action assertions aligned with the refined shared wording
