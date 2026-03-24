---
estimated_steps: 5
estimated_files: 7
skills_used:
  - test
---

# T02: Wire the authenticated public endpoint and ledger correlation

**Slice:** S01 — Public embeddings endpoint
**Milestone:** M003

## Description

Turn the embeddings foundation into a real adoption path. This task adds a dedicated authenticated `POST /v1/embeddings` route, wires it into the app, and proves the same request can be correlated through `X-Request-ID` into the existing usage ledger. The route must reuse the existing tenant/auth boundary and middleware, stay independent from chat orchestration, and expose only the narrow happy-path contract needed for embeddings adoption.

## Steps

1. Add `src/nebula/api/routes/embeddings.py` with a dedicated FastAPI route for `POST /v1/embeddings` that depends on `get_tenant_context`, reads `request.state.request_id`, calls the embeddings service directly, and returns the narrow OpenAI-style embeddings response shape.
2. Add any required dependency access in `src/nebula/api/dependencies.py` and register the router in `src/nebula/main.py` under the existing `/v1` prefix without changing the auth model or introducing chat-service coupling.
3. Persist correlatable embeddings usage through the existing governance ledger path in `src/nebula/services/governance_store.py` and `src/nebula/models/governance.py`, keeping the record metadata-only (request id, tenant, model, provider/route, status) and not storing raw inputs or vectors.
4. Create `tests/test_embeddings_api.py` with real API assertions for authenticated single-input and batch-input requests, auth failures on the existing public contract, and narrow validation failures for unsupported shapes/options.
5. Extend `tests/test_governance_api.py` with an embeddings-specific correlation test that proves `X-Request-ID` from `/v1/embeddings` can be used with `/v1/admin/usage/ledger?request_id=...` to inspect the durable backend record.

## Must-Haves

- [ ] `src/nebula/api/routes/embeddings.py` exposes a real authenticated `/v1/embeddings` route under the existing API prefix.
- [ ] Embeddings requests can be correlated through `X-Request-ID` into `usage_ledger` metadata without storing raw prompts or embedding vectors.
- [ ] `tests/test_embeddings_api.py` and `tests/test_governance_api.py` provide executable proof for the happy path, validation boundary, auth reuse, and ledger correlation.

## Verification

- `pytest tests/test_embeddings_api.py`
- `pytest tests/test_governance_api.py -k embeddings`

## Observability Impact

- Signals added/changed: embeddings requests now emit `X-Request-ID` and create usage-ledger records that capture route/provider/status metadata for later operator proof.
- How a future agent inspects this: run `pytest tests/test_governance_api.py -k embeddings` or query `/v1/admin/usage/ledger?request_id=...` after an embeddings call.
- Failure state exposed: auth failures stay on the shared auth path, while request-correlation and ledger status make embeddings runtime outcomes inspectable without new helper tooling.

## Inputs

- `src/nebula/api/dependencies.py` — existing dependency entrypoints for tenant/auth resolution.
- `src/nebula/main.py` — current router registration point for public API surfaces.
- `src/nebula/models/governance.py` — current usage ledger record shape used by the admin API.
- `src/nebula/services/governance_store.py` — persistence path for durable request evidence.
- `tests/support.py` — existing configured app and auth header helpers for public API tests.
- `tests/test_governance_api.py` — current admin ledger proof surface to extend with embeddings correlation.
- `src/nebula/models/openai.py` — embeddings schemas produced by T01.
- `src/nebula/services/embeddings_service.py` — embeddings runtime behavior produced by T01.

## Expected Output

- `src/nebula/api/routes/embeddings.py` — public embeddings route implementation.
- `src/nebula/api/dependencies.py` — dependency accessor updates for the embeddings route.
- `src/nebula/main.py` — router registration for the new embeddings entrypoint.
- `src/nebula/models/governance.py` — any usage ledger model updates needed for embeddings evidence.
- `src/nebula/services/governance_store.py` — persistence logic used by embeddings request correlation.
- `tests/test_embeddings_api.py` — focused public embeddings API tests.
- `tests/test_governance_api.py` — embeddings request/ledger correlation assertions.
