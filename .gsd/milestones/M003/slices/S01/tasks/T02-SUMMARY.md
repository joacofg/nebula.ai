---
id: T02
parent: S01
milestone: M003
provides:
  - A real authenticated `/v1/embeddings` API route with request-ID-linked usage-ledger evidence and narrow-contract API coverage.
key_files:
  - src/nebula/api/routes/embeddings.py
  - src/nebula/api/dependencies.py
  - src/nebula/main.py
  - src/nebula/models/openai.py
  - tests/test_embeddings_api.py
  - tests/test_governance_api.py
  - .gsd/milestones/M003/slices/S01/S01-PLAN.md
key_decisions:
  - Reused the existing generic usage ledger with embeddings-specific route/provider/status metadata instead of widening the ledger schema or coupling embeddings into chat orchestration.
patterns_established:
  - New public routes should depend on request-scoped accessors or `request.app.state.container`, not `Depends(get_container)`, because FastAPI will otherwise misinterpret helper parameters as request inputs.
observability_surfaces:
  - `X-Request-ID` on `/v1/embeddings`; `/v1/admin/usage/ledger?request_id=...`; `pytest tests/test_embeddings_api.py`; `pytest tests/test_governance_api.py -k embeddings`
duration: 2h
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T02: Wire the authenticated public endpoint and ledger correlation

**Added a real authenticated `/v1/embeddings` endpoint that records metadata-only usage rows correlated by `X-Request-ID`.**

## What Happened

I first applied the required pre-flight observability fix by extending the slice verification section in `.gsd/milestones/M003/slices/S01/S01-PLAN.md` with an explicit embeddings failure-path command.

Then I added `src/nebula/api/routes/embeddings.py` as a dedicated public route under `/v1/embeddings`. The handler reuses the existing tenant/auth dependency, reads `request.state.request_id`, calls the embeddings service directly rather than going through chat orchestration, maps explicit embeddings service failures into narrow HTTP errors, and records a usage-ledger row for both successful and terminal failure outcomes.

In `src/nebula/api/dependencies.py` I added a typed `get_embeddings_service()` accessor, and in `src/nebula/main.py` I registered the new router under the existing API prefix.

I kept the ledger path metadata-only by reusing the existing `UsageLedgerRecord` shape in `src/nebula/models/governance.py` and `src/nebula/services/governance_store.py` rather than introducing a separate embeddings table or storing raw inputs/vectors. Embeddings rows now use route/provider/status fields like `final_route_target="embeddings"`, `final_provider="ollama"`, and route reasons such as `embeddings_direct` or explicit failure reasons.

I also tightened the public contract in `src/nebula/models/openai.py` by forbidding extra request fields on `EmbeddingsRequest`, so unsupported OpenAI options are rejected instead of being silently ignored.

Finally, I created `tests/test_embeddings_api.py` for authenticated happy-path, auth reuse, unsupported-shape rejection, and upstream-failure mapping, and I extended `tests/test_governance_api.py` with an embeddings-specific correlation test that proves the emitted `X-Request-ID` can be used to inspect the durable usage-ledger row without exposing request text or vectors.

## Verification

I ran the new embeddings API suite, the embeddings-specific governance ledger proof, and both slice-level embeddings service checks from T01 to ensure the new route did not regress the underlying service contract.

All four commands passed. The route now returns an OpenAI-style embeddings payload for single and batch inputs, rejects unsupported fields/shapes at the contract boundary, reuses the existing auth path, and produces an admin-queryable usage-ledger row keyed by the same `X-Request-ID` returned to the caller.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py -q` | 0 | ✅ pass | ~0.9s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 0 | ✅ pass | ~0.7s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding` | 0 | ✅ pass | ~0.7s |
| 4 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k 'embedding and (blank or upstream or empty)'` | 0 | ✅ pass | ~0.6s |

## Diagnostics

Future agents can inspect a real embeddings request via:

- `pytest tests/test_embeddings_api.py`
- `pytest tests/test_governance_api.py -k embeddings`
- `/v1/admin/usage/ledger?request_id=<value-from-X-Request-ID>`

The persisted row exposes metadata-only evidence: request id, tenant id, requested model, final route target, provider, terminal status, route reason, and policy outcome. It does not store raw embedding inputs or returned vectors.

For runtime failure inspection, the route distinguishes narrow contract failures from upstream failures via HTTP status/detail and persisted terminal metadata such as `route_reason="embeddings_upstream_error"` or `route_reason="embeddings_empty_result"`.

## Deviations

I did not need to widen `src/nebula/models/governance.py` or `src/nebula/services/governance_store.py` beyond reusing the existing generic usage-ledger fields, because the current schema already supports the embeddings metadata required by the plan.

## Known Issues

Verification still depends on the repo-root virtualenv interpreter path because the worktree shell does not expose `python`/`pytest` directly on PATH.

## Files Created/Modified

- `src/nebula/api/routes/embeddings.py` — added the authenticated public embeddings route, failure mapping, response headers, and metadata-only ledger recording.
- `src/nebula/api/dependencies.py` — added a request-scoped embeddings service accessor for the new route.
- `src/nebula/main.py` — registered the embeddings router under the existing `/v1` API prefix.
- `src/nebula/models/openai.py` — forbade extra fields on `EmbeddingsRequest` to preserve the narrow public contract.
- `tests/test_embeddings_api.py` — added focused public API tests for success, auth reuse, unsupported options, and upstream failure mapping.
- `tests/test_governance_api.py` — added request-ID-to-ledger correlation coverage for embeddings requests.
- `.gsd/milestones/M003/slices/S01/S01-PLAN.md` — added the missing slice-level failure-path verification command required by pre-flight observability checks.
