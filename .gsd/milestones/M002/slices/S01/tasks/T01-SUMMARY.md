---
id: T01
parent: S01
milestone: M002
provides:
  - Runtime-aligned API key scope guidance across the console page, creation dialog, and inventory table.
key_files:
  - console/src/app/(console)/api-keys/page.tsx
  - console/src/components/api-keys/create-api-key-dialog.tsx
  - console/src/components/api-keys/api-key-table.tsx
  - console/src/components/api-keys/create-api-key-dialog.test.tsx
  - console/src/components/api-keys/api-key-table.test.tsx
key_decisions:
  - Derived visible scope summaries entirely from existing tenant_id and allowed_tenant_ids fields instead of adding backend fields or pseudo-entities.
patterns_established:
  - When console copy explains auth behavior, mirror AuthService resolution order explicitly and lock wording with focused vitest assertions.
observability_surfaces:
  - Focused vitest assertions for API-key scope wording; manual inspection of API Keys page header, create dialog guidance, and Tenant Scope column.
duration: 25m
verification_result: passed
completed_at: 2026-03-23T20:52:00-03:00
blocker_discovered: false
---

# T01: Clarify API key scope and tenant-header consequences in console key surfaces

**Clarified API key tenant scope in the console so operators can see when Nebula infers a tenant versus when callers must send `X-Nebula-Tenant-ID`.**

## What Happened

I first fixed the task-plan observability gap by adding an `Observability Impact` section that explains the operator-visible signal and the tests that protect it. Then I read `src/nebula/services/auth_service.py` and aligned the console wording to the real resolution rule: explicit allowed tenant header wins, otherwise `tenant_id`, otherwise the single allowed tenant, otherwise the request is rejected until the caller sends `X-Nebula-Tenant-ID`.

On `console/src/app/(console)/api-keys/page.tsx`, I rewrote the header copy so the page frames API keys as client credentials, explains what `allowed_tenant_ids` means, and states when `tenant_id` acts as the default for callers that omit the tenant header. On `console/src/components/api-keys/create-api-key-dialog.tsx`, I expanded the issuance guidance so operators are told how `allowed_tenant_ids` and `tenant_id` interact and why intentionally multi-tenant keys without a default tenant require the public caller to provide `X-Nebula-Tenant-ID`.

On `console/src/components/api-keys/api-key-table.tsx`, I replaced the generic `Scoped` display with a derived `Tenant Scope` summary. The table now distinguishes three runtime-true cases: a key with `tenant_id` auto-resolves that default tenant, a key with exactly one allowed tenant infers that tenant automatically, and a key with multiple allowed tenants but no default requires `X-Nebula-Tenant-ID`. I extended the focused component tests to lock this copy and these visible distinctions.

## Verification

I ran the task-level vitest command for the two touched API-key components and both passed. I also ran the remaining slice verification commands to make sure this task did not regress adjacent console copy: the playground tests still passed unchanged, while the observability command failed because the referenced `console/src/app/(console)/observability/page.test.tsx` file does not exist in the local checkout.

Manual review also confirms the touched API key page, dialog, and table explain tenant scope using only the existing `tenant_id` and `allowed_tenant_ids` fields, with no new backend API and no app/workload runtime language.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx` | 0 | ✅ pass | 1.22s |
| 2 | `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx` | 0 | ✅ pass | 1.03s |
| 3 | `npm --prefix console run test -- --run src/app/(console)/observability/page.test.tsx` | 1 | ❌ fail | 0.00s (file missing locally; Vitest reported no test files found) |
| 4 | Manual review — `console/src/app/(console)/api-keys/page.tsx`, `console/src/components/api-keys/create-api-key-dialog.tsx`, and `console/src/components/api-keys/api-key-table.tsx` | 0 | ✅ pass | 0.00s |

## Diagnostics

Inspect `src/nebula/services/auth_service.py` for the canonical resolution order, then compare it with the operator copy in `console/src/app/(console)/api-keys/page.tsx`, `console/src/components/api-keys/create-api-key-dialog.tsx`, and the `Tenant Scope` summaries in `console/src/components/api-keys/api-key-table.tsx`. Future drift should surface quickly through `console/src/components/api-keys/create-api-key-dialog.test.tsx` and `console/src/components/api-keys/api-key-table.test.tsx`.

## Deviations

None in the shipped implementation. The only mismatch was verification-related: the slice-level observability command references `console/src/app/(console)/observability/page.test.tsx`, but that test file is absent in the current worktree.

## Known Issues

- The slice verification command for `console/src/app/(console)/observability/page.test.tsx` cannot pass in this worktree because the referenced file does not exist locally. This is a pre-existing plan/path mismatch unrelated to T01.

## Files Created/Modified

- `.gsd/milestones/M002/slices/S01/tasks/T01-PLAN.md` — added the missing `Observability Impact` section required by the execution contract.
- `.gsd/milestones/M002/slices/S01/tasks/T01-SUMMARY.md` — recorded the task outcome, verification evidence, and the missing observability-test path mismatch.
- `.gsd/milestones/M002/slices/S01/S01-PLAN.md` — marked T01 as complete.
- `console/src/app/(console)/api-keys/page.tsx` — reframed the API Keys page around client credentials, tenant defaults, and tenant-header consequences.
- `console/src/components/api-keys/create-api-key-dialog.tsx` — added runtime-truth issuance guidance for `tenant_id`, `allowed_tenant_ids`, and `X-Nebula-Tenant-ID`.
- `console/src/components/api-keys/api-key-table.tsx` — replaced the generic scope label with explicit tenant-scope summaries derived from existing fields.
- `console/src/components/api-keys/create-api-key-dialog.test.tsx` — added assertions for the new operator guidance and submission semantics.
- `console/src/components/api-keys/api-key-table.test.tsx` — added assertions for single-tenant inference, multi-tenant header requirements, and revoked-record visibility.
