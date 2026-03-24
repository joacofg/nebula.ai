# Embeddings Adoption Contract

This document is Nebula's canonical compatibility boundary for adopting the public `POST /v1/embeddings` endpoint.

It is intentionally narrow. Every supported claim here is grounded in the current runtime implementation and the contract tests in:

- `tests/test_embeddings_api.py`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`

If code, tests, and prose disagree, treat the tests and live behavior as authoritative and update this document.

## Scope and intent

Nebula exposes an OpenAI-like embeddings surface for the currently shipped public adoption path, but it does **not** claim full OpenAI embeddings API parity.

This contract covers the **public** client path only:

- endpoint: `POST /v1/embeddings`
- auth: `X-Nebula-API-Key`
- behavior: direct embeddings generation through the configured embeddings service
- evidence: `X-Request-ID`, `X-Nebula-*` response headers, and metadata-only usage-ledger correlation

This document does **not** redefine admin-only APIs, broader model-selection semantics from chat completions, or future compatibility work that has not been proven in tests.

## Supported public request contract

Nebula currently supports the following request shape on `POST /v1/embeddings`:

- a JSON request body with `model` and `input`
- `model` as a non-blank string
- `input` as either:
  - one non-blank string, or
  - a flat list of non-blank strings

Example single-input request:

```http
POST /v1/embeddings
X-Nebula-API-Key: <tenant-client-key>
Content-Type: application/json

{
  "model": "nomic-embed-text",
  "input": "hello world"
}
```

Example batch request:

```http
POST /v1/embeddings
X-Nebula-API-Key: <tenant-client-key>
Content-Type: application/json

{
  "model": "nomic-embed-text",
  "input": ["first", "second"]
}
```

Validation boundary proven today:

- blank `model` values fail validation
- blank string `input` values fail validation
- empty `input` lists fail validation
- nested lists are rejected; the supported batch shape is a flat list of strings only
- extra request fields are rejected because the request schema forbids unknown fields

The contract tests specifically prove rejection of unsupported shapes such as nested input arrays and extra options like `encoding_format`.

## Authentication and tenant boundary

The public embeddings path reuses Nebula's existing client authentication contract:

- required header: `X-Nebula-API-Key`
- public auth is **not** documented as OpenAI-style `Authorization: Bearer ...`

Behavior proven by tests:

- missing `X-Nebula-API-Key` returns HTTP `401`
- invalid client API keys return HTTP `401`
- the embeddings route uses the resolved tenant context from the same client-auth path as other public Nebula APIs

Adopters should treat `X-Nebula-API-Key` as the stable public auth contract for this endpoint.

## Supported response behavior

On success, Nebula returns an OpenAI-like embeddings payload with the currently tested shape:

- top-level object type `list`
- `data` as an ordered list of embedding items
- each item contains:
  - `object: "embedding"`
  - `index`
  - `embedding` as a list of floats
- `model` set to the response model returned by the embeddings service
- `usage` with:
  - `prompt_tokens: 0`
  - `total_tokens: 0`

Example success body:

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.1, 0.2]
    }
  ],
  "model": "nomic-embed-text",
  "usage": {
    "prompt_tokens": 0,
    "total_tokens": 0
  }
}
```

Additional behavior proven by lower-level tests:

- batch response ordering is preserved from the upstream embeddings result
- the route passes through the requested model to the embeddings service
- the public contract today is a float-vector response only

## Response-header and ledger evidence

Nebula's public embeddings contract includes immediate response evidence plus durable operator-side correlation.

Success responses include these inspectable headers:

- `X-Request-ID`
- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target: embeddings`
- `X-Nebula-Route-Reason: embeddings_direct`
- `X-Nebula-Provider: ollama`
- `X-Nebula-Cache-Hit: false`
- `X-Nebula-Fallback-Used: false`
- `X-Nebula-Policy-Mode: embeddings_direct`
- `X-Nebula-Policy-Outcome: embeddings=completed`

These headers are the immediate runtime evidence that the request resolved through Nebula's dedicated embeddings path.

For durable correlation, use the `X-Request-ID` from the public response to inspect the persisted metadata record through:

- `GET /v1/admin/usage/ledger?request_id=<X-Request-ID>`

Behavior proven by tests:

- a successful embeddings request creates a usage-ledger row with the matching request id
- the ledger row includes metadata such as tenant id, requested model, final route target, final provider, terminal status, route reason, and policy outcome
- the ledger correlation path is metadata-only; the tested boundary does **not** expose raw `input` values or returned `embedding` vectors in the ledger response

## Failure semantics

The current contract proves several distinct failure classes.

Request-shape failures return HTTP `422` before the embeddings service runs:

- nested input lists are rejected
- extra unsupported request fields are rejected
- blank or empty values rejected by the request model produce validation failures

Provider/runtime failures are mapped explicitly by the route:

- HTTP `422` when the embeddings service raises a validation error
- HTTP `502` when the upstream embeddings request fails
- HTTP `502` when the upstream service returns no embeddings

The route records these failure categories in ledger metadata using inspectable reasons such as:

- `embeddings_validation_error`
- `embeddings_upstream_error`
- `embeddings_empty_result`

Authentication failures remain part of the public contract as well:

- HTTP `401` for missing client API key
- HTTP `401` for invalid client API key

Operationally, adopters should read the HTTP status code first, then use `X-Request-ID` and the admin usage ledger when they need durable correlation for routed embeddings outcomes.

## Unsupported or deferred claims

The following items are intentionally unsupported, deferred, or simply unproven by the current runtime and tests. They should not be promised as part of Nebula's stable embeddings boundary yet:

- full OpenAI embeddings API parity beyond the tested `POST /v1/embeddings` path
- OpenAI-style `Authorization: Bearer ...` authentication for public embeddings traffic
- nested input arrays, token-array inputs, or mixed-type input collections
- extra request options not present in the current request schema, including `encoding_format`
- alternate embedding encodings such as base64
- any response usage accounting beyond the current zeroed `prompt_tokens` and `total_tokens` fields
- cache-hit, fallback, or multi-provider embeddings routing behavior beyond the documented direct `ollama` path
- any promise that ledger or admin APIs expose raw embedding inputs or embedding vectors

If a feature is not named here and backed by the referenced tests, treat it as outside the current adoption contract.

## Local verification commands

Use the focused checks that back this document:

```bash
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding
python - <<'PY'
from pathlib import Path
text = Path("docs/embeddings-adoption-contract.md").read_text()
assert text.count("\n## ") >= 6
PY
rg -n "X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|unsupported|deferred" docs/embeddings-adoption-contract.md
```

For repository-level discoverability, the slice also verifies that `README.md` and `docs/architecture.md` point readers to this canonical file rather than restating the detailed embeddings contract inline.
