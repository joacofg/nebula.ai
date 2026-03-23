# S03 UAT — Reference migration integration

## Purpose

Validate that Nebula now provides a believable, end-to-end migration proof for an existing OpenAI-style chat-completions caller, and that the migrated request can be verified from both the public response and the operator usage ledger.

## Preconditions

1. Worktree contains the S03 deliverables:
   - `docs/reference-migration.md`
   - `tests/test_reference_migration.py`
2. Python test environment is available and the repo venv exists at `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv`.
3. No file edits are pending that would invalidate the tested contract.
4. Reviewer has access to the repository docs and can read the test file.

## Test Case 1 — Canonical migration guide is discoverable from repo entry docs

**Goal:** Ensure adopters can find the migration proof without hunting or reopening contract/setup ambiguity.

### Steps

1. Open `README.md`.
2. Find the documentation map and quick-start sections.
3. Confirm `docs/reference-migration.md` is linked as the canonical migration proof.
4. Open `docs/quickstart.md`.
5. Confirm it points readers to `docs/reference-migration.md` after the first public request works.
6. Open `docs/reference-migration.md`.
7. Confirm it points back to:
   - `docs/quickstart.md` for setup
   - `docs/adoption-api-contract.md` for the public API contract
   - `docs/production-model.md` for tenant/operator/app/workload framing

### Expected outcomes

- The migration guide is easy to find from `README.md`.
- The quickstart hands off to the migration guide instead of duplicating it.
- The migration guide stays narrowly scoped and does not restate the full quickstart or contract.

## Test Case 2 — Migration guide shows an honest before/after diff

**Goal:** Ensure the human-facing example looks like a real migration rather than a toy demo.

### Steps

1. In `docs/reference-migration.md`, read the “Before”, “After”, and “Before/after diff” sections.
2. Verify the before example is a plausible OpenAI-style client call.
3. Verify the after example preserves the chat-completions call shape.
4. Confirm the primary caller changes are limited to:
   - Nebula base URL
   - `X-Nebula-API-Key`
   - optional `X-Nebula-Tenant-ID`
   - model selection appropriate for Nebula (`nebula-auto` in the example)
5. Confirm the guide explicitly says `X-Nebula-Tenant-ID` should **not** be sent on every request by default.

### Expected outcomes

- The before/after example reads like a credible migration path.
- The code diff is small and believable.
- The guide does not imply that callers must redesign request bodies or adopt a Nebula-only façade.

## Test Case 3 — Executable migration proof passes for the happy path

**Goal:** Confirm the repository contains runnable proof that a migrated caller reaches Nebula and preserves an OpenAI-like response.

### Steps

1. Run:
   - `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_reference_migration.py -q`
2. Review the test names in the output or in `tests/test_reference_migration.py`.
3. Inspect `test_reference_migration_proves_public_headers_and_usage_ledger_correlation`.
4. Confirm the test sends a public request to `POST /v1/chat/completions` using `X-Nebula-API-Key`.
5. Confirm the test asserts:
   - HTTP 200
   - `object == "chat.completion"`
   - assistant role/content in the response body
   - `X-Nebula-*` response headers
   - `X-Request-ID`
   - matching usage-ledger row returned by `GET /v1/admin/usage/ledger?request_id=...`

### Expected outcomes

- The test passes.
- The test proves both the application-facing response contract and the operator-facing correlation story.

## Test Case 4 — Tenant-header edge case behaves exactly as documented

**Goal:** Confirm `X-Nebula-Tenant-ID` is required only for intentionally ambiguous multi-tenant keys.

### Steps

1. Run:
   - `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_reference_migration.py -k "tenant_header or request_id or ledger" -q`
2. Inspect `test_reference_migration_requires_tenant_header_only_for_ambiguous_multi_tenant_keys`.
3. Confirm the test creates an API key with:
   - `tenant_id=None`
   - multiple `allowed_tenant_ids`
4. Confirm the test first omits `X-Nebula-Tenant-ID` and expects a `403` with `{"detail": "Tenant header is required for this API key."}`.
5. Confirm the test then retries with `X-Nebula-Tenant-ID: team-b` and expects success.
6. Confirm the successful request is again correlated through the usage ledger by `request_id`.

### Expected outcomes

- The targeted edge-case test passes.
- The runtime behavior matches the docs exactly.
- The failure mode is explicit and understandable.

## Test Case 5 — Slice-level regression suite passes with current runtime truth

**Goal:** Confirm the assembled slice still works when run with its supporting contract/header/governance coverage.

### Steps

1. Run:
   - `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_reference_migration.py tests/test_chat_completions.py tests/test_response_headers.py tests/test_governance_api.py -q`
2. Confirm the full command exits successfully.
3. Spot-check that the suite includes coverage for:
   - chat-completion response shape
n   - public route headers
   - ledger persistence and filtering
   - migration-specific request-id correlation
4. In `tests/test_governance_api.py`, verify the current runtime assumptions reflected by the passing suite:
   - `default_premium_model == "gpt-4o-mini"`
   - the explicit premium-request ledger scenario includes `("policy_denied", "denied")`

### Expected outcomes

- The full slice verification suite passes.
- The surrounding governance assertions are aligned with present runtime behavior.

## Test Case 6 — Migration verification instructions are concrete enough for a human operator

**Goal:** Ensure the docs tell an operator exactly how to prove a migrated request worked.

### Steps

1. Read the “How to confirm the migration worked” and “Minimal verification path” sections in `docs/reference-migration.md`.
2. Confirm the guide instructs the reader to verify:
   - the response still looks like a standard `chat.completion`
   - `X-Nebula-*` response headers
   - `X-Request-ID`
   - `GET /v1/admin/usage/ledger?request_id=...`
3. Confirm the guide lists concrete ledger fields to compare against the public response, including:
   - `request_id`
   - `tenant_id`
   - `requested_model`
   - `final_route_target`
   - `final_provider`
   - `cache_hit`
   - `fallback_used`
   - `route_reason`
   - `policy_outcome`
   - `terminal_status`

### Expected outcomes

- A reviewer can follow the guide without inventing extra debugging steps.
- The public-to-operator verification loop is concrete and repeatable.

## Edge Cases to Review

### Edge Case A — Missing tenant header for ambiguous key
- Expected: `403` with `Tenant header is required for this API key.`
- Expected: no route-level `X-Nebula-*` success headers are emitted before tenant resolution succeeds.

### Edge Case B — Bootstrap-style single-tenant path
- Expected: public request succeeds with only `X-Nebula-API-Key`.
- Expected: tenant is inferred automatically and exposed in `X-Nebula-Tenant-ID`.

### Edge Case C — Public proof must not be replaced by admin-only surfaces
- Expected: docs explicitly say Playground is useful for inspection but is not the migration target.
- Expected: the canonical proof remains the public `POST /v1/chat/completions` route plus ledger correlation.

## UAT verdict criteria

Mark S03 accepted when all of the following are true:

- the migration guide is discoverable and compositionally correct
- the before/after example feels like a real migration, not a toy rewrite
- the executable migration proof passes
- the ambiguous multi-tenant-key edge case passes exactly as documented
- the slice-level regression suite passes
- the docs provide a concrete public-response-to-ledger verification path
