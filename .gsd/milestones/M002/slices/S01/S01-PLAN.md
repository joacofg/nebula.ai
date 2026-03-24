# S01: Operator structuring truth surface

**Goal:** Align the highest-impact operator-facing console surfaces with Nebula's existing runtime-truth production model so tenants, API-key scope, and operator-only evidence surfaces read consistently with the canonical docs.
**Demo:** In the console, an operator can issue or inspect API keys without guessing when `X-Nebula-Tenant-ID` is required, can recognize Playground as an operator-only corroboration surface rather than the public migration boundary, and can recognize Observability as the persisted explanation surface for recorded request outcomes and dependency health.

## Must-Haves

- API key issuance and inventory explicitly distinguish single-tenant inference from intentionally multi-tenant authorization using the existing `tenant_id` and `allowed_tenant_ids` model.
- Playground copy reinforces the admin-only, non-streaming, operator-corroboration role and does not teach it as the public adoption path.
- Observability copy reinforces that it is the persisted ledger and dependency-health explanation surface for recorded request outcomes.
- No touched console surface introduces `app` or `workload` as first-class runtime entities.
- Focused console tests assert the updated truth-surface wording and scope semantics.

## Proof Level

- This slice proves: integration
- Real runtime required: no
- Human/UAT required: no

## Verification

- `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx`
- `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx`
- `npm --prefix console run test -- --run src/app/(console)/observability/page.test.tsx`

## Observability / Diagnostics

- Runtime signals: existing request ids, route metadata, ledger terminal status, and dependency-health states remain the diagnostic anchors; this slice mainly clarifies their operator meaning in UI copy.
- Inspection surfaces: `console/src/app/(console)/playground/page.tsx`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/playground/playground-recorded-outcome.tsx`, and the usage-ledger/dependency-health UI.
- Failure visibility: targeted vitest assertions should fail when wording drifts away from tenant-scope semantics, operator-only framing, or persisted-outcome framing.
- Redaction constraints: preserve current secret boundaries; copy may describe API-key scope and request evidence but must not expose raw secrets beyond the existing one-time reveal flow.

## Integration Closure

- Upstream surfaces consumed: `src/nebula/services/auth_service.py`, `src/nebula/api/routes/admin.py`, `console/src/lib/admin-api.ts`, and the canonical production-model docs already cited by research.
- New wiring introduced in this slice: none beyond reusing existing admin API data in console copy and scope presentation.
- What remains before the milestone is truly usable end-to-end: S02 must add app/workload guidance without fake runtime entities, and S03 must assemble the integrated production-structuring walkthrough.

## Tasks

- [x] **T01: Clarify API key scope and tenant-header consequences in console key surfaces** `est:1.5h`
  - Why: The highest-risk operator contradiction is at API-key issuance and inventory, where current copy and table display underspecify when tenant inference works versus when callers must send `X-Nebula-Tenant-ID`.
  - Files: `console/src/app/(console)/api-keys/page.tsx`, `console/src/components/api-keys/create-api-key-dialog.tsx`, `console/src/components/api-keys/api-key-table.tsx`, `console/src/components/api-keys/create-api-key-dialog.test.tsx`, `console/src/components/api-keys/api-key-table.test.tsx`
  - Do: Update API Keys page framing, key-creation guidance, and table scope display so they expose the real `tenant_id` plus `allowed_tenant_ids` behavior without adding new backend fields or fake entities; add focused tests for single-tenant inference versus intentional multi-tenant authorization and the caller header consequence.
  - Verify: `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx`
  - Done when: An operator can read the API Keys screen and understand whether a key infers one tenant or requires public callers to send `X-Nebula-Tenant-ID`, and the updated semantics are asserted in component tests.
- [x] **T02: Reframe Playground and Observability as operator evidence surfaces** `est:1.5h`
  - Why: The remaining truth-surface risk is wording drift that makes Playground sound like the public integration boundary and Observability sound like a generic dashboard instead of the persisted explanation surface.
  - Files: `console/src/app/(console)/playground/page.tsx`, `console/src/components/playground/playground-form.tsx`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/playground/playground-form.test.tsx`, `console/src/components/playground/playground-page.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`
  - Do: Update Playground page and form copy to emphasize admin-only, non-streaming, tenant-selected operator corroboration; update Observability framing to emphasize persisted request outcomes plus dependency health; add or extend tests that lock this wording and preserve the immediate-response-versus-recorded-outcome distinction.
  - Verify: `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx src/app/(console)/observability/page.test.tsx`
  - Done when: Playground clearly reads as operator corroboration rather than the public client path, Observability clearly reads as the persisted explanation surface, and focused tests fail if that framing drifts.

## Files Likely Touched

- `console/src/app/(console)/api-keys/page.tsx`
- `console/src/components/api-keys/create-api-key-dialog.tsx`
- `console/src/components/api-keys/api-key-table.tsx`
- `console/src/app/(console)/playground/page.tsx`
- `console/src/components/playground/playground-form.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/components/api-keys/create-api-key-dialog.test.tsx`
- `console/src/components/api-keys/api-key-table.test.tsx`
- `console/src/components/playground/playground-form.test.tsx`
- `console/src/components/playground/playground-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
