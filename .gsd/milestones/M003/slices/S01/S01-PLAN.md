# S01: Public embeddings endpoint

**Goal:** Expose a real authenticated `POST /v1/embeddings` entrypoint that accepts Nebula’s narrow OpenAI-style happy-path contract and returns usable float embeddings without widening the public surface beyond D015.
**Demo:** An authenticated client sends `POST /v1/embeddings` with `input` as a string or flat list of strings plus `model`, receives an OpenAI-style embeddings payload, and the same request can be correlated via `X-Request-ID` into the existing usage ledger.

## Must-Haves

- Public FastAPI routing exists for authenticated `POST /v1/embeddings` under the existing `/v1` prefix and reuses the current tenant/auth boundary.
- The public contract stays intentionally narrow: `input` + `model`, string input and simple batch input only, standard float embeddings response shape, and explicit failures for unsupported or invalid shapes.
- The runtime path actually honors caller-supplied `model` and batch input through the existing embeddings capability instead of silently falling back to a single configured model.
- Embeddings requests emit durable correlation proof through existing request/ledger surfaces so later slices can build docs and migration evidence on runtime truth.
- Slice execution must preserve milestone guardrails by avoiding chat-service coupling, broad embeddings-option parity, new auth modes, SDK work, or unrelated infrastructure changes.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `pytest tests/test_embeddings_api.py`
- `pytest tests/test_governance_api.py -k embeddings`
- `pytest tests/test_service_flows.py -k embedding`

## Observability / Diagnostics

- Runtime signals: `X-Request-ID` on the public response plus `usage_ledger` rows keyed by `request_id` with embeddings route/provider/status fields.
- Inspection surfaces: `tests/test_governance_api.py -k embeddings`, `/v1/admin/usage/ledger?request_id=...`, and focused service tests around `src/nebula/services/embeddings_service.py`.
- Failure visibility: invalid auth remains on the existing auth path; upstream embedding failures and narrow-contract validation failures must be distinguishable in API responses and/or persisted terminal status.
- Redaction constraints: do not persist raw embedding inputs or response vectors in the ledger; correlation should stay at request/tenant/model/status metadata only.

## Integration Closure

- Upstream surfaces consumed: `src/nebula/api/dependencies.py`, `src/nebula/services/auth_service.py`, `src/nebula/services/embeddings_service.py`, `src/nebula/services/governance_store.py`, `src/nebula/models/openai.py`, `src/nebula/observability/middleware.py`.
- New wiring introduced in this slice: `src/nebula/api/routes/embeddings.py` registered from `src/nebula/main.py`, with request/response schemas in `src/nebula/models/openai.py` and embeddings usage persistence flowing into the existing admin ledger surface.
- What remains before the milestone is truly usable end-to-end: S02 must publish the canonical contract/exclusions, S03 must prove a realistic caller migration, and S04 must assemble the operator-evidence story around this runtime path.

## Tasks

- [ ] **T01: Extend embeddings internals for the public narrow contract** `est:1.5h`
  - Why: The existing embeddings helper only supports one string and ignores the caller’s `model`, so the public route would be fake without a real service/schema foundation.
  - Files: `src/nebula/services/embeddings_service.py`, `src/nebula/models/openai.py`, `tests/test_service_flows.py`
  - Do: Add narrow OpenAI-style embeddings request/response models in `src/nebula/models/openai.py`; extend `OllamaEmbeddingsService` so it can embed a single string or ordered flat list of strings while forwarding the requested model; and add focused service-level tests that lock down model passthrough, batch ordering, and intentional failure behavior for blank/invalid upstream results without introducing broad parameter parity.
  - Verify: `pytest tests/test_service_flows.py -k embedding`
  - Done when: the codebase has stable embeddings schemas plus service behavior that can power the public route truthfully for string and simple batch input.
- [ ] **T02: Wire the authenticated public endpoint and ledger correlation** `est:2h`
  - Why: S01 is only complete when a real client can call `/v1/embeddings`, receive a usable response, and correlate the request to durable backend evidence.
  - Files: `src/nebula/api/routes/embeddings.py`, `src/nebula/api/dependencies.py`, `src/nebula/main.py`, `src/nebula/models/governance.py`, `src/nebula/services/governance_store.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`
  - Do: Add a dedicated embeddings API route that reuses `get_tenant_context` and request ID middleware, depends directly on the existing embeddings service rather than chat orchestration, returns the narrow OpenAI-style response shape, and persists correlatable usage metadata into the existing ledger; register the router and any needed dependency accessors; and add API/integration tests for authenticated happy-path requests, validation boundaries, auth failures, `X-Request-ID`, and ledger lookup by request id.
  - Verify: `pytest tests/test_embeddings_api.py && pytest tests/test_governance_api.py -k embeddings`
  - Done when: a real authenticated `/v1/embeddings` request works end-to-end in tests for single and batch input, unsupported shapes are rejected, and admin ledger queries can explain the request using the emitted `X-Request-ID`.

## Files Likely Touched

- `src/nebula/api/routes/embeddings.py`
- `src/nebula/api/dependencies.py`
- `src/nebula/main.py`
- `src/nebula/models/openai.py`
- `src/nebula/models/governance.py`
- `src/nebula/services/embeddings_service.py`
- `src/nebula/services/governance_store.py`
- `tests/test_embeddings_api.py`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
