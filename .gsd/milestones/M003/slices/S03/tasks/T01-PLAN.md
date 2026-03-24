---
estimated_steps: 4
estimated_files: 6
skills_used:
  - test
---

# T01: Add executable embeddings migration proof coverage

**Slice:** S03 — Realistic migration proof
**Milestone:** M003

## Description

Create the executable proof that anchors the embeddings migration story. This task should mirror the proven structure of `tests/test_reference_migration.py`, but keep the scope strictly on the public embeddings route: a realistic OpenAI-style embeddings request goes through `POST /v1/embeddings`, returns the expected OpenAI-like embeddings payload, exposes `X-Request-ID` plus the embeddings `X-Nebula-*` headers, and correlates to a metadata-only usage-ledger row. The test is the source of truth for the later migration guide, so it must lock the minimal-change path without implying unsupported options or extra helper layers.

## Steps

1. Read `tests/test_reference_migration.py`, `tests/test_governance_api.py`, `tests/test_embeddings_api.py`, and `docs/embeddings-adoption-contract.md` to copy the established migration-proof shape and stay inside the current embeddings boundary.
2. Add `tests/test_embeddings_reference_migration.py` with a deterministic embeddings-service stub using `configured_app()` so the proof stays fast and isolated while still exercising the real public `/v1/embeddings` route and ledger persistence path.
3. In the new test, send a realistic migrated request using `X-Nebula-API-Key` auth and a supported embeddings body, capture `X-Request-ID`, query `GET /v1/admin/usage/ledger?request_id=...`, and assert the response body shape, exact embeddings route headers, and aligned ledger metadata including the redaction boundary.
4. Keep the proof intentionally narrow: no bearer-auth path, no `encoding_format`, no Playground/UI corroboration, and no broad model-portability claims beyond the tested request.

## Must-Haves

- [ ] `tests/test_embeddings_reference_migration.py` proves the happy-path public embeddings migration with response-body, header, and ledger correlation assertions.
- [ ] The test asserts metadata-only evidence by confirming the ledger row matches public evidence fields and does not expose raw `input` values or embedding vectors.

## Verification

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`

## Observability Impact

- Signals added/changed: this task adds a locked executable proof for the public embeddings evidence surface — `X-Request-ID`, `X-Nebula-*` response headers, and ledger metadata keyed by request id.
- How a future agent inspects this: run `tests/test_embeddings_reference_migration.py` and inspect `GET /v1/admin/usage/ledger?request_id=...` behavior through the test assertions when a future change breaks migration proof semantics.
- Failure state exposed: mismatches between public headers/body and persisted ledger metadata become explicit test failures, including accidental redaction-boundary regressions.

## Inputs

- `tests/test_reference_migration.py` — proven migration-proof structure to mirror for embeddings without importing chat-only operator steps.
- `tests/test_governance_api.py` — existing embeddings request-id to ledger-correlation assertions to reuse for expected ledger fields and redaction boundaries.
- `tests/test_embeddings_api.py` — current public embeddings response/header truth to align with the route contract.
- `tests/support.py` — standard `configured_app()`, auth helpers, and test harness utilities for isolated runtime setup.
- `docs/embeddings-adoption-contract.md` — canonical narrow embeddings boundary that the proof must not exceed.
- `src/nebula/api/routes/embeddings.py` — exact success headers and route reason/provider semantics to assert.

## Expected Output

- `tests/test_embeddings_reference_migration.py` — executable embeddings migration proof grounded in the public route and durable ledger correlation.
