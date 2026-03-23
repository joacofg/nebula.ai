---
estimated_steps: 4
estimated_files: 5
skills_used:
  - react-best-practices
---

# T01: Clarify API key scope and tenant-header consequences in console key surfaces

**Slice:** S01 — Operator structuring truth surface
**Milestone:** M002

## Description

Make the API Keys operator surface teach the real runtime model already enforced by Nebula. Executors should keep the existing backend contract intact and use the existing `tenant_id` and `allowed_tenant_ids` fields to explain the difference between a key that resolves one tenant automatically and a key that intentionally authorizes multiple tenants, which makes public callers send `X-Nebula-Tenant-ID`.

## Steps

1. Read `src/nebula/services/auth_service.py`, `console/src/app/(console)/api-keys/page.tsx`, `console/src/components/api-keys/create-api-key-dialog.tsx`, and `console/src/components/api-keys/api-key-table.tsx` to anchor the copy and display logic to the real tenant-resolution behavior.
2. Update the API Keys page header and create-key dialog copy so operators are told that API keys are client credentials, `allowed_tenant_ids` defines which tenants a key may use, and intentionally multi-tenant keys require public callers to send `X-Nebula-Tenant-ID`.
3. Replace the imprecise inventory display in `console/src/components/api-keys/api-key-table.tsx` with a clearer scope summary derived from existing fields, without adding new admin APIs or implying any `app` or `workload` runtime entity.
4. Extend `console/src/components/api-keys/create-api-key-dialog.test.tsx` and `console/src/components/api-keys/api-key-table.test.tsx` to assert the new operator guidance and the visible distinction between single-tenant inference and multi-tenant authorization.

## Must-Haves

- [ ] All API-key wording matches the actual resolution rule in `src/nebula/services/auth_service.py`: explicit tenant allowed, else `tenant_id`, else single allowed tenant, else `403` requiring `X-Nebula-Tenant-ID`.
- [ ] The API key table no longer hides scope semantics behind a generic label like `Scoped`.
- [ ] No new backend endpoint, no schema expansion, and no app/workload pseudo-entity language are introduced.

## Verification

- `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx`
- Manual review — `console/src/app/(console)/api-keys/page.tsx`, `console/src/components/api-keys/create-api-key-dialog.tsx`, and `console/src/components/api-keys/api-key-table.tsx` clearly explain tenant scope using existing fields only.

## Inputs

- `src/nebula/services/auth_service.py` — runtime tenant-resolution rule that UI wording must mirror
- `console/src/app/(console)/api-keys/page.tsx` — page-level operator framing to update
- `console/src/components/api-keys/create-api-key-dialog.tsx` — key issuance guidance to update
- `console/src/components/api-keys/api-key-table.tsx` — inventory scope display to refine
- `console/src/components/api-keys/create-api-key-dialog.test.tsx` — existing component tests to extend
- `console/src/components/api-keys/api-key-table.test.tsx` — existing table tests to extend

## Expected Output

- `console/src/app/(console)/api-keys/page.tsx` — updated page framing for runtime-truth key scope
- `console/src/components/api-keys/create-api-key-dialog.tsx` — updated issuance guidance tied to `allowed_tenant_ids`
- `console/src/components/api-keys/api-key-table.tsx` — clearer tenant-scope display derived from existing fields
- `console/src/components/api-keys/create-api-key-dialog.test.tsx` — assertions for key-scope guidance and submit semantics
- `console/src/components/api-keys/api-key-table.test.tsx` — assertions for visible single-tenant versus multi-tenant scope semantics
