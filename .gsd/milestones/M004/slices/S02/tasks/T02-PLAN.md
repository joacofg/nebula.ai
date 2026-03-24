---
estimated_steps: 4
estimated_files: 4
skills_used:
  - react-best-practices
  - make-interfaces-feel-better
---

# T02: Add the deployments fleet posture summary surface

**Slice:** S02 — Fleet posture UX
**Milestone:** M004

## Description

Turn the new posture model into the actual hosted reading surface at the top of the deployments page. This task should add a clear, compact summary layer that helps operators understand fleet linkage, freshness visibility, and bounded-action blockage across multiple deployments before drilling into details, while keeping the wording explicitly metadata-backed and non-authoritative.

## Steps

1. Build `console/src/components/deployments/fleet-posture-summary.tsx` to render summary cards or grouped cues for linked/current, pending enrollment, stale/offline visibility, and bounded-action-blocked deployments from the shared helper output.
2. Add `console/src/components/deployments/fleet-posture-summary.test.tsx` to assert the summary renders meaningful counts, empty-state behavior, and trust-boundary-aware copy for mixed fleets.
3. Wire the summary into `console/src/app/(console)/deployments/page.tsx` above the deployment table, computing posture from the fetched deployments data and preserving the existing drawer/mutation flow.
4. Reuse `console/src/lib/hosted-contract.ts` strings for explanatory copy or extend that shared contract minimally if an additional fleet-posture explanation is truly needed, keeping local runtime authority explicit.

## Must-Haves

- [ ] The deployments page shows a real summary surface at the entrypoint instead of burying posture interpretation in the drawer.
- [ ] Summary copy stays grounded in `console/src/lib/hosted-contract.ts` and does not imply hosted authority over serving-time health, routing, fallback, or policy enforcement.
- [ ] Empty or all-pending fleets still render a coherent, non-broken hosted posture summary.

## Verification

- `npm --prefix console run test -- --run src/components/deployments/fleet-posture-summary.test.tsx src/lib/hosted-contract.test.ts`
- `rg -n "metadata-backed|fleet posture|local runtime|bounded" console/src/app/\(console\)/deployments/page.tsx console/src/components/deployments/fleet-posture-summary.tsx console/src/lib/hosted-contract.ts`

## Observability Impact

- Signals added/changed: the deployments page exposes fleet-level posture counts and trust-boundary copy as explicit UI state rather than implicit row interpretation.
- How a future agent inspects this: render tests for `fleet-posture-summary` and the page wiring show whether failures are in data derivation, copy sourcing, or composition.
- Failure state exposed: missing/incorrect summary groups or wording drift are visible directly in the top-of-page summary component and its assertions.

## Inputs

- `console/src/components/deployments/fleet-posture.ts` — shared posture counts/groups from T01.
- `console/src/app/(console)/deployments/page.tsx` — deployments entrypoint where the new summary must be composed.
- `console/src/lib/hosted-contract.ts` — canonical trust-boundary wording seam to reuse.
- `console/src/components/deployments/deployment-table.tsx` — existing inventory surface that the summary must precede without replacing.

## Expected Output

- `console/src/components/deployments/fleet-posture-summary.tsx` — new page-level fleet posture summary component.
- `console/src/components/deployments/fleet-posture-summary.test.tsx` — tests for mixed-fleet counts, empty-state behavior, and non-authoritative wording.
- `console/src/app/(console)/deployments/page.tsx` — deployments page wired to compute and render the summary.
- `console/src/lib/hosted-contract.ts` — reused or minimally extended shared wording seam if needed for the summary copy.
