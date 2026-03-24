---
estimated_steps: 3
estimated_files: 7
skills_used:
  - best-practices
---

# T01: Author the canonical embeddings contract document

**Slice:** S02 — Canonical embeddings contract docs
**Milestone:** M003

## Description

Create the one canonical public embeddings contract document for Nebula. This task should translate the S01 runtime truth into a narrow, test-backed doc that explains what `POST /v1/embeddings` supports today, what evidence the route emits, how failures behave, and which OpenAI-like embeddings features are intentionally out of scope. The doc must stand alone as the single detailed embeddings boundary so later docs can link to it instead of re-explaining it.

## Steps

1. Read `docs/adoption-api-contract.md` for structure and tone, then derive the embeddings content only from `src/nebula/api/routes/embeddings.py`, `src/nebula/models/openai.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`, and `tests/test_service_flows.py`.
2. Write `docs/embeddings-adoption-contract.md` with clear sections for scope/intent, supported request contract, authentication, supported response behavior, response-header and ledger evidence, failure semantics, explicit unsupported or deferred claims, and local verification commands.
3. Keep every claim narrow and test-backed: describe only string or flat-list inputs, the current float-vector response and zeroed usage fields, `X-Nebula-*` / `X-Request-ID` evidence, and the metadata-only ledger correlation path without implying broader OpenAI parity or extra request-option support.

## Must-Haves

- [ ] `docs/embeddings-adoption-contract.md` is the only detailed embeddings contract file and names the supported `POST /v1/embeddings` boundary from runtime truth.
- [ ] The doc explicitly documents supported request shape, auth, response shape, headers/evidence, failure semantics, and unsupported/deferred edges.

## Verification

- `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" docs/embeddings-adoption-contract.md && [ "$(rg -c "^## " docs/embeddings-adoption-contract.md)" -ge 6 ]`
- `rg -n "X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|unsupported|deferred" docs/embeddings-adoption-contract.md`

## Inputs

- `docs/adoption-api-contract.md` — canonical structure and narrow-boundary composition pattern to mirror without copying chat-specific content.
- `src/nebula/api/routes/embeddings.py` — runtime truth for headers, route reason, provider labeling, and usage-ledger recording semantics.
- `src/nebula/models/openai.py` — request/response schema truth for embeddings input validation and response payload shape.
- `tests/test_embeddings_api.py` — public embeddings contract proof for auth, success shape, unsupported input rejection, and upstream failure mapping.
- `tests/test_governance_api.py` — request-ID to usage-ledger correlation proof and metadata-only evidence boundary.
- `tests/test_service_flows.py` — lower-level validation, batch ordering, blank-input rejection, upstream failure, and empty-result invariants.

## Expected Output

- `docs/embeddings-adoption-contract.md` — canonical embeddings adoption contract doc grounded in the S01 runtime and test-backed boundary.
