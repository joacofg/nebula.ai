---
estimated_steps: 4
estimated_files: 5
skills_used:
  - agent-browser
  - react-best-practices
---

# T03: Add browser proof for the hosted trust walkthrough

**Slice:** S03 — Confidence proof and trust walkthrough
**Milestone:** M004

## Description

Add a narrow Playwright proof that exercises the hosted trust walkthrough as a real browser flow. The goal is not a broad deployments dashboard suite; it is one credible operator walkthrough showing that a mixed fleet can be interpreted from the deployments entrypoint, that the detail drawer reinforces the trust boundary and bounded action scope, and that the public trust-boundary page remains part of the proof path.

## Steps

1. Review the existing style and fixtures in `console/e2e/trust-boundary.spec.ts`, then create `console/e2e/deployments-proof.spec.ts` focused on the deployments confidence walkthrough.
2. Mock the admin/deployments responses needed for a mixed fleet so the browser proof can show linked/current, pending, stale or offline, and bounded-action-blocked states without introducing backend coupling.
3. In the new spec, open the deployments page, assert fleet summary and scan-time table cues, select a deployment, and verify the detail drawer shows dependency context, trust-boundary guidance, and bounded hosted action wording that still directs serving-time confirmation back to local runtime observability.
4. Keep the proof aligned with `docs/hosted-integrated-adoption-proof.md`; update `console/e2e/trust-boundary.spec.ts` only if small shared assertions or proof ordering adjustments improve the joined story.

## Must-Haves

- [ ] `console/e2e/deployments-proof.spec.ts` exercises the real hosted deployments entrypoint with mocked mixed-fleet data and drawer interaction.
- [ ] The browser proof asserts hosted descriptive-only wording and local-runtime authority caveats, not just generic visibility of cards.
- [ ] The flow remains narrow and deterministic; it should not expand into unrelated dashboard or backend integration coverage.

## Verification

- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`

## Observability Impact

- Signals added/changed: browser-level evidence that the hosted walkthrough still renders mixed-fleet interpretation, trust-boundary framing, and fail-closed bounded-action semantics together
- How a future agent inspects this: run Playwright for `console/e2e/deployments-proof.spec.ts` and inspect assertion failures by step (entry summary, row scan, drawer trust copy, bounded-action copy)
- Failure state exposed: broken page composition, missing mock wiring, or trust-boundary text regressions become visible in end-to-end proof instead of only component tests

## Inputs

- `docs/hosted-integrated-adoption-proof.md` — canonical walkthrough the browser proof should mirror
- `console/e2e/trust-boundary.spec.ts` — existing public hosted proof pattern and assertion style
- `console/src/app/(console)/deployments/page.tsx` — browser entrypoint under proof
- `console/src/components/deployments/deployment-detail-drawer.tsx` — drawer content the browser proof must surface
- `console/src/components/deployments/remote-action-card.tsx` — bounded-action wording the browser proof must assert
- `console/src/components/deployments/fleet-posture-summary.tsx` — fleet summary cues the browser proof must assert

## Expected Output

- `console/e2e/deployments-proof.spec.ts` — new Playwright proof for the hosted confidence walkthrough
- `console/e2e/trust-boundary.spec.ts` — optional small assertion update if needed to align the joined proof path
- `console/src/app/(console)/deployments/page.tsx` — optional minimal testability adjustment only if required for deterministic browser proof
- `console/src/components/deployments/deployment-detail-drawer.tsx` — optional minimal accessibility/testability adjustment only if required for deterministic browser proof
- `docs/hosted-integrated-adoption-proof.md` — optional small wording update if browser-proof learnings require clarifying the documented walkthrough
