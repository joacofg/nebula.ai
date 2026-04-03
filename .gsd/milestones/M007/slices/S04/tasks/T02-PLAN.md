---
estimated_steps: 47
estimated_files: 2
skills_used: []
---

# T02: Align page framing and mutation orchestration with the new decision flow

---
estimated_steps: 4
estimated_files: 2
skills_used:
  - react-best-practices
---

# T02: Align page framing and mutation orchestration with the new decision flow

**Slice:** S04 — Rework policy preview into a comparison-and-decision flow
**Milestone:** M007

## Description

Update the policy page wrapper only where the new form-level decision flow exposes framing or orchestration gaps. Preserve the current preview-vs-save mutation split, tenant-level reset behavior, and bounded simulate request shape, while tightening page-level copy and tests so the whole surface reads as compare → decide → save instead of a blended editor or analytics page.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `simulateTenantPolicy` / `updateTenantPolicy` mutations in `console/src/app/(console)/policy/page.tsx` | Keep preview and save errors isolated to their existing surfaces; do not let preview imply persistence | Preserve pending-state separation so preview latency does not block unrelated framing or fake a saved state | Fail through existing page/form error handling; do not widen contract assumptions beyond the current bounded response |

## Load Profile

- **Shared resources**: React Query cache entries for tenant list, policy, options, and simulation state within the policy page
- **Per-operation cost**: One tenant-policy query, one options query, and bounded preview/save mutations already present
- **10x breakpoint**: Repeated tenant switching or preview calls mainly risks stale UI messaging; keep resets explicit and local

## Negative Tests

- **Malformed inputs**: tenant switch with stale preview state does not leak old comparison evidence into the new tenant context
- **Error paths**: preview mutation failure remains non-saving and save mutation success clears obsolete preview evidence
- **Boundary conditions**: zero-result preview, unchanged preview, and null parity rows remain correctly framed at the page level

## Steps

1. Review `console/src/app/(console)/policy/page.tsx` against the new form-level decision review and adjust only the page intro, handoff props, or state-reset semantics needed to keep compare-before-save framing coherent.
2. Preserve the existing bounded simulate payload (`limit: 50`, `changed_sample_limit: 5`), tenant-change reset, and save-success reset behavior unless a real mismatch with the decision flow appears.
3. Expand `console/src/components/policy/policy-page.test.tsx` to prove the page-level framing, non-saving preview contract, reset semantics, and anti-drift boundary still hold with the new comparison-and-decision UI.
4. Run the focused policy Vitest bundle and adjust until the form/page integration is stable.

## Must-Haves

- [ ] Preview and save remain separate mutations with explicit non-saving preview semantics.
- [ ] Tenant change and save success clear obsolete preview evidence.
- [ ] Page-level copy reinforces compare-before-save framing without adding dashboard or analytics language.
- [ ] Focused integration tests cover the real page entrypoint and bounded simulate payload.

## Verification

- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
- Page tests assert preview payload shape, explicit non-saving semantics, tenant-level framing, and reset behavior after save/tenant change.

## Observability Impact

- Signals added/changed: Focused page-level Vitest assertions for mutation separation, reset semantics, and bounded framing
- How a future agent inspects this: `src/components/policy/policy-page.test.tsx`
- Failure state exposed: Stale preview carryover, incorrect mutation wiring, or page-level scope drift appears as narrow integration-test failures

## Inputs

- `console/src/app/(console)/policy/page.tsx` — current tenant selection, simulation/save mutations, and reset behavior
- `console/src/components/policy/policy-page.test.tsx` — existing page-level policy framing and orchestration assertions
- `console/src/components/policy/policy-form.tsx` — task-one comparison-and-decision UI that the page composes

## Expected Output

- `console/src/app/(console)/policy/page.tsx` — page framing and orchestration aligned to compare-before-save flow
- `console/src/components/policy/policy-page.test.tsx` — integration assertions for page-level decision-flow composition and reset semantics

## Inputs

- ``console/src/app/(console)/policy/page.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/components/policy/policy-form.tsx``

## Expected Output

- ``console/src/app/(console)/policy/page.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Verification

npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

Focused page-level Vitest failures become the inspection surface for stale preview state, drifted page framing, or broken preview/save mutation separation.
