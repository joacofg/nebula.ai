# S01 — Research

**Date:** 2026-03-23

## Summary

S01 primarily serves R012 and materially supports the already-validated production-boundary requirement R006 by retiring the highest-risk contradiction between the canonical docs and the operator console. The docs are already quite explicit: `docs/production-model.md`, `docs/quickstart.md`, and `docs/reference-migration.md` consistently say that tenant, policy, API key, and operator admin session are the real enforced entities; `app` and `workload` remain guidance only; and `X-Nebula-Tenant-ID` is required only for intentionally multi-tenant keys. The larger remaining risk is product-surface wording drift, not missing backend behavior.

The console already uses the real runtime model mechanically, but several high-impact operator surfaces underspecify or slightly blur the truth surface. Playground currently reads as a generic “routing sandbox” even though docs require it to read as an operator-only corroboration surface. API Keys exposes the right fields (`tenant_id`, `allowed_tenant_ids`) but does not explain the key runtime consequence: multi-tenant authorization is an operator choice that makes the public caller send `X-Nebula-Tenant-ID`. Observability centers on ledger filters and dependency health, but its current copy does not explicitly anchor itself as the persisted explanation surface for tenant/routing outcomes.

## Recommendation

Treat this slice as targeted operator-surface alignment, not a runtime redesign. Follow the existing M001 documentation rule (keep docs canonical and make product surfaces reinforce them) and update the highest-impact console copy/components first: Playground, API key issuance/inventory, and Observability. The backend model and enforcement already support the intended story, so the first proof should be that the UI tells the same runtime-truth model the docs already tell.

Implementation should prefer copy, labeling, and small presentational-field additions over new entities or new admin APIs. In particular, keep tenant as the authoritative enforced object, explicitly present `allowed_tenant_ids` as the source of multi-tenant scope, and avoid introducing any app/workload selectors, records, or implied first-class objects in the console. This matches the loaded `react-best-practices` skill guidance to make targeted component changes around existing data flow rather than widening state/API surfaces, and the milestone constraint that app/workload must not be promoted to runtime objects unless implementation exists.

## Implementation Landscape

### Key Files

- `docs/production-model.md` — canonical runtime-truth reference. Already states the exact S01 story: tenant/policy/API key/admin session are real, app/workload are conceptual only, and tenant-header requirements depend on API-key scope.
- `docs/quickstart.md` — canonical operator/public-path walkthrough. Already distinguishes `X-Nebula-API-Key` vs `X-Nebula-Admin-Key`, bootstrap vs tenant-scoped keys, and when `X-Nebula-Tenant-ID` is required.
- `docs/reference-migration.md` — canonical migration proof. Already establishes that `X-Nebula-Tenant-ID` is not default and is only required for ambiguous multi-tenant keys.
- `src/nebula/services/auth_service.py` — authoritative runtime rule for tenant resolution. Planner/executors should treat this as the source of truth: explicit tenant must be allowed; otherwise infer from `tenant_id`; otherwise infer from single `allowed_tenant_ids`; otherwise fail with `403 "Tenant header is required for this API key."`.
- `src/nebula/db/models.py` — confirms the real enforced data model: `ApiKeyModel.tenant_id` plus `allowed_tenant_ids_json`; no app/workload models exist.
- `src/nebula/api/routes/admin.py` — admin/product surface contract. Exposes tenants, policies, API keys, Playground completions, and usage ledger; no app/workload admin resources exist.
- `console/src/lib/admin-api.ts` — typed console contract layer. Contains the exact frontend shapes for `ApiKeyRecord`, `PlaygroundCompletionResult`, and `UsageLedgerRecord`; this is the seam for any UI enrichment that reuses existing API data.
- `console/src/app/(console)/playground/page.tsx` — top-level Playground framing. Current header copy says “Prompt routing sandbox” and “Run prompt requests through the live Nebula routing path with the active operator session.” This is accurate but not yet explicitly anchored to the canonical “operator corroboration, non-public boundary” story.
- `console/src/components/playground/playground-form.tsx` — operator input copy. Current form text says “Choose a tenant, set the target model, and send a single prompt through Nebula.” Natural place to clarify that tenant selection here is an operator-chosen execution context, not a public caller header tutorial.
- `console/src/components/playground/playground-metadata.tsx` — immediate response evidence component. Already aligns with M001/S05 proof ordering (“Immediate response evidence” before ledger write); likely only needs wording refinement.
- `console/src/components/playground/playground-recorded-outcome.tsx` — persisted evidence component. Already aligns well with the “recorded outcome” / ledger corroboration story.
- `console/src/app/(console)/api-keys/page.tsx` — top-level API key inventory framing. Good candidate for adding the production-structuring explanation that keys are client credentials and that multi-tenant scope changes caller requirements.
- `console/src/components/api-keys/create-api-key-dialog.tsx` — most important key-issuance truth surface. It already exposes `tenant_id` and `allowed_tenant_ids`; copy should explain the relationship between those fields and public `X-Nebula-Tenant-ID` requirements.
- `console/src/components/api-keys/api-key-table.tsx` — inventory table. Currently shows `tenant_id ?? "Scoped"`, which is imprecise for production structuring because “Scoped” hides the difference between single-tenant inference and multi-tenant authorization. Strong candidate for a small display improvement.
- `console/src/app/(console)/observability/page.tsx` — top-level persisted-evidence framing. Should be aligned to docs/knowledge wording: Observability is the persisted explanation surface for recorded request outcomes and dependency-health context.
- `console/src/components/ledger/ledger-filters.tsx` — filter form. Already runtime-truthful and probably needs no structural change.
- `console/src/components/ledger/ledger-table.tsx` — usage list showing tenant, route target, provider, status, latency, cost. This is already runtime-truthful and likely only needs surrounding copy, not schema changes.
- `console/src/components/ledger/ledger-request-detail.tsx` — detailed persisted explanation for one request. Already presents provider, route reason, policy outcome, fallback/cache, and token data; good evidence surface for S01 without API changes.
- `console/src/components/playground/playground-page.test.tsx` — existing Playground truth-surface tests. Good seam for wording assertions or preserved evidence ordering.
- `console/src/components/playground/playground-form.test.tsx` — verifies Playground interaction text/behavior.
- `console/src/components/api-keys/create-api-key-dialog.test.tsx` — verifies `allowed_tenant_ids` behavior and should be extended if copy or scope-display behavior changes.

