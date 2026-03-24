# UAT — M003/S02: Canonical embeddings contract docs

## Preconditions
- Worktree is the assembled M003/S02 state.
- Python test environment is available at `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python`.
- Reader has access to these files:
  - `docs/embeddings-adoption-contract.md`
  - `README.md`
  - `docs/architecture.md`
  - `src/nebula/api/routes/embeddings.py`
  - `tests/test_embeddings_api.py`
  - `tests/test_governance_api.py`
  - `tests/test_service_flows.py`

## Test Case 1 — Canonical embeddings contract doc exists and reads as a real contract
1. Open `docs/embeddings-adoption-contract.md`.
   - Expected: The file exists under `docs/` and is clearly written as the canonical public `POST /v1/embeddings` contract.
2. Scan the section structure.
   - Expected: The doc has multiple concrete sections covering scope, request contract, auth, response behavior, evidence, failure semantics, unsupported/deferred claims, and verification.
3. Search the file for placeholder markers like `TODO` or `TBD`.
   - Expected: No placeholders remain.
4. Read the opening sections.
   - Expected: The doc explicitly says the embeddings surface is intentionally narrow and does not claim full OpenAI embeddings parity.

## Test Case 2 — Supported request shape is documented narrowly and matches S01 runtime truth
1. In `docs/embeddings-adoption-contract.md`, find the supported request contract section.
   - Expected: It documents `POST /v1/embeddings` with `model` plus `input`.
2. Verify the documented `input` forms.
   - Expected: Only these are supported:
     - one non-blank string
     - one flat list of non-blank strings
3. Check for explicit unsupported shape language.
   - Expected: Nested lists, mixed-type input collections, token-array inputs, and extra request fields are called unsupported or deferred.
4. Cross-check against `tests/test_embeddings_api.py`.
   - Expected: There is focused coverage for authenticated single-input and batch-input success plus unsupported-shape rejection before runtime.

## Test Case 3 — Auth contract is documented correctly and does not drift toward bearer auth
1. In `docs/embeddings-adoption-contract.md`, locate the authentication section.
   - Expected: The file names `X-Nebula-API-Key` as the required public auth header.
2. Check that the doc explicitly rejects or does not promise `Authorization: Bearer ...`.
   - Expected: Bearer auth is named as unsupported or unproven for embeddings adoption.
3. Cross-check against `tests/test_embeddings_api.py` auth coverage.
   - Expected: Missing or invalid `X-Nebula-API-Key` returns `401`.

## Test Case 4 — Success response and evidence surfaces are documented concretely
1. In the canonical doc, locate the success response section.
   - Expected: The doc shows an OpenAI-like `object: "list"` payload with `data[]`, `index`, and float `embedding` vectors.
2. Confirm usage semantics.
   - Expected: The doc states the currently tested `usage` shape with zeroed token counts.
3. Locate the response-header and ledger evidence section.
   - Expected: The doc names `X-Request-ID` plus the `X-Nebula-*` headers emitted on successful embeddings responses.
4. Confirm the durable operator lookup path.
   - Expected: The doc points to `GET /v1/admin/usage/ledger?request_id=<X-Request-ID>` and explains that it is metadata-only.
5. Cross-check against runtime-facing files.
   - Expected:
     - `src/nebula/api/routes/embeddings.py` sets the documented headers.
     - `tests/test_governance_api.py` proves request-id to ledger correlation.

## Test Case 5 — Failure semantics are documented and traceable to code/tests
1. In the canonical doc, find the failure-semantics section.
   - Expected: The file distinguishes request-shape validation failures from embeddings-service/provider failures.
2. Confirm documented status codes.
   - Expected:
     - `401` for missing/invalid API key
     - `422` for request-shape validation failures
     - `422` for embeddings validation error
     - `502` for upstream failure
     - `502` for empty embeddings result
3. Confirm documented route-reason vocabulary.
   - Expected: The file names `embeddings_validation_error`, `embeddings_upstream_error`, and `embeddings_empty_result`.
4. Cross-check the route implementation.
   - Expected: `src/nebula/api/routes/embeddings.py` records those exact route reasons in ledger metadata.
5. Cross-check the focused tests.
   - Expected: `tests/test_service_flows.py` and `tests/test_embeddings_api.py` exercise these branches.

## Test Case 6 — Entry docs point to the canonical contract without becoming competing contracts
1. Open `README.md`.
   - Expected: It mentions the embeddings adoption contract and points readers to `docs/embeddings-adoption-contract.md`.
2. Open `docs/architecture.md`.
   - Expected: It mentions the narrow public embeddings surface and links to the canonical doc.
3. Read the surrounding text in both files.
   - Expected: Neither file duplicates the detailed request/response/header/failure contract inline; they stay discoverability- and inventory-oriented.
4. Compare against the canonical doc.
   - Expected: `docs/embeddings-adoption-contract.md` is clearly the only detailed embeddings contract file.

## Test Case 7 — Slice verification commands pass in the assembled worktree
1. Run:
   `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
   - Expected: Passes.
2. Run:
   `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
   - Expected: Passes.
3. Run:
   `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding`
   - Expected: Passes.
4. Run:
   `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" docs/embeddings-adoption-contract.md && [ "$(rg -c "^## " docs/embeddings-adoption-contract.md)" -ge 6 ]`
   - Expected: Exits successfully.
5. Run:
   `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md`
   - Expected: Matches appear in all intended files.
6. Run:
   `rg -n "embeddings_validation_error|embeddings_upstream_error|embeddings_empty_result|X-Request-ID|/v1/admin/usage/ledger" src/nebula/api/routes/embeddings.py tests/test_embeddings_api.py tests/test_governance_api.py tests/test_service_flows.py docs/embeddings-adoption-contract.md`
   - Expected: Matches confirm runtime/doc/test alignment.

## Edge Cases to review manually
- The doc should not imply cache-hit, fallback, or multi-provider embeddings behavior beyond the current direct `ollama` path.
- The doc should not promise raw embedding inputs or vectors in ledger/admin evidence.
- The doc should not introduce migration guidance or helper ergonomics that belong to S03.
- The doc should not broaden the public auth story beyond `X-Nebula-API-Key`.

## UAT Result Criteria
Mark UAT complete only if all of the following are true:
- `docs/embeddings-adoption-contract.md` reads as the single canonical embeddings contract.
- README and architecture docs point to it without duplicating detailed semantics.
- Supported behavior, exclusions, evidence surfaces, and failure semantics all match the assembled route/tests.
- All slice verification commands pass.