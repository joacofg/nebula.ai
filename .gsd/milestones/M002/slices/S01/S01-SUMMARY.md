# S01: Operator structuring truth surface — Summary

## Slice Outcome

S01 delivered the highest-impact operator truth-surface alignment promised by M002: the console now tells the same runtime-truthful tenant and API-key story as the canonical production-model docs, while Playground and Observability are framed as distinct operator evidence surfaces instead of generic product marketing surfaces.

The slice removed the main contradiction called out in the roadmap: operators no longer have to guess when Nebula infers tenant context from an API key versus when a public caller must send `X-Nebula-Tenant-ID`. It also tightened the console trust boundary so Playground reads as an admin-only, non-streaming corroboration path and Observability reads as the persisted explanation surface for recorded request outcomes plus dependency-health context.

## What This Slice Actually Delivered

### 1. Runtime-aligned API key scope semantics in operator surfaces

Updated API key surfaces now expose the real behavior already enforced by runtime/auth logic:

- `console/src/app/(console)/api-keys/page.tsx` frames API keys as client credentials with explicit tenant-resolution consequences.
- `console/src/components/api-keys/create-api-key-dialog.tsx` explains how `tenant_id` and `allowed_tenant_ids` interact, including when multi-tenant keys require `X-Nebula-Tenant-ID`.
- `console/src/components/api-keys/api-key-table.tsx` replaces generic scope language with concrete tenant-scope summaries:
  - default `tenant_id` auto-resolves that tenant
  - one allowed tenant is inferred automatically
  - multiple allowed tenants without a default require `X-Nebula-Tenant-ID`

This was done without backend changes or new pseudo-entities.

### 2. Playground reframed as operator corroboration, not public integration

Updated Playground copy now explicitly preserves the existing contract boundary:

- `console/src/app/(console)/playground/page.tsx` presents Playground as an operator corroboration sandbox using the active admin session.
- `console/src/components/playground/playground-form.tsx` now describes an operator-selected, admin-session, non-streaming request path.
- The immediate-response versus later recorded-ledger split remains intact.

This matters because M001 already established that Playground is not the public migration boundary. S01 makes that legible in product wording.

### 3. Observability reframed as persisted request evidence plus runtime context

Updated Observability copy now describes the surface in the terms operators actually need:

- `console/src/app/(console)/observability/page.tsx` now leads with “Persisted request evidence”.
- The dependency-health section is explicitly framed as supporting runtime context rather than a replacement for ledger evidence.

This keeps Observability aligned with the ledger-first proof model established earlier in the program.

### 4. Focused regression tests that lock the truth surface

The slice added or aligned targeted vitest coverage for every touched surface:

- `console/src/components/api-keys/create-api-key-dialog.test.tsx`
- `console/src/components/api-keys/api-key-table.test.tsx`
- `console/src/components/playground/playground-form.test.tsx`
- `console/src/components/playground/playground-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`

These tests now fail if wording drifts away from:

- tenant inference vs explicit tenant-header semantics
- operator-only Playground framing
- persisted-evidence Observability framing

## Verification

### Slice-level verification

Passed:

- `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx`
- `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx`
- `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`

Consolidated rerun also passed:

- `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'`

### Observability / diagnostics confirmation

Confirmed at the source and test layer:

- Playground still shows immediate request metadata first and recorded outcome only after ledger persistence.
- Observability now clearly reads as persisted request evidence with dependency health as supporting context.
- Existing runtime signals remain unchanged: request ids, route metadata, terminal status, and dependency-health states are still the underlying anchors.

## Patterns Established

- Derive operator-facing scope language from the real runtime/admin contract, not from aspirational UX labels.
- For API keys, visible scope summaries should come from `tenant_id` and `allowed_tenant_ids` only.
- For operator evidence surfaces, preserve the split between immediate corroboration and persisted explanation:
  - Playground = immediate admin corroboration
  - Observability = persisted request evidence + dependency-health context
- Lock operator trust-boundary wording with focused component tests instead of relying on broad end-to-end coverage alone.

## Decisions / Notable Changes

- No new backend fields, entities, or admin APIs were introduced.
- No console surface in this slice introduced `app` or `workload` as runtime objects.
- The slice reinforced existing runtime truth rather than expanding product scope.
- A new decision was recorded in `.gsd/DECISIONS.md` to keep operator truth surfaces grounded in existing runtime/admin contracts.

## Requirement Impact

- `R006` remains validated and now has stronger product-surface proof, not just documentation proof.
- `R011`, `R012`, `R013`, and `R014` remain deferred.
- This slice does not claim embeddings support or first-class app/workload runtime entities.

## What S02 Should Know

S02 can now assume a stable, console-visible truth surface for:

- tenant scope
- API key behavior
- tenant-header requirements
- operator-only evidence boundaries

That means downstream work should not reopen:

- whether multi-tenant key behavior needs new entities
- whether Playground is a public integration path
- whether Observability is just a generic dashboard

Instead, S02 should build app/workload guidance on top of this established rule set:

- tenants, policies, API keys, and operator surfaces are real enforced/admin entities
- app/workload language must stay guidance-only unless runtime implementation exists

## Residual Risks / Follow-on Work

- S01 aligned the highest-impact console surfaces, but not the full end-to-end production-structuring walkthrough; S03 still needs to assemble the integrated story.
- S02 still needs to prove that app/workload guidance can help teams structure real deployments without implying those are first-class runtime objects.
- If future console copy changes touch operator scope or evidence framing, the focused tests added here should be treated as contract-level guardrails.

## Files Touched by the Slice

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

## Final Assessment

S01 achieved its slice goal. The biggest production-structuring contradiction in operator-facing product surfaces is removed, and the resulting console wording now matches Nebula’s runtime-truth tenant/API-key model closely enough for downstream slices to build on it.