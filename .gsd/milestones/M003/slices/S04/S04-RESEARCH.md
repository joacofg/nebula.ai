# M003/S04 — Research

**Date:** 2026-03-23

## Summary

S04 is targeted research, not deep exploration. The core durable evidence path for embeddings already exists in backend runtime truth: `src/nebula/api/routes/embeddings.py` records metadata-only usage ledger rows keyed by `X-Request-ID`, and S03 already proved public `POST /v1/embeddings` → response headers → `GET /v1/admin/usage/ledger?request_id=...` correlation in `tests/test_embeddings_reference_migration.py`. The remaining slice work is therefore about making that same correlation path easier to explain and inspect through existing operator surfaces, not inventing new storage, new helper stacks, or console-first truth.

R023 is the active requirement this slice owns. R024 is a milestone guardrail this slice supports. The implementation should follow the established proof-order rule from project knowledge: public embeddings request first, then immediate `X-Request-ID` / `X-Nebula-*` evidence, then durable usage-ledger correlation, with operator surfaces used only as corroboration. The existing Playground/Observability console patterns from M001/M002 already match this shape for chat; S04 should reuse those patterns narrowly for embeddings evidence explanation, preserving the metadata-only persistence boundary and avoiding any new entity/model expansion.

## Recommendation

Use the existing usage-ledger and request-id correlation as the durable source of truth, and add only enough operator-surface and test coverage to make embeddings evidence inspectable and explainable. Concretely: keep backend persistence unchanged unless a missing field blocks operator explanation; extend the Observability/ledger presentation and focused tests so embeddings rows (`final_route_target="embeddings"`) show the same explanatory fields already relied on by the migration proof; add one embeddings-focused console/browser verification path if needed to prove that an operator can inspect the correlated row.

This follows the loaded guidance from the `agent-browser` skill only insofar as browser verification should end with explicit assertions, not prose inference, and it follows the project knowledge guardrails more importantly: Playground is immediate corroboration, Observability is the persisted explanation surface, and neither should replace the public request + ledger proof sequence. Avoid new console pages, new APIs, or new persistence of raw input/vector data.

## Implementation Landscape

### Key Files

- `src/nebula/api/routes/embeddings.py` — already the authoritative embeddings evidence producer. It records usage-ledger rows via `_record_usage(...)` for success and failure branches and sets the public `X-Nebula-*` headers on success. Current persisted fields are request id, tenant id, requested/response model, route/provider, fallback/cache flags, token counts, status, route reason, and policy outcome. This is likely sufficient for S04 unless operator explanation proves a gap.
- `src/nebula/api/routes/admin.py` — exposes `GET /v1/admin/usage/ledger` with filters for `request_id`, `tenant_id`, `terminal_status`, `route_target`, and time range. If S04 needs richer correlation, this is the stable admin API seam; prefer extending filters/shape here over inventing a second evidence endpoint.
- `src/nebula/services/governance_store.py` — persistence/query implementation for `record_usage(...)` and `list_usage_records(...)`. Natural backend seam if S04 needs ledger-query behavior changes. Current query filtering already supports `request_id` and `route_target`, which aligns well with embeddings evidence.
- `src/nebula/db/models.py` — `UsageLedgerModel` schema. Treat this as high-cost to change. Only touch if a concrete evidence gap cannot be solved through existing metadata fields.
- `src/nebula/models/governance.py` — `UsageLedgerRecord` public/admin shape. If backend evidence needs one more metadata field exposed to operator surfaces, add it here and wire through store/API together.
- `tests/test_embeddings_reference_migration.py` — current executable source of truth for public embeddings correlation. S04 should build on this rather than duplicating the same proof elsewhere.
- `tests/test_embeddings_api.py` — focused backend route coverage for embeddings happy path, auth reuse, validation failure, and upstream error mapping. Good place for any additional assertions about durable evidence semantics if backend behavior changes.
- `console/src/app/(console)/observability/page.tsx` — existing operator persisted-evidence surface. It already fetches usage-ledger rows and shows request detail plus dependency health. This is the most likely console surface for embeddings durable evidence correlation.
- `console/src/components/ledger/ledger-table.tsx` — current ledger inventory view. Today it shows timestamp, tenant, route target, provider, status, latency, and cost. It is suitable for embeddings row discoverability already because `final_route_target` is displayed.
- `console/src/components/ledger/ledger-request-detail.tsx` — current per-request persisted explanation card. It shows provider, route reason, policy outcome, fallback/cache, and token counts. This is the likely place to make embeddings outcomes clearer if the current generic labels are not sufficient.
- `console/src/lib/admin-api.ts` — shared console API client. `UsageLedgerRecord` type and `listUsageLedger(...)` / `getUsageLedgerEntry(...)` are already present, so UI work should stay on these helpers rather than using ad hoc fetches.
- `console/src/app/(console)/playground/page.tsx` + `console/src/components/playground/playground-metadata.tsx` + `console/src/components/playground/playground-recorded-outcome.tsx` — existing M001/M002 chat proof composition. Important mainly as a pattern reference: immediate response evidence first, then persisted outcome. Do not copy this into a new embeddings-only playground unless there is a proven trust gap.
- `console/e2e/observability.spec.ts` — current end-to-end operator verification for the observability page. Natural seam for embeddings-specific operator proof if S04 needs browser-level verification.
- `console/src/components/ledger/ledger-table.test.tsx` — focused component coverage for ledger rows.
- `docs/embeddings-reference-migration.md` and `docs/embeddings-adoption-contract.md` — already document the public proof path and canonical contract. S04 may need a small evidence-oriented update or cross-link, but should not create a second competing contract document.

