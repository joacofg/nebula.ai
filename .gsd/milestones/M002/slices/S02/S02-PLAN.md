# S02: App/workload guidance without fake runtime entities

**Goal:** Make the tenant-facing console surfaces show operators how to map conceptual apps and workloads onto Nebula’s real tenant and API-key model without implying that app or workload are first-class runtime objects.
**Demo:** On the Tenants page, an operator can read concrete guidance that tenants remain the enforced boundary, API keys carry caller scope, and app/workload naming belongs in conventions or notes rather than fake product objects.

## Must-Haves

- Tenant-facing console copy explains how teams should apply app/workload concepts using tenants and API keys while preserving the runtime truth established in `docs/production-model.md` and S01.
- Tenant creation/editing surfaces stop using misleading “workspace” or pseudo-entity language and frame metadata as optional operator notes rather than an enforced app/workload schema.
- Focused console tests lock the new guidance so future wording changes cannot reintroduce fake runtime entities or drift from tenant-header/API-key semantics.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx'`
- `npm --prefix console run test -- --run src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`

## Observability / Diagnostics

- Runtime signals: UI copy and form guidance rendered from the tenant page and drawer components
- Inspection surfaces: focused vitest assertions in `console/src/app/(console)/tenants/page.test.tsx`, `console/src/components/tenants/tenant-editor-drawer.test.tsx`, and `console/src/components/tenants/tenant-table.test.tsx`
- Failure visibility: failing text assertions identify which operator surface drifted away from the tenant/API-key/runtime-truth contract
- Redaction constraints: no secrets; keep examples and assertions limited to public copy and existing admin field names

## Integration Closure

- Upstream surfaces consumed: `docs/production-model.md`, `console/src/app/(console)/api-keys/page.tsx`, `console/src/app/(console)/tenants/page.tsx`, `console/src/components/tenants/tenant-editor-drawer.tsx`, `console/src/components/tenants/tenant-table.tsx`
- New wiring introduced in this slice: a new tenant page test plus copy alignment between the tenant page shell and tenant drawer
- What remains before the milestone is truly usable end-to-end: S03 still needs to assemble the full production-structuring walkthrough across docs and operator surfaces

## Tasks

- [x] **T01: Reframe tenant surfaces around runtime-truth app/workload guidance** `est:45m`
  - Why: The slice’s user-facing value lives in the tenant page and drawer, where current wording is generic or misleading and does not yet teach operators how to map apps/workloads onto real tenants and keys.
  - Files: `console/src/app/(console)/tenants/page.tsx`, `console/src/components/tenants/tenant-editor-drawer.tsx`, `console/src/components/tenants/tenant-table.tsx`
  - Do: Update the tenant page header copy to explain that tenants are the enforced boundary, API keys segment callers, and app/workload naming stays conceptual unless implemented; replace the drawer’s “workspace” language with runtime-truthful tenant guidance; mention `metadata` only as optional notes/runbook context; touch the tenant table only if needed to keep the wording coherent without adding fake columns or pseudo-entities.
  - Verify: `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
  - Done when: the tenant page and drawer visibly teach the operator how to structure apps/workloads with tenants and keys, and no touched tenant surface implies that app/workload are real runtime objects.
- [x] **T02: Add tenant-surface regression tests for app/workload truth boundaries** `est:40m`
  - Why: S01 established that operator trust surfaces must be locked with targeted tests; this slice needs the same guardrails so future copy changes do not reintroduce fake entities.
  - Files: `console/src/app/(console)/tenants/page.test.tsx`, `console/src/components/tenants/tenant-editor-drawer.test.tsx`, `console/src/components/tenants/tenant-table.test.tsx`
  - Do: Add a new page-level test for the tenant shell copy, extend drawer tests to assert the new runtime-truth guidance and metadata framing, and update the tenant table test only if any visible semantics change; keep assertions anchored to tenants, API-key scope, and the absence of first-class app/workload wording.
  - Verify: `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
  - Done when: targeted vitest coverage fails on wording drift that would misrepresent app/workload as enforced objects or contradict tenant/API-key behavior.

## Files Likely Touched

- `console/src/app/(console)/tenants/page.tsx`
- `console/src/app/(console)/tenants/page.test.tsx`
- `console/src/components/tenants/tenant-editor-drawer.tsx`
- `console/src/components/tenants/tenant-editor-drawer.test.tsx`
- `console/src/components/tenants/tenant-table.tsx`
- `console/src/components/tenants/tenant-table.test.tsx`
