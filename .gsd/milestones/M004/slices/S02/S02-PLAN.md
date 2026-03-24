# S02: Fleet posture UX

**Goal:** Add a real hosted console fleet-posture reading layer that helps operators interpret multi-deployment linkage, freshness, and bounded-action availability from existing deployment metadata without implying hosted authority over local runtime enforcement.
**Demo:** From the deployments console entrypoint, an operator can scan fleet posture cards and the deployment table to distinguish pending enrollment, active/linked deployments, stale or offline visibility, revoked/unlinked records, and bounded-action blocked states before opening a detail drawer, while trust-boundary wording remains sourced from the shared hosted contract.

## Must-Haves

- Add a pure posture-derivation seam that computes fleet-level and per-deployment posture from existing `DeploymentRecord` facts, including bounded-action availability/block reasons, without inventing backend authority or new hosted status enums.
- Add a deployments-page fleet summary surface that shows at-a-glance linked/current, pending, stale/offline visibility, and bounded-action blocked counts with copy grounded in `console/src/lib/hosted-contract.ts`.
- Upgrade the deployments inventory table so linked, pending enrollment, revoked, unlinked, freshness, and bounded-action-blocked states are legible during scan-time rather than only in the detail drawer.
- Reuse one shared truth source for bounded-action blocking semantics so summary/table cues and `RemoteActionCard` stay aligned.
- Lock the slice with focused Vitest coverage proving the posture derivation, summary rendering, table legibility, and trust-boundary wording.

## Proof Level

- This slice proves: integration
- Real runtime required: no
- Human/UAT required: no

## Verification

- `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts`
- `rg -n "metadata-backed and descriptive only|fleet posture|local runtime|pending enrollment|stale|offline|unlinked|revoked|bounded" console/src`

## Observability / Diagnostics

- Runtime signals: derived UI state for fleet counts, row posture labels, and bounded-action block reasons sourced from shared helper functions rather than duplicated component-local conditionals.
- Inspection surfaces: `console/src/components/deployments/fleet-posture.ts`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-table.tsx`, and focused Vitest assertions covering rendered copy and blocked-state explanations.
- Failure visibility: tests should reveal whether regressions come from derivation logic, hosted-contract wording drift, or page/table composition by asserting each seam separately.
- Redaction constraints: remain metadata-only; no new secrets, credentials, prompts, or responses may be surfaced.

## Integration Closure

- Upstream surfaces consumed: `console/src/lib/admin-api.ts`, `console/src/lib/hosted-contract.ts`, `console/src/lib/freshness.ts`, `console/src/components/deployments/deployment-status-badge.tsx`, `console/src/components/deployments/remote-action-card.tsx`, `console/src/app/(console)/deployments/page.tsx`.
- New wiring introduced in this slice: shared posture helper feeds a new fleet summary component, the deployments page header/body composition, the inventory table scan surface, and the remote-action card's blocked-state semantics.
- What remains before the milestone is truly usable end-to-end: S03 must assemble and prove the integrated confidence walkthrough using the real hosted fleet-posture surface delivered here.

## Tasks

- [x] **T01: Extract shared fleet posture and bounded-action derivation** `est:45m`
  - Why: S02's biggest risk is semantic drift: if the page summary, table, and remote-action card each derive posture differently, operators will see contradictory state and the hosted trust boundary will blur.
  - Files: `console/src/components/deployments/fleet-posture.ts`, `console/src/components/deployments/fleet-posture.test.ts`, `console/src/components/deployments/remote-action-card.tsx`, `console/src/components/deployments/remote-action-card.test.tsx`
  - Do: Add a pure helper module that maps `DeploymentRecord[]` into fleet posture counts and per-row interpretation details using existing enrollment, freshness, capability, and remote-action metadata only; extract shared bounded-action disabled-reason logic from `RemoteActionCard`; keep wording descriptive and aligned with the hosted contract rather than inventing new authority-leaning language.
  - Verify: `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/remote-action-card.test.tsx`
  - Done when: one shared helper produces the fleet posture model and bounded-action block reasons, and `RemoteActionCard` consumes it without changing the bounded hosted action scope.
- [x] **T02: Add the deployments fleet posture summary surface** `est:45m`
  - Why: R032 and R036 require an at-a-glance hosted reading surface at the page entrypoint; without a real summary above the table, operators still have to reconstruct fleet posture from row-by-row inspection.
  - Files: `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/fleet-posture-summary.test.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/lib/hosted-contract.ts`
  - Do: Build a summary component that renders fleet posture cards or grouped cues for linked/current, pending enrollment, stale/offline visibility, and bounded-action blocked deployments; wire it into the deployments page using the shared posture helper and hosted-contract wording; keep the page copy explicit that hosted posture is metadata-backed and local runtime remains authoritative.
  - Verify: `npm --prefix console run test -- --run src/components/deployments/fleet-posture-summary.test.tsx src/lib/hosted-contract.test.ts`
  - Done when: the deployments page shows a trustworthy summary layer above the table and its explanatory text still comes from the shared hosted-contract seam.
- [x] **T03: Make deployment scan-time state legible in the inventory table** `est:45m`
  - Why: The fleet summary alone is not enough; R033 and R035 also require operators to understand each deployment's state and bounded-action eligibility without opening the detail drawer for every row.
  - Files: `console/src/components/deployments/deployment-table.tsx`, `console/src/components/deployments/deployment-table.test.tsx`, `console/src/components/deployments/deployment-status-badge.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/fleet-posture.ts`
  - Do: Update the table to surface enrollment state plus a compact posture/action-status interpretation column or equivalent scan-friendly cues derived from the shared helper; preserve current selection/drawer behavior; keep the table from becoming a noisy operations dashboard by emphasizing legibility over extra telemetry.
  - Verify: `npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts`
  - Done when: an operator can scan the table and distinguish pending, active, revoked, unlinked, stale/offline visibility, and bounded-action-blocked rows without relying on drawer-only details.

## Files Likely Touched

- `console/src/app/(console)/deployments/page.tsx`
- `console/src/components/deployments/fleet-posture.ts`
- `console/src/components/deployments/fleet-posture.test.ts`
- `console/src/components/deployments/fleet-posture-summary.tsx`
- `console/src/components/deployments/fleet-posture-summary.test.tsx`
- `console/src/components/deployments/deployment-table.tsx`
- `console/src/components/deployments/deployment-table.test.tsx`
- `console/src/components/deployments/remote-action-card.tsx`
- `console/src/components/deployments/remote-action-card.test.tsx`
- `console/src/lib/hosted-contract.ts`
