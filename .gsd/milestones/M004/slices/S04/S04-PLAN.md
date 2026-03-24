# S04: Targeted reinforcement refinements

**Goal:** Close any remaining wording, evidence-mapping, or interpretation gaps found in the hosted integrated proof by tightening the existing shared hosted-contract and deployments-console seams without expanding hosted scope or authority.
**Demo:** An evaluator can follow the public trust-boundary page through the real deployments console, including fleet summary, mixed-state table, deployment drawer, and bounded remote action framing, and see a fully aligned descriptive-only story with no page-local authority drift.

## Must-Haves

- Advance active requirement R034 by ensuring hosted posture summaries, drawer/detail interpretation, proof copy, and any derived status language stay grounded in metadata-only facts and explicitly avoid implying serving-time or policy authority.
- Materially support deferred requirement R014 by closing proof-time clarity gaps only through targeted reinforcement refinements, not new hosted mechanics, statuses, or remote actions.
- Keep `console/src/lib/hosted-contract.ts` as the single wording authority and `console/src/components/deployments/fleet-posture.ts` as the posture interpretation authority; S04 must not create a second wording island or duplicate semantics.
- Preserve the canonical S03 walkthrough order and evidence path across `console/src/app/trust-boundary/page.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-table.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `console/src/components/deployments/remote-action-card.tsx`, and `docs/hosted-integrated-adoption-proof.md`.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'`
- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
- `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md`

## Observability / Diagnostics

- Runtime signals: hosted trust-boundary wording, fleet-posture interpretation labels, drawer-level trust/evidence cues, and bounded remote-action wording remain separable and assertion-backed.
- Inspection surfaces: `console/src/lib/hosted-contract.ts`, `console/src/components/deployments/fleet-posture.ts`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `console/src/components/deployments/remote-action-card.tsx`, `docs/hosted-integrated-adoption-proof.md`, and `console/e2e/deployments-proof.spec.ts`.
- Failure visibility: focused Vitest failures should localize wording drift vs posture derivation drift vs page/drawer composition drift; Playwright failures should localize whether the integrated walkthrough no longer reads as descriptive-only in the real console flow.
- Redaction constraints: refinements must preserve the metadata-only boundary and must not introduce prompts, responses, provider credentials, tenant secrets, or authoritative local runtime policy state into hosted proof artifacts.

## Integration Closure

- Upstream surfaces consumed: `console/src/lib/hosted-contract.ts`, `console/src/components/deployments/fleet-posture.ts`, `console/src/app/trust-boundary/page.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-table.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `console/src/components/deployments/remote-action-card.tsx`, `docs/hosted-integrated-adoption-proof.md`, `docs/hosted-reinforcement-boundary.md`.
- New wiring introduced in this slice: narrow composition and wording refinements only, threaded from the shared hosted-contract seam into the existing deployments summary/drawer/proof path.
- What remains before the milestone is truly usable end-to-end: nothing for this slice; completion means the integrated hosted reinforcement path stays aligned after targeted close-out refinements.

## Tasks

- [x] **T01: Tighten shared hosted wording and the narrowest UI seam** `est:45m`
  - Why: R034 is still active because the hosted walkthrough must stay explicitly descriptive-only across all reused surfaces; the highest-risk gap is wording or evidence-mapping drift between the shared contract and the deployments summary/drawer flow.
  - Files: `console/src/lib/hosted-contract.ts`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `console/src/components/deployments/remote-action-card.tsx`
  - Do: Compare the current hosted walkthrough surfaces against the canonical proof path, identify the smallest real interpretation gap, then fix it by reusing or minimally extending shared hosted-contract exports and threading that wording through the narrowest affected UI seam; keep `fleet-posture.ts` as the semantic authority, avoid adding new statuses/cards/workflows, and prefer drawer-level connective clarification if the gap is context-reading rather than summary math.
  - Verify: `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'`
  - Done when: the refined UI surfaces read as one continuous descriptive-only story sourced from shared contract wording, with no new hosted authority or duplicated page-local trust copy.
- [ ] **T02: Re-lock the integrated proof and regression coverage** `est:45m`
  - Why: S04 is done only if the canonical proof artifact and executable verification still match the real UI after refinements; otherwise the milestone regresses into story drift.
  - Files: `docs/hosted-integrated-adoption-proof.md`, `console/src/app/(console)/deployments/page.test.tsx`, `console/src/components/deployments/remote-action-card.test.tsx`, `console/e2e/deployments-proof.spec.ts`, `console/e2e/trust-boundary.spec.ts`
  - Do: Update the integrated proof document and the closest focused/browser assertions to reflect the refined wording/evidence path, keeping the walkthrough composition-first and anchored to shared hosted-contract exports rather than page-local prose; rerun the full S03 verification bar and fix any regression that appears within the existing hosted reinforcement scope.
  - Verify: `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx' && npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q && rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md`
  - Done when: the proof doc, focused tests, browser walkthrough, backend guardrail tests, and wording/artifact checks all pass without widening hosted scope.

## Files Likely Touched

- `console/src/lib/hosted-contract.ts`
- `console/src/app/(console)/deployments/page.tsx`
- `console/src/components/deployments/fleet-posture-summary.tsx`
- `console/src/components/deployments/deployment-detail-drawer.tsx`
- `console/src/components/deployments/remote-action-card.tsx`
- `docs/hosted-integrated-adoption-proof.md`
- `console/src/app/(console)/deployments/page.test.tsx`
- `console/src/components/deployments/remote-action-card.test.tsx`
- `console/e2e/deployments-proof.spec.ts`
- `console/e2e/trust-boundary.spec.ts`
