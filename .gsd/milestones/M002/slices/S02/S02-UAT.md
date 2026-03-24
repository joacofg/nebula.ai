# S02 UAT — App/workload guidance without fake runtime entities

## Purpose

Verify that the Tenants console surfaces teach operators how to map conceptual apps and workloads onto Nebula's real tenant and API-key model without implying that app or workload are first-class runtime objects.

## Preconditions

1. Worktree is at the assembled S02 state.
2. Console test dependencies are installed (`npm --prefix console install` already completed in the environment that runs UAT).
3. The following focused tests are available:
   - `console/src/app/(console)/tenants/page.test.tsx`
   - `console/src/components/tenants/tenant-editor-drawer.test.tsx`
   - `console/src/components/tenants/tenant-table.test.tsx`
4. Operator reviewing the UI understands the canonical runtime truth from `docs/production-model.md`: tenants and API keys are enforced; app/workload are conceptual guidance only.

## Test Case 1 — Tenant page shell teaches the real boundary model

**Goal:** Confirm the Tenants page header explains the production structuring model in runtime-truthful terms.

### Steps

1. Run:
   `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx'`
2. Open `console/src/app/(console)/tenants/page.tsx` and inspect the header copy rendered by the page.
3. Confirm the page states that tenants are the enforced runtime boundary.
4. Confirm the page states that API keys segment which callers can reach each tenant.
5. Confirm the page states that app/workload names are team conventions captured in tenant names, key names, or notes.
6. Confirm the page ties the surface back to the real admin tenants endpoint rather than an invented abstraction.
7. Confirm the page does **not** use “workspace” wording.

### Expected outcomes

- The focused test passes.
- The rendered copy makes tenants, not apps/workloads, the authoritative object.
- The page tells operators where app/workload naming belongs without implying stored runtime app/workload objects.
- No “workspace” copy appears.

## Test Case 2 — Tenant editor drawer keeps metadata and creation guidance truthful

**Goal:** Confirm the create/edit drawer explains tenant creation and metadata without inventing schema or pseudo-entities.

### Steps

1. Run:
   `npm --prefix console run test -- --run src/components/tenants/tenant-editor-drawer.test.tsx`
2. Open `console/src/components/tenants/tenant-editor-drawer.tsx`.
3. Inspect the create-mode helper text.
4. Confirm it says creating a tenant creates a real tenant boundary for policy and attribution.
5. Confirm it says API keys are issued separately for callers.
6. Confirm the metadata helper text describes metadata as optional operator notes, ownership hints, or runbook context only.
7. Confirm it explicitly says Nebula does not enforce app/workload schema from metadata.
8. Confirm no “workspace” wording appears in the drawer.

### Expected outcomes

- The focused test passes.
- Create/edit guidance stays grounded in tenant and API-key runtime truth.
- Metadata is clearly positioned as optional notes, not structure.
- The drawer contains no language that could be read as an enforced app/workload model.

## Test Case 3 — Tenant table remains tenant-only and does not grow pseudo-entity semantics

**Goal:** Confirm the tenant inventory view did not silently reintroduce app/workload concepts as columns or visible structure.

### Steps

1. Run:
   `npm --prefix console run test -- --run src/components/tenants/tenant-table.test.tsx`
2. Open `console/src/components/tenants/tenant-table.test.tsx`.
3. Confirm the visible semantics being asserted are tenant-oriented (`Tenant ID`, `Active`, `Inactive`).
4. Confirm the test explicitly asserts the absence of `app` and `workload` column headers.

### Expected outcomes

- The focused test passes.
- The table remains a tenant inventory surface.
- There are no app/workload pseudo-entity columns or equivalent visible semantics.

## Test Case 4 — Full slice regression suite catches wording drift at the right seams

**Goal:** Confirm the slice-level verification command remains the authoritative regression suite for this guidance.

### Steps

1. Run:
   `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
2. Confirm all three test files execute.
3. Confirm the suite passes with 8 total tests.
4. If any test fails, identify whether the regression came from:
   - page shell copy
   - drawer helper text / metadata framing
   - table pseudo-entity drift

### Expected outcomes

- All 3 test files pass.
- The suite acts as the slice's observability surface for runtime-truth copy drift.
- Failures, if introduced later, point directly to the surface that violated the tenant/API-key truth contract.

## Edge Cases to review explicitly

### Edge Case A — App/workload words may appear, but only as guidance

- Acceptable: text that tells operators to treat app/workload as naming conventions or notes.
- Not acceptable: text that implies apps/workloads are created, stored, selected, or enforced by the tenant surfaces.

### Edge Case B — Metadata must not become an implied schema carrier

- Acceptable: metadata as notes, ownership hints, runbook context.
- Not acceptable: metadata described as a place to define workload routing, app structure, or enforced runtime grouping.

### Edge Case C — Legacy “workspace” wording must not return

- Acceptable: tenant, tenant boundary, API-key scope, admin endpoint.
- Not acceptable: workspace as the semantic label for tenant creation or editing.

## UAT verdict rule

Mark this slice UAT-ready when:

- all focused tenant-surface tests pass
- the page and drawer copy remain runtime-truthful on manual inspection
- no tenant surface implies app/workload are first-class runtime/admin objects
- metadata remains clearly optional and non-enforced
