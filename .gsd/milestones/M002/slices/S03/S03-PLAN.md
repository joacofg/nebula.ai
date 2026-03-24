# S03: Integrated production-structuring walkthrough

**Goal:** Assemble one runtime-truthful production-structuring walkthrough that lets an operator move from tenant/API-key structuring guidance to public-request proof and admin corroboration without inventing new product entities or boundaries.
**Demo:** A reader can follow the canonicals and matching console truth surfaces in one coherent order: choose tenant and API-key structure, understand when `X-Nebula-Tenant-ID` is required, send the public request, correlate `X-Request-ID` and `X-Nebula-*` headers to the usage ledger, then use Playground and Observability only as operator corroboration surfaces.

## Must-Haves

- The assembled walkthrough explicitly composes `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`, and `docs/integrated-adoption-proof.md` into one end-to-end operator story without duplicating or contradicting their canonical roles.
- The integrated proof keeps the public route first, preserves the conditional `X-Nebula-Tenant-ID` rule, and reinforces that tenants/API keys are enforced while app/workload remain guidance only.
- Focused verification proves the linked console surfaces still match the walkthrough order and wording boundaries for tenant structuring, Playground corroboration, and Observability persisted explanation.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: no
- Human/UAT required: yes

## Verification

- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'`
- `test -s docs/integrated-adoption-proof.md && test -s .gsd/milestones/M002/slices/S03/S03-UAT.md`
- `rg -n "X-Nebula-Tenant-ID|Playground|Observability|usage ledger|tenant" docs/integrated-adoption-proof.md .gsd/milestones/M002/slices/S03/S03-UAT.md`

## Observability / Diagnostics

- Runtime signals: existing `X-Request-ID`, `X-Nebula-*` headers, usage-ledger records, Playground request metadata, and Observability dependency-health context remain the diagnostic anchors this slice composes.
- Inspection surfaces: `docs/integrated-adoption-proof.md`, `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`, `console/src/app/(console)/tenants/page.tsx`, `console/src/app/(console)/playground/page.tsx`, and `console/src/app/(console)/observability/page.tsx` plus their focused Vitest files.
- Failure visibility: drift appears as contradictory wording, missing proof-order steps, or failing focused Vitest assertions on tenant boundaries, immediate-vs-persisted evidence, and operator/admin-only corroboration semantics.
- Redaction constraints: keep secrets and sample credentials out of docs/UAT; refer only to key names and request identifiers, never actual secret values.

## Integration Closure

- Upstream surfaces consumed: `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`, `docs/integrated-adoption-proof.md`, `console/src/app/(console)/tenants/page.tsx`, `console/src/components/tenants/tenant-editor-drawer.tsx`, `console/src/app/(console)/playground/page.tsx`, `console/src/components/playground/playground-form.tsx`, `console/src/app/(console)/observability/page.tsx`
- New wiring introduced in this slice: documentation-level composition of the canonical operator flow plus a human-readable integrated UAT artifact that exercises the same story order against the existing console proof surfaces.
- What remains before the milestone is truly usable end-to-end: nothing

## Tasks

- [x] **T01: Tighten the canonical integrated walkthrough** `est:40m`
  - Why: S03 is the final assembly slice, so the first increment must make the end-to-end production-structuring story explicit in the canonical docs rather than leaving the operator to infer how the pieces fit together.
  - Files: `docs/integrated-adoption-proof.md`, `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`
  - Do: Update `docs/integrated-adoption-proof.md` so it clearly starts with tenant/API-key structuring grounded in `docs/production-model.md`, then walks the operator through the public request, conditional `X-Nebula-Tenant-ID` rule, usage-ledger correlation, Playground corroboration, and Observability corroboration without restating full contract/setup details from the canonicals.
  - Verify: `test -s docs/integrated-adoption-proof.md && rg -n "production-model|X-Nebula-Tenant-ID|usage ledger|Playground|Observability" docs/integrated-adoption-proof.md`
  - Done when: the integrated proof reads as one ordered production-structuring walkthrough, keeps the public route first, and links back to the existing canonicals for detailed contract/runtime truth.
- [x] **T02: Lock the integrated story with focused proof and operator UAT** `est:45m`
  - Why: The slice is only complete if the console truth surfaces still corroborate the assembled walkthrough and there is an explicit integrated acceptance script a human can follow.
  - Files: `.gsd/milestones/M002/slices/S03/S03-UAT.md`, `console/src/app/(console)/tenants/page.test.tsx`, `console/src/components/tenants/tenant-editor-drawer.test.tsx`, `console/src/components/tenants/tenant-table.test.tsx`, `console/src/components/playground/playground-form.test.tsx`, `console/src/components/playground/playground-page.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`
  - Do: Add an integrated UAT/read-through artifact that mirrors the canonical proof order and tighten focused Vitest assertions only where needed so the Tenants, Playground, and Observability surfaces explicitly back the walkthrough without pseudo-entity drift or boundary confusion.
  - Verify: `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx' && test -s .gsd/milestones/M002/slices/S03/S03-UAT.md`
  - Done when: the integrated UAT exists, the focused console tests pass, and an operator can trace the same story from tenant structuring through persisted evidence without the console implying new runtime objects.

## Files Likely Touched

- `docs/integrated-adoption-proof.md`
- `.gsd/milestones/M002/slices/S03/S03-UAT.md`
- `console/src/app/(console)/tenants/page.test.tsx`
- `console/src/components/tenants/tenant-editor-drawer.test.tsx`
- `console/src/components/tenants/tenant-table.test.tsx`
- `console/src/components/playground/playground-form.test.tsx`
- `console/src/components/playground/playground-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