### Build Order

1. **Prove the runtime truth boundary from backend/admin contracts first** — use `src/nebula/services/auth_service.py`, `src/nebula/db/models.py`, and `src/nebula/api/routes/admin.py` as the hard source of truth. This locks the planner onto what the UI is allowed to claim and avoids scope drift into fake app/workload entities.
2. **Align API key surfaces next** — this is the highest-value contradiction to remove because it directly affects production caller behavior (`X-Nebula-Tenant-ID` required vs not required). The create dialog and API-key table are the clearest operator education seam.
3. **Align Playground framing after key scope language is settled** — Playground should reinforce that it is an operator-only, non-streaming corroboration surface running under admin trust, not the public migration boundary.
4. **Tighten Observability framing last** — its data is already truthful; this is mainly copy-level alignment once the primary tenant/key model is explicit elsewhere.
5. **Then add/refresh focused console tests** — prefer component/page tests for wording and visible scope semantics instead of broad E2E work.

### Verification Approach

- Console unit tests for touched components/pages:
  - `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx`
  - `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx`
  - `npm --prefix console run test -- --run src/components/playground/playground-page.test.tsx`
  - add a targeted test for `console/src/components/api-keys/api-key-table.tsx` if table semantics change
- If multiple touched files share the same area, run the narrower vitest slice first, then `make console-test` if the environment is healthy.
- For backend truth preservation, a planner may optionally run targeted pytest coverage around tenant resolution or migration behavior if wording changes raise doubt, but S01 currently looks doc/UI-heavy rather than behavior-changing.
- Manual observable checks in the console should confirm:
  - API key issuance explains single-tenant vs multi-tenant scope in terms of caller header requirements
  - Playground explicitly reads as an operator surface, not the public adoption boundary
  - Observability reads as the persisted ledger/dependency-health explanation surface
  - no console copy introduces app/workload as first-class resources

## Constraints

- `app` and `workload` are not first-class runtime objects anywhere in code or admin APIs; S01 must not add wording that implies otherwise.
- The real tenant-selection rule is already enforced in `AuthService.resolve_tenant_context()`; UI copy must match that exact behavior.
- Playground is admin-only and non-streaming by implementation (`/v1/admin/playground/completions` rejects `stream=true`); copy should reinforce this rather than soften it.
- Console changes should reuse existing typed admin data from `console/src/lib/admin-api.ts`; there is no evidence that new backend endpoints are needed for S01.

## Common Pitfalls

- **Hiding multi-tenant semantics behind generic wording** — labels like `tenant_id ?? "Scoped"` obscure whether a key is inferable or ambiguous. Prefer copy/display that exposes how `tenant_id` and `allowed_tenant_ids` interact.
- **Accidentally teaching Playground as the migration path** — the docs explicitly reserve the public migration proof for `POST /v1/chat/completions`; Playground should stay framed as operator corroboration.
- **Using app/workload language as if it were data-model truth** — keep such terms advisory only unless the UI is clearly describing team conventions rather than runtime enforcement.

## Open Risks

- The current admin API record shape for API keys may be just barely sufficient for a stronger table display; if a clearer scope summary is needed and cannot be derived from `tenant_id` + `allowed_tenant_ids`, a small API/UI extension may surface during execution.
- There may be additional operator-surface wording drift outside the initially inspected pages (for example trust-boundary or tenants/policy pages), so planners should leave room for one follow-up sweep after primary changes land.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Next.js | `react-best-practices` | installed / available |
| React | `react-best-practices` | installed / available |
| FastAPI | `wshobson/agents@fastapi-templates` | available via `npx skills add wshobson/agents@fastapi-templates` |

