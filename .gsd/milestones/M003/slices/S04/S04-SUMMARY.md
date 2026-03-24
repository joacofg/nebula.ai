# S04: Durable evidence correlation — Summary

## Slice Summary

**Status:** Complete
**Milestone:** M003
**Slice Goal:** Make the existing embeddings request-id evidence path intentionally inspectable through Nebula’s operator surfaces so a team can explain the same public `POST /v1/embeddings` request via durable backend/operator proof without adding new storage or helper layers.

### What this slice actually delivered

S04 closed the embeddings evidence gap by making the existing metadata-only usage-ledger path intentionally usable from Observability instead of leaving embeddings correlation as backend truth that only tests or direct API queries could see.

The assembled result is:

- public embeddings requests still emit `X-Request-ID` plus `X-Nebula-*` headers
- the durable record is still the existing usage-ledger row keyed by `request_id`
- Observability can now intentionally filter to `final_route_target="embeddings"`
- the ledger table exposes `request_id` directly so operators can visually match the public header to the persisted row
- the request-detail card now renders the persisted explanation fields needed to explain the outcome coherently: request id, timestamp, tenant, route target, terminal status, requested/response model, provider, route reason, policy outcome, fallback/cache flags, and token counts
- the Playwright proof and migration guide now treat Observability as corroboration of the same durable row rather than a replacement proof source

This means the S03 migration proof now has a concrete operator-side continuation: take the `X-Request-ID` from the public `/v1/embeddings` response, query the ledger, then corroborate that same row in Observability by filtering to embeddings and inspecting the same persisted metadata.

### Key implementation patterns established

1. **Extend shared ledger surfaces instead of creating embeddings-specific UI paths.**
   Embeddings discoverability was added by extending the shared route-target options list with `embeddings`, keeping the existing `routeTarget -> route_target` admin API contract unchanged.

2. **Explain richer request outcomes from existing metadata-only fields.**
   The request-detail and table surfaces were expanded from `UsageLedgerRecord` rather than from any new schema, storage layer, or payload capture path.

3. **Keep request-id correlation visible before drill-down.**
   The table now includes a `Request ID` column so operators can match the public `X-Request-ID` before opening the detail card.

4. **Keep Observability subordinate to the public request + ledger proof order.**
   The migration guide and browser proof preserve the sequence: public `/v1/embeddings` request -> `X-Request-ID`/`X-Nebula-*` headers -> `GET /v1/admin/usage/ledger?request_id=...` -> Observability corroboration.

### Scope/guardrail outcome

S04 stayed within the M003 guardrails:

- no new storage
- no new admin API family
- no embeddings-specific backend schema
- no raw `input` persistence
- no returned vector persistence
- no helper stack or SDK layer
- no console-first proof model

The slice strengthens requirement `R023` while still supporting `R024`’s milestone-wide constraint discipline.

### Verification run for close-out

#### Passed
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `rg -n 'embeddings' console/src/components/ledger console/src/app/\(console\)/observability console/e2e/observability.spec.ts tests/test_embeddings_reference_migration.py -S`

#### Environment gaps / non-blocking verification caveats
- `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx` could not be rerun in this close-out environment because the console Vitest runner was not provisioned (`vitest` missing from `console/node_modules/.bin`).
- `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx` hit the same missing-runner environment gap.
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` hit the same missing-runner environment gap.
- `npm --prefix console run playwright test e2e/observability.spec.ts` could not be rerun in this close-out environment because the local Playwright runner was not provisioned.
- The negative grep from the plan (`! rg -n 'input|embedding"|embeddings"' ...`) is not a reliable regression gate in this repo because it matches legitimate fixtures/assertions and unrelated `*Input` type names; the actual redaction boundary is better proved by the migration test assertions and the fact that `UsageLedgerRecord` contains only metadata fields.

### Requirement impact

- **R023** moved from **active** to **validated**.
  S04 now proves that the same public embeddings request can be correlated through durable backend truth and operator corroboration without adding payload capture or a new helper/admin surface.

### Files and surfaces future slices should rely on

- `tests/test_embeddings_reference_migration.py` — source-of-truth executable public request + ledger correlation proof
- `docs/embeddings-reference-migration.md` — human-readable proof sequence and corroboration framing
- `console/src/components/ledger/ledger-filters.tsx` — shared embeddings route-target filter option
- `console/src/components/ledger/ledger-table.tsx` — request-id-visible row inventory/selection surface
- `console/src/components/ledger/ledger-request-detail.tsx` — metadata-only persisted explanation surface
- `console/e2e/observability.spec.ts` — UI corroboration contract for embeddings evidence

### What S05 should know

S05 should assemble, not reinvent. The contract, migration, and evidence story now exists in three distinct layers:

1. `docs/embeddings-adoption-contract.md` for the narrow public boundary
2. `tests/test_embeddings_reference_migration.py` + `docs/embeddings-reference-migration.md` for the realistic caller swap and durable ledger proof
3. Observability ledger filter/detail surfaces for operator corroboration of the same request id and persisted row

When S05 assembles the milestone, it should preserve the proof order and keep Observability as a secondary persisted-evidence surface rather than elevating it above the public response and usage-ledger correlation path.

## UAT Summary

A human evaluator should be able to:

1. Send a real `POST /v1/embeddings` request.
2. Capture `X-Request-ID` and relevant `X-Nebula-*` headers.
3. Query `GET /v1/admin/usage/ledger?request_id=...` and confirm the row is metadata-only.
4. Open Observability, filter `Route target = embeddings`, select the matching row, and explain the outcome from the visible persisted fields.
5. Confirm neither raw embedding inputs nor returned vectors appear in the durable evidence surfaces.
