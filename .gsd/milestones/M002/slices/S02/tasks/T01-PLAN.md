---
estimated_steps: 4
estimated_files: 3
skills_used:
  - react-best-practices
---

# T01: Reframe tenant surfaces around runtime-truth app/workload guidance

**Slice:** S02 — App/workload guidance without fake runtime entities
**Milestone:** M002

## Description

Update the tenant-facing console copy so operators can map conceptual apps and workloads onto Nebula’s real tenant and API-key model without the UI implying that app/workload are first-class runtime objects. Keep the implementation copy-first and grounded in the existing canonical operating model.

## Steps

1. Read `docs/production-model.md` and the existing tenant-facing console wording in `console/src/app/(console)/tenants/page.tsx`, `console/src/components/tenants/tenant-editor-drawer.tsx`, and `console/src/components/tenants/tenant-table.tsx` to anchor the copy in the current runtime/admin contract.
2. Update `console/src/app/(console)/tenants/page.tsx` so the page header explains that tenants are the enforced boundary, API keys help segment callers, and app/workload labels are team conventions rather than product objects unless implemented later.
3. Update `console/src/components/tenants/tenant-editor-drawer.tsx` to remove the current “workspace” framing, describe tenant creation/editing in runtime-truthful terms, and frame `metadata` only as optional operator notes or runbook context rather than an enforced schema.
4. Touch `console/src/components/tenants/tenant-table.tsx` only if needed for wording coherence, and do not add app/workload columns, fields, or pseudo-entity semantics.

## Must-Haves

- [ ] Tenant page copy explicitly helps operators apply app/workload concepts through tenants and API keys while preserving the canonical runtime truth from `docs/production-model.md`.
- [ ] Tenant drawer copy no longer uses “workspace” language and does not imply that `metadata` is an app/workload contract.
- [ ] No touched tenant surface invents app/workload routes, fields, or enforced runtime objects.

## Verification

- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
- Manual review — confirm the changed page and drawer copy mention tenants/API keys as real boundaries and keep app/workload guidance conceptual only.

## Inputs

- `docs/production-model.md` — canonical operating-model language defining tenants and API keys as real boundaries and app/workload as guidance only
- `console/src/app/(console)/tenants/page.tsx` — tenant page shell that needs the top-level structuring guidance
- `console/src/components/tenants/tenant-editor-drawer.tsx` — tenant creation/editing surface with the misleading “workspace” copy
- `console/src/components/tenants/tenant-table.tsx` — existing tenant inventory surface to keep coherent without adding fake entity semantics

## Expected Output

- `console/src/app/(console)/tenants/page.tsx` — page header copy aligned to the runtime-truth tenant/API-key/app-workload guidance
- `console/src/components/tenants/tenant-editor-drawer.tsx` — drawer copy aligned to tenant reality and optional metadata notes framing
- `console/src/components/tenants/tenant-table.tsx` — unchanged or minimally adjusted wording only if needed for coherence
