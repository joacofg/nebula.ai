# S04: Durable evidence correlation

**Goal:** Make the existing embeddings request-id evidence path intentionally inspectable through Nebula’s operator surfaces so a team can explain the same public `POST /v1/embeddings` request via durable backend/operator proof without adding new storage or helper layers.
**Demo:** An operator can take the `X-Request-ID` from the S03 embeddings migration proof, find the matching usage-ledger row in Observability, see that it is an embeddings request, and inspect enough persisted metadata to explain the outcome while preserving the metadata-only boundary.

## Must-Haves

- The slice directly advances active requirement `R023` by making the public embeddings request → durable evidence correlation path easier to inspect and explain from existing backend/operator surfaces.
- Observability supports intentional embeddings evidence discovery, including route-target filtering that can surface `final_route_target="embeddings"` rows instead of treating embeddings as an unfilterable special case.
- The request-detail surface exposes the persisted fields needed to explain the same embeddings request coherently, including request identity and route/outcome metadata already stored in the usage ledger.
- Verification proves both the durable backend truth and the operator corroboration path for embeddings without introducing raw input/vector persistence, a new API family, or a console-first proof model.
- The slice stays inside the milestone guardrail that supports `R024`: reuse the existing usage-ledger/admin API path and narrow Observability updates only.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx`
- `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx`
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`
- `npm --prefix console run playwright test e2e/observability.spec.ts`
- `rg -n 'embeddings' console/src/components/ledger console/src/app/\(console\)/observability console/e2e/observability.spec.ts tests/test_embeddings_reference_migration.py -S`
- `! rg -n 'input|embedding\"|embeddings\"' console/src/components/ledger console/src/lib/admin-api.ts tests/test_embeddings_reference_migration.py -g '!docs/**'`

## Observability / Diagnostics

- Runtime signals: public embeddings requests emit `X-Request-ID` plus the existing `X-Nebula-*` headers, and the durable row remains the usage-ledger record keyed by `request_id` with `final_route_target`, `terminal_status`, `route_reason`, `policy_outcome`, provider, model, and timestamp metadata.
- Inspection surfaces: `GET /v1/admin/usage/ledger?request_id=...`, the Observability page at `console/src/app/(console)/observability/page.tsx`, the ledger filter controls, and the request-detail card are the supported operator inspection path.
- Failure visibility: embeddings request explanation must remain localizable through request id, route target `embeddings`, terminal status, route reason, and policy outcome in both tests and operator UI; failures should show up as targeted test/e2e assertion breaks rather than requiring source spelunking.
- Redaction constraints: no raw embeddings `input`, returned vectors, or new payload-capture fields may be added to ledger-facing types, UI, or proofs.

## Integration Closure

- Upstream surfaces consumed: `tests/test_embeddings_reference_migration.py`, `src/nebula/api/routes/embeddings.py`, `src/nebula/api/routes/admin.py`, `console/src/lib/admin-api.ts`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/ledger/*`
- New wiring introduced in this slice: Observability explicitly recognizes embeddings ledger rows and renders the persisted explanation fields needed to correlate the same request shown by the migration proof.
- What remains before the milestone is truly usable end-to-end: S05 must assemble the contract, migration, and evidence artifacts into one final adoption package and re-check the milestone guardrails.

## Tasks

- [x] **T01: Make embeddings ledger rows intentionally discoverable in Observability** `est:45m`
  - Why: R023 is not credibly satisfied if embeddings evidence exists only in backend truth but the operator surface cannot intentionally filter to embeddings rows.
  - Files: `console/src/components/ledger/ledger-filters.tsx`, `console/src/components/ledger/ledger-filters.test.tsx`, `console/src/app/(console)/observability/page.tsx`, `console/src/lib/admin-api.ts`
  - Do: Update the shared ledger filter surface so embeddings is a first-class route-target option, keep the existing admin API query path unchanged, and add focused unit coverage that proves an operator can select embeddings filtering without widening the filter model or inventing a new admin endpoint.
  - Verify: `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx`
  - Done when: the Observability filter controls can intentionally request embeddings rows through the existing usage-ledger API contract and the focused test locks that behavior.
- [x] **T02: Expose embeddings request explanation fields in the ledger detail surface** `est:55m`
  - Why: Filtering to the right row is not enough; the selected row must show enough persisted metadata for an operator to explain the same embeddings request coherently.
  - Files: `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/components/ledger/ledger-table.tsx`, `console/src/components/ledger/ledger-table.test.tsx`, `console/src/lib/admin-api.ts`
  - Do: Expand the request-detail rendering to include the persisted identity/context fields most relevant to embeddings correlation — request id, tenant, route target, requested/response model, status, timestamp, provider, route reason, policy outcome, and existing fallback/cache/token metadata — while preserving the metadata-only boundary and keeping the ledger table aligned with row selection behavior.
  - Verify: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx && npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx`
  - Done when: selecting an embeddings row reveals the durable explanation fields an operator needs, and component tests lock the visible contract without introducing raw payload data.
- [ ] **T03: Add end-to-end operator proof for embeddings evidence correlation** `est:1h`
  - Why: The slice only closes at integration proof level if the same embeddings evidence path works across the executable migration proof and the actual Observability UI, not just isolated components.
  - Files: `console/e2e/observability.spec.ts`, `tests/test_embeddings_reference_migration.py`, `docs/embeddings-reference-migration.md`, `console/src/components/ledger/ledger-filters.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`
  - Do: Extend the Observability Playwright scenario with an embeddings ledger row that can be filtered and inspected, assert the route target, request id, and persisted explanation fields explicitly, and align the migration-proof/doc wording if needed so the operator corroboration path still reads as subordinate to the public request + ledger truth rather than a new primary proof surface.
  - Verify: `npm --prefix console run playwright test e2e/observability.spec.ts && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py && rg -n 'X-Request-ID|/v1/admin/usage/ledger|Observability|request id' docs/embeddings-reference-migration.md tests/test_embeddings_reference_migration.py console/e2e/observability.spec.ts`
  - Done when: one executable browser proof shows an operator can filter to an embeddings request and inspect the same durable evidence sequence already established by the migration test, with no new storage or helper stack.

## Files Likely Touched

- `console/src/components/ledger/ledger-filters.tsx`
- `console/src/components/ledger/ledger-filters.test.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/lib/admin-api.ts`
- `console/e2e/observability.spec.ts`
- `tests/test_embeddings_reference_migration.py`
- `docs/embeddings-reference-migration.md`
