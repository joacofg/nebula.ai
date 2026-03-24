---
estimated_steps: 4
estimated_files: 5
skills_used:
  - react-best-practices
  - agent-browser
---

# T02: Re-lock the integrated proof and regression coverage

**Slice:** S04 — Targeted reinforcement refinements
**Milestone:** M004

## Description

Refresh the canonical hosted proof artifact and executable verification so they exactly match the refined shared wording and UI composition from T01. This task closes the slice by proving the same real walkthrough still works after the targeted refinement: public trust-boundary framing, deployments summary/table interpretation, deployment drawer context, and bounded remote action wording all stay aligned without broadening hosted scope.

## Steps

1. Update `docs/hosted-integrated-adoption-proof.md` only where needed so it reflects the actual refined walkthrough path and still delegates contract language back to `console/src/lib/hosted-contract.ts` and `docs/hosted-reinforcement-boundary.md`.
2. Adjust the closest focused Vitest assertions in the hosted walkthrough tests so they lock the refined wording/evidence path without snapshotting whole trees or duplicating page-local prose.
3. Update the Playwright walkthrough only where the visible wording or proof order changed, keeping the browser proof tied to the real hosted trust-boundary page and deployments console flow.
4. Rerun the full S03 verification bar and fix any regression that appears within the existing hosted reinforcement scope.

## Must-Haves

- [ ] `docs/hosted-integrated-adoption-proof.md` remains a composition-first artifact and does not become a second hosted contract.
- [ ] Focused tests and browser proof assert the refined descriptive-only story across the real UI path, not a mock-only or doc-only interpretation.
- [ ] Full verification passes with no new hosted mechanics, no broadened remote-action scope, and no authority drift.

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'`
- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
- `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md`

## Observability Impact

- Signals added/changed: browser proof and focused tests now lock the refined wording/evidence map for the hosted walkthrough.
- How a future agent inspects this: rerun the exact Vitest and Playwright commands, then inspect `docs/hosted-integrated-adoption-proof.md` together with `console/e2e/deployments-proof.spec.ts` and the focused page/component tests.
- Failure state exposed: verification should distinguish doc drift, page/component wording drift, browser interaction drift, and backend hosted-contract drift.

## Inputs

- `docs/hosted-integrated-adoption-proof.md` — canonical hosted walkthrough artifact to keep aligned with the real UI
- `docs/hosted-reinforcement-boundary.md` — boundary contract the integrated proof must continue to defer to
- `console/src/lib/hosted-contract.ts` — shared wording authority the proof must remain anchored to
- `console/src/app/(console)/deployments/page.test.tsx` — focused page-level proof assertions to refresh after T01
- `console/src/components/deployments/remote-action-card.test.tsx` — focused bounded-action/trust assertions to refresh after T01
- `console/e2e/deployments-proof.spec.ts` — browser walkthrough for the authenticated hosted proof path
- `console/e2e/trust-boundary.spec.ts` — browser walkthrough for the public trust-boundary entrypoint
- `tests/test_hosted_contract.py` — backend hosted contract guardrail test that must stay green
- `tests/test_remote_management_api.py` — backend bounded remote-action guardrail test that must stay green

## Expected Output

- `docs/hosted-integrated-adoption-proof.md` — proof artifact updated to match the refined shared wording and real UI seams
- `console/src/app/(console)/deployments/page.test.tsx` — page-level hosted walkthrough assertions refreshed for the final refined story
- `console/src/components/deployments/remote-action-card.test.tsx` — bounded-action/trust assertions refreshed if wording changed in T01
- `console/e2e/deployments-proof.spec.ts` — browser walkthrough assertions aligned with the final refined deployments proof path
- `console/e2e/trust-boundary.spec.ts` — browser trust-boundary assertions aligned if the public wording changed in T01
