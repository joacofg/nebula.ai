---
id: S02
parent: M002
milestone: M002
provides:
  - Runtime-truth tenant-surface guidance that shows operators how to map conceptual apps and workloads onto Nebula's real tenant and API-key model without inventing enforced app/workload objects.
requires:
  - slice: S01
    provides: Stable operator-facing tenant/API-key/runtime-truth framing for downstream guidance surfaces.
affects:
  - S03
key_files:
  - console/src/app/(console)/tenants/page.tsx
  - console/src/app/(console)/tenants/page.test.tsx
  - console/src/components/tenants/tenant-editor-drawer.tsx
  - console/src/components/tenants/tenant-editor-drawer.test.tsx
  - console/src/components/tenants/tenant-table.test.tsx
key_decisions:
  - Tenant-facing console guidance should teach teams to represent apps and workloads through tenant names, API key names, and optional notes instead of pretending those are first-class runtime objects.
patterns_established:
  - For copy-heavy runtime-truth surfaces, pair positive text assertions with negative drift checks (for example, absence of workspace/app/workload pseudo-entity wording) rather than broad snapshots.
  - Keep tenant metadata framed as optional operator notes, ownership hints, or runbook context only; do not imply enforced app/workload schema unless implementation exists.
observability_surfaces:
  - Focused vitest assertions in console/src/app/(console)/tenants/page.test.tsx, console/src/components/tenants/tenant-editor-drawer.test.tsx, and console/src/components/tenants/tenant-table.test.tsx
  - Slice verification command: npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx
drill_down_paths:
  - .gsd/milestones/M002/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S02/tasks/T02-SUMMARY.md
duration: 35m
verification_result: passed
completed_at: 2026-03-23T21:05:19-03:00
---

# S02: App/workload guidance without fake runtime entities

## Outcome

S02 completed the tenant-facing part of M002's production-structuring story. The Tenants page and tenant editor drawer now teach operators that tenants remain Nebula's enforced runtime boundary, API keys are the mechanism for segmenting callers, and app/workload naming stays conceptual unless Nebula implements real objects later. The slice did not add new runtime entities or schemas; it made the existing tenant/admin surfaces more truthful and more usable.

## What This Slice Actually Delivered

- Reframed `console/src/app/(console)/tenants/page.tsx` so the page header explicitly explains:
  - tenants are the enforced boundary for policy, request attribution, and usage
  - API keys segment which callers can reach each tenant
  - app and workload names should be carried through tenant names, key names, or notes rather than treated as product objects
  - the page is grounded in the real admin tenants endpoint rather than an invented higher-level abstraction
- Reworked `console/src/components/tenants/tenant-editor-drawer.tsx` so create/edit guidance is runtime-truthful:
  - removed misleading “workspace” framing
  - describes tenant creation as creating a real tenant boundary for policy and attribution
  - frames `metadata` strictly as optional operator notes, ownership hints, or runbook context
  - explicitly states that Nebula does not enforce app/workload schema from metadata
- Added and/or confirmed focused regression coverage across the tenant shell, drawer, and table:
  - `console/src/app/(console)/tenants/page.test.tsx`
  - `console/src/components/tenants/tenant-editor-drawer.test.tsx`
  - `console/src/components/tenants/tenant-table.test.tsx`
- Locked adjacent semantics so the table cannot silently drift toward fake runtime entities by asserting the absence of app/workload pseudo-entity columns.

## Verification

### Slice-level verification

Passed:

- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`

Result: 3 test files passed, 8 tests passed.

### Observability / diagnostic surface check

The slice plan defined focused Vitest assertions as the inspection surface and failure visibility mechanism. Those surfaces are present and working:

- page test catches drift in tenant/API-key/app-workload explanatory copy
- drawer test catches drift in create/edit guidance, metadata framing, and removal of workspace language
- table test catches drift that would introduce app/workload pseudo-entity semantics into the tenant inventory view

## Requirement impact

- `R012` remains **deferred**. S02 proved that Nebula can give actionable app/workload structuring guidance in admin surfaces without promoting those concepts into first-class runtime/admin entities. That resolves the immediate ambiguity risk without claiming the deferred capability itself has been implemented.
- This slice also strengthens the lived evidence behind `R006` by extending the production-model truth story into the Tenants surface, though `R006` was already historically validated before this slice.

## Patterns and lessons for downstream slices

- When the product truth is mostly wording and operator framing, narrow text assertions plus explicit absence checks are a better guardrail than snapshots.
- Tenant guidance should stay anchored to real enforcement points already visible in the product: tenant records, API-key scope, and admin endpoints. Avoid introducing convenience nouns that sound like stored/enforced entities.
- If a planner assumes a verification surface already exists, verify that assumption locally. In this slice, `console/src/app/(console)/tenants/page.test.tsx` had to be created in T01 before the contract could actually be locked.
- Metadata is now a canonical “optional notes/runbook context” field on the tenant surface. S03 should preserve that framing instead of turning metadata into implied structure.

## What S03 should know

S03 can now rely on a stable tenant-surface explanation for app/workload mapping:

- tenants are the real boundary
- API keys carry caller scope
- `X-Nebula-Tenant-ID` rules still belong to the tenant/API-key story from S01
- app/workload language is guidance only unless runtime implementation changes

That means S03 should assemble the end-to-end production-structuring walkthrough by composing canonicals and console surfaces around this exact boundary, not by adding new conceptual objects or restating tenant semantics differently on each screen.

## Files changed in assembled slice state

- `console/src/app/(console)/tenants/page.tsx`
- `console/src/app/(console)/tenants/page.test.tsx`
- `console/src/components/tenants/tenant-editor-drawer.tsx`
- `console/src/components/tenants/tenant-editor-drawer.test.tsx`
- `console/src/components/tenants/tenant-table.test.tsx`
- `.gsd/milestones/M002/slices/S02/tasks/T01-PLAN.md`
- `.gsd/milestones/M002/slices/S02/tasks/T02-PLAN.md`

## UAT status

No human-run UAT was required to mark the slice complete, but a concrete UAT script has been written in `/.gsd/milestones/M002/slices/S02/S02-UAT.md` for downstream review and milestone assembly.