### Natural Seams

1. **Backend evidence seam**: `embeddings.py` → `UsageLedgerRecord` → `governance_store.py` → admin ledger API. Only touch if some operator-visible fact needed for embeddings correlation is not already preserved.
2. **Operator UI seam**: observability ledger table/detail components. Best place to improve inspectability without widening scope.
3. **Proof seam**: focused backend pytest stays the source of truth for request-id correlation; console/unit/e2e tests only corroborate that operators can inspect the same persisted evidence.
4. **Docs seam**: small pointer updates only. If documentation changes, keep them subordinate to the existing canonical embeddings contract and migration proof.

### Current Gaps / Constraints

- There is no embeddings-specific operator surface today; Observability is generic. That is probably acceptable for R023 if the generic ledger detail is clear enough, but the planner should inspect whether embeddings rows need slightly better wording or coverage to be self-explanatory.
- `LedgerFilters` currently hard-codes route targets to `["cache", "local", "premium", "denied"]` and terminal statuses to chat-oriented values. This is the most obvious concrete gap for S04 because embeddings rows use `final_route_target="embeddings"` and may otherwise be harder to filter intentionally in the operator UI. This looks like the likeliest slice change.
- `TerminalStatus` in `src/nebula/models/governance.py` already includes `provider_error`, which covers the embeddings error branches; no obvious schema problem there.
- `ledger-request-detail.tsx` does not currently show request model, response model, route target, tenant, timestamp, or request id beyond the heading. If the operator story for embeddings needs stronger “same request” explanation, this component is the cheapest expansion point.
- The proof-order guardrail matters: do not reposition Observability as the primary proof. Any console work should read as “inspect the persisted row for the same request id,” not “trust the console on its own.”
- The `agent-browser` skill suggests explicit final assertions for UI verification. If browser/UAT automation is added, finish with targeted assertions against request id, route target `embeddings`, and persisted reason/outcome strings.

### Build Order

1. **Confirm the operator evidence gap precisely** — inspect whether the existing Observability UI can intentionally surface embeddings rows today. The hard-coded route-target filter is the first likely blocker and should be resolved before any broader UI polish.
2. **If needed, extend the minimal operator UI** — update ledger filters/detail rendering to make embeddings request correlation explicit without adding a new page or new data model.
3. **Lock focused tests** — add/adjust Vitest coverage for the new filter/detail behavior and, if warranted, an observability Playwright scenario with embeddings ledger rows. Keep backend pytest minimal unless backend fields actually change.
4. **Only then touch docs** — if the UI proof surface changes materially, add a small pointer/update in existing embeddings proof docs. Do not create a new canonical contract source.

### Verification

Backend / proof:

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`

Console unit tests (focused):

- `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx`
- `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx`
- `npm --prefix console run test -- --run src/components/playground/playground-page.test.tsx`
  - mainly as regression protection if shared usage-ledger types/helpers change

Console e2e / operator corroboration:

- `npm --prefix console run playwright test e2e/observability.spec.ts`
  - if updated for embeddings, assert filterability and detail visibility for an embeddings ledger row explicitly

Artifact/source checks:

- `rg -n "embeddings" console/src/components/ledger console/src/app/\(console\)/observability docs tests -S`
- Verify no new persistence of raw `input`, `inputs`, `embedding`, or `embeddings` fields is introduced into ledger-facing shapes/tests.

### Skill Discovery

Directly relevant installed skills already available:

- `agent-browser` — relevant if the executor chooses browser/UAT verification for the Observability surface. No install needed.
- `test` — relevant for generating/running focused Vitest or Playwright coverage. No install needed.

No additional external skill discovery looks necessary for this slice because the work is standard FastAPI + React/Next + Playwright/Vitest work already established in this repo.
