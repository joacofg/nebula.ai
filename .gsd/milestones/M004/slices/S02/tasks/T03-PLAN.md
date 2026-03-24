---
estimated_steps: 4
estimated_files: 5
skills_used:
  - react-best-practices
  - make-interfaces-feel-better
---

# T03: Make deployment scan-time state legible in the inventory table

**Slice:** S02 — Fleet posture UX
**Milestone:** M004

## Description

Upgrade the deployment inventory table so operators can understand each deployment's enrollment state, posture, and bounded-action eligibility at scan time without opening every detail drawer. This task closes the loop between fleet-level summary and per-row interpretation, preserving the current selection workflow while making row states explicit and trustworthy.

## Steps

1. Update `console/src/components/deployments/deployment-table.tsx` to render enrollment state plus a compact posture/action-status interpretation column or equivalent row cues derived from `console/src/components/deployments/fleet-posture.ts`.
2. Reuse `console/src/components/deployments/deployment-status-badge.tsx`, `FreshnessBadge`, and shared bounded-action state where appropriate so row rendering stays consistent with existing detail surfaces.
3. Expand `console/src/components/deployments/deployment-table.test.tsx` to cover pending, active, revoked, unlinked, stale/offline visibility, and bounded-action-blocked row output, while preserving empty-state and row-selection expectations.
4. Make any minimal page wiring adjustments in `console/src/app/(console)/deployments/page.tsx` needed to pass shared posture data cleanly into the table without changing the drawer selection flow.

## Must-Haves

- [ ] The table exposes row-level state legibility for pending enrollment, active linkage, revoked/unlinked records, stale/offline visibility, and bounded-action-blocked cases.
- [ ] The scan surface remains compact and readable; it should not become a dense operations dashboard or duplicate the drawer's full detail set.
- [ ] Existing row click/selection behavior still opens the detail drawer correctly after the table changes.

## Verification

- `npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts`
- `rg -n "Pending enrollment|Revoked|Unlinked|Stale|Offline|blocked|available" console/src/components/deployments/deployment-table.tsx console/src/components/deployments/deployment-table.test.tsx`

## Inputs

- `console/src/components/deployments/fleet-posture.ts` — shared per-deployment posture interpretation from T01.
- `console/src/components/deployments/fleet-posture-summary.tsx` — summary vocabulary and grouping from T02 to keep row cues aligned.
- `console/src/components/deployments/deployment-table.tsx` — current inventory-only table to upgrade.
- `console/src/components/deployments/deployment-table.test.tsx` — current table assertions to expand.
- `console/src/components/deployments/deployment-status-badge.tsx` — reusable enrollment-state badge.

## Expected Output

- `console/src/components/deployments/deployment-table.tsx` — table updated with scan-time posture/action-state legibility.
- `console/src/components/deployments/deployment-table.test.tsx` — richer table coverage for the new row states and preserved behavior.
- `console/src/components/deployments/deployment-status-badge.tsx` — reused or minimally adjusted badge support for the upgraded scan surface.
- `console/src/app/(console)/deployments/page.tsx` — any necessary wiring updates to feed table posture data while preserving selection flow.
- `console/src/components/deployments/fleet-posture.ts` — any small helper refinements needed to support final table rendering.

## Observability Impact

- Runtime signals: the inventory table should render helper-derived row posture labels, freshness interpretation, and bounded-action availability from `console/src/components/deployments/fleet-posture.ts` instead of ad hoc per-cell conditionals.
- Inspection surfaces: future agents should inspect `console/src/components/deployments/deployment-table.tsx` for the scan-time row composition and `console/src/components/deployments/deployment-table.test.tsx` for explicit expectations around pending, linked, revoked, unlinked, stale/offline, and blocked states.
- Failure visibility: regressions should fail in focused table tests that distinguish derivation-seam breakage from row-rendering drift, while preserving row-selection assertions so broken drawer-opening behavior remains visible.
