# S02: App/workload guidance without fake runtime entities — Research

**Date:** 2026-03-23

## Summary

This slice primarily supports `R012` and must preserve the already-validated `R006` boundary: Nebula’s enforced entities are still tenant, tenant policy, API key, and operator admin session. The backend/admin contracts already prove that `app` and `workload` do **not** exist as first-class runtime objects: there are no `/v1/admin/apps` or `/v1/admin/workloads` routes, no app/workload fields in governance models, and tenant resolution still flows only through `tenant_id`, `allowed_tenant_ids`, and optional `X-Nebula-Tenant-ID`.

The implementation landscape suggests this is a light-to-targeted slice, mostly console-copy and test work. The strongest seam is the tenant surface: `console/src/app/(console)/tenants/page.tsx`, `console/src/components/tenants/tenant-table.tsx`, and `console/src/components/tenants/tenant-editor-drawer.tsx` currently present a generic “tenant operations / workspace” framing and expose freeform metadata, but they do not yet help operators map conceptual apps/workloads onto the existing tenant/key model. S01 already locked the API-key, Playground, and Observability truth boundary; S02 should build on that instead of reopening it.

## Recommendation

Add explicit operator guidance to the tenant-facing console surfaces explaining how teams should map apps and workloads onto Nebula today: use tenants as the enforceable boundary, use API-key names/scope for caller segmentation, and treat app/workload labels as naming/runbook conventions rather than product objects. Keep the guidance grounded in the runtime contracts already described in `docs/production-model.md` and reinforced in S01’s API-key copy.

Do this as copy-first UI refinement plus focused vitest coverage, not backend work. The relevant skill guidance is already available in-project: `react-best-practices` is the right pattern for touching Next.js/React components conservatively, and the M002 console truth-surface guardrail plus S01 forward-intelligence require that any new operator wording derive from existing runtime/admin contracts instead of inventing new fields or pseudo-entities.

## Implementation Landscape

### Key Files

- `docs/production-model.md` — canonical source for this slice’s truth boundary. Already states that app/workload are guidance only, lists what Nebula does **not** expose (`/v1/admin/apps`, `/v1/admin/workloads`, app/workload-keyed policy), and gives the allowed practical pattern: encode app/workload intent in tenant naming, API-key naming, or external runbooks.
- `console/src/app/(console)/tenants/page.tsx` — main tenant page shell. Current header says “Tenant operations” and only describes a “dense tenant control surface backed by /api/admin/tenants”; this is the best place for top-level structuring guidance that connects tenant management to conceptual app/workload planning.
- `console/src/components/tenants/tenant-table.tsx` — tenant inventory table. Currently shows id, name, status, updated time only. Natural place for concise per-row cues or preserved neutral labels, but avoid inventing runtime columns like app/workload.
- `console/src/components/tenants/tenant-editor-drawer.tsx` — create/edit drawer. It currently says “Create a workspace with governance metadata and an explicit active state.” That “workspace” wording is the most likely drift point; change it to runtime-truthful tenant guidance and use the existing `metadata` field only as optional operator notes, not as a hidden app/workload contract.
- `console/src/components/tenants/tenant-table.test.tsx` — existing focused tests for tenant table rendering/selection. Extend only if table copy or semantics change.
- `console/src/components/tenants/tenant-editor-drawer.test.tsx` — existing focused tests for tenant drawer behavior. Add assertions for new guidance text if the drawer becomes the main app/workload explanation surface.
- `console/src/components/api-keys/api-key-table.tsx` and `console/src/components/api-keys/create-api-key-dialog.tsx` — S01-established contract surfaces. Use these as wording anchors for tenant inference, `allowed_tenant_ids`, default `tenant_id`, and when `X-Nebula-Tenant-ID` is required.
- `src/nebula/models/governance.py` — authoritative proof that tenant and API key are real modeled entities and that no app/workload governance models exist.
- `src/nebula/api/routes/admin.py` — authoritative proof of current admin surface. It exposes tenants, policies, API keys, playground, and usage ledger only.
- `src/nebula/api/dependencies.py` — authoritative proof that public runtime tenant resolution still depends only on `X-Nebula-API-Key` plus optional `X-Nebula-Tenant-ID`.

### Build Order

1. Re-anchor the slice on runtime truth from `docs/production-model.md`, `src/nebula/models/governance.py`, and `src/nebula/api/routes/admin.py` so planner/executors do not accidentally add fake runtime concepts.
2. Update the tenant page shell (`console/src/app/(console)/tenants/page.tsx`) with the highest-level app/workload guidance first. This unlocks the page-level story and is the least risky place to make the production-structuring guidance visible.
3. Update the tenant drawer (`console/src/components/tenants/tenant-editor-drawer.tsx`) next, because its current “workspace” copy is the clearest wording seam that could mislead operators. Keep guidance explicit: tenant is enforced; app/workload belong in naming, metadata notes, and external operating conventions.
4. Touch `tenant-table.tsx` only if needed for coherence. Prefer minimal change here; avoid adding pseudo-entity columns.
5. Add focused vitest assertions around the changed copy so future drift is caught the same way S01 guarded API-key/Playground/Observability wording.

### Verification Approach

- Source verification:
  - Confirm no backend files need changes because the runtime/admin contract already supports the slice.
  - Confirm all operator wording still aligns with `docs/production-model.md` language: tenant enforceable, API key credential, app/workload guidance only.
- Console tests:
  - `npm --prefix console run test -- --run src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
  - If page-level copy gets a new test, run that targeted file too.
- Optional regression confidence:
  - Re-run the S01 truth-surface tests if tenant wording cross-references API-key semantics:
    - `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx`
- Observable behaviors to preserve:
  - No new app/workload routes, models, or request headers.
  - Tenant creation/editing still submits the same `TenantInput` shape.
  - API-key semantics remain tied to `tenant_id`, `allowed_tenant_ids`, and `X-Nebula-Tenant-ID`.

## Constraints

- Do not describe app/workload as first-class runtime entities unless implementation exists; current runtime/admin code exposes only tenants, policies, API keys, playground, and usage ledger.
- Do not repurpose tenant `metadata` into an implied product contract; it is freeform JSON, not an enforced app/workload schema.
- Preserve S01’s established truth boundary: API key scope language must continue to derive from `tenant_id` + `allowed_tenant_ids`, Playground stays admin-only/non-streaming corroboration, and Observability stays persisted request evidence plus dependency-health context.

## Common Pitfalls

- **Reintroducing fake entity language** — Avoid labels like “app record”, “workload object”, or “workspace” unless clearly marked as operator convention only.
- **Hiding guidance in backend assumptions** — This slice should not smuggle meaning into `metadata`; if metadata is mentioned, frame it as optional notes/runbook context rather than something Nebula enforces.
- **Drifting from public tenant-resolution rules** — Any tenant/app/workload guidance must still match the existing API-key behavior already locked by S01 tests.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Next.js / React console work | `react-best-practices` | available |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | installable via `npx skills add wshobson/agents@nextjs-app-router-patterns` |
| FastAPI admin/runtime contracts | `wshobson/agents@fastapi-templates` | installable via `npx skills add wshobson/agents@fastapi-templates` |
