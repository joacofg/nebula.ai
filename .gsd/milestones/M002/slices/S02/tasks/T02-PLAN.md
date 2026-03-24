---
estimated_steps: 4
estimated_files: 3
skills_used:
  - react-best-practices
  - test
---

# T02: Add tenant-surface regression tests for app/workload truth boundaries

**Slice:** S02 — App/workload guidance without fake runtime entities
**Milestone:** M002

## Description

Lock the updated tenant-surface guidance with focused vitest coverage so future changes cannot drift back toward fake app/workload entities or contradict the tenant/API-key behavior already established by the canonical production model and S01.

## Steps

1. Read the updated tenant UI copy from `console/src/app/(console)/tenants/page.tsx`, `console/src/components/tenants/tenant-editor-drawer.tsx`, and any touched tenant table copy from T01 before changing tests.
2. Create `console/src/app/(console)/tenants/page.test.tsx` with a focused render test that asserts the page frames tenants as the enforced boundary and app/workload language as conceptual guidance tied to tenants and API keys.
3. Extend `console/src/components/tenants/tenant-editor-drawer.test.tsx` to assert the new create/edit guidance, including that metadata is described as optional notes/runbook context rather than an enforced app/workload schema.
4. Update `console/src/components/tenants/tenant-table.test.tsx` only if T01 changed visible table semantics; keep the assertions narrow and tied to the real tenant surface instead of generic snapshots.

## Must-Haves

- [ ] `console/src/app/(console)/tenants/page.test.tsx` exists and fails if the page stops presenting tenants as the real boundary for operator structuring.
- [ ] Drawer tests fail if misleading workspace language or fake app/workload enforcement language returns.
- [ ] Any table assertions remain focused on visible tenant semantics and do not require pseudo-entity UI that this slice intentionally avoids.

## Verification

- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
- `test -f 'console/src/app/(console)/tenants/page.test.tsx'`

## Inputs

- `console/src/app/(console)/tenants/page.tsx` — updated tenant page copy under test
- `console/src/components/tenants/tenant-editor-drawer.tsx` — updated tenant drawer copy under test
- `console/src/components/tenants/tenant-editor-drawer.test.tsx` — existing drawer test file to extend with wording assertions
- `console/src/components/tenants/tenant-table.tsx` — tenant table surface whose semantics may need regression coverage
- `console/src/components/tenants/tenant-table.test.tsx` — existing table test file to keep aligned with any visible changes

## Expected Output

- `console/src/app/(console)/tenants/page.test.tsx` — new focused tenant page truth-surface test
- `console/src/components/tenants/tenant-editor-drawer.test.tsx` — extended drawer regression coverage for runtime-truth guidance
- `console/src/components/tenants/tenant-table.test.tsx` — unchanged or minimally updated table regression coverage aligned to the final UI
