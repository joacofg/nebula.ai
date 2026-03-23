# Adoption API Contract

This document is Nebula's canonical compatibility boundary for adopting the public `POST /v1/chat/completions` endpoint.

It is intentionally narrow. Every supported claim here is grounded in the contract tests in:

- `tests/test_chat_completions.py`
- `tests/test_response_headers.py`
- `tests/test_admin_playground_api.py`

If code, tests, and prose disagree, treat the tests and live behavior as authoritative and update this document.

## Scope and intent

Nebula exposes an OpenAI-like chat-completions surface for common adoption and migration work, but it does **not** claim full OpenAI API parity.

This contract covers the **public** client path only:

- endpoint: `POST /v1/chat/completions`
- auth: `X-Nebula-API-Key`
- behavior: non-streaming and streaming chat completions
- evidence: `X-Nebula-*` response headers

This document does **not** redefine admin-only APIs, console behavior, or future compatibility work that has not been proven in tests.

## Supported public request contract

Nebula currently supports the following adoption shape on `POST /v1/chat/completions`:

- a JSON request body with `model` and `messages`
- message arrays using chat roles such as `system`, `user`, and `assistant`
- at least one `user` message in every request
- optional `stream: true` for Server-Sent Events responses

Example non-streaming request:

```http
POST /v1/chat/completions
X-Nebula-API-Key: <tenant-client-key>
Content-Type: application/json

{
  "model": "nebula-auto",
  "messages": [
    {"role": "system", "content": "You are Nebula."},
    {"role": "user", "content": "Hello Nebula"}
  ]
}
```

Example streaming request:

```http
POST /v1/chat/completions
X-Nebula-API-Key: <tenant-client-key>
Content-Type: application/json

{
  "model": "nebula-auto",
  "stream": true,
  "messages": [
    {"role": "user", "content": "Hello streaming"}
  ]
}
```

Validation boundary proven today:

- requests without a `user` message fail with HTTP `422`
- the failure shape is FastAPI validation output, not a custom Nebula error envelope
- validation failures happen before routing, so route-specific `X-Nebula-*` metadata is not emitted on those request-shape failures

## Authentication and tenant boundary

The public adoption path uses Nebula-specific header auth:

- required header: `X-Nebula-API-Key`
- public auth is **not** OpenAI-style `Authorization: Bearer ...`

Behavior proven by tests:

- missing `X-Nebula-API-Key` returns HTTP `401`
- sending only `Authorization: Bearer ...` returns HTTP `401` with `{"detail": "Missing client API key."}`
- Nebula can infer the bootstrap tenant from the bootstrap API key fixture used in tests, so an explicit tenant header is not required for that bootstrap case

Adopters should treat `X-Nebula-API-Key` as the stable public auth contract for this endpoint.

## Model naming and routing guidance

Nebula accepts chat-completions requests through a narrow set of tested model-selection patterns.

Supported, tested guidance:

- `nebula-auto` lets Nebula choose among local, cache, premium, or fallback behavior according to policy and request characteristics
- explicit local models are supported when the configured local model name is provided directly
- explicit premium-model requests participate in policy checks and may be denied if the tenant policy does not allow that premium model
- OpenAI-compatible premium aliases may be understood by Nebula routing logic, but allowance still depends on tenant policy rather than alias syntax alone

What adopters should rely on:

- `nebula-auto` is the safest adoption starting point when you want Nebula-managed routing
- response headers, not naming conventions alone, are the source of truth for what route actually executed
- policy can deny explicit premium requests even when the request shape itself is valid

## Supported response behavior

For non-streaming requests, Nebula returns an OpenAI-like chat completion payload. The tested surface includes:

- top-level object type `chat.completion`
- `choices[0].message.role == "assistant"`
- a resolved response `model`
- `usage` with prompt and completion token counts

For streaming requests with `stream: true`, Nebula returns Server-Sent Events with:

- `content-type: text/event-stream`
- `cache-control: no-cache`
- `connection: keep-alive`
- chunk objects containing `chat.completion.chunk`
- a terminal `[DONE]` event

Nebula preserves the same response-header evidence on the streaming path that it does on the non-streaming path.

## Nebula response-header evidence

Nebula's public adoption contract includes inspectable `X-Nebula-*` headers on routed success and routed failure paths.

Headers proven in tests include:

- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

These headers make the gateway explainable to adopters and operators. Depending on the path, they expose evidence such as:

- whether the request ran on `local`, `cache`, or `premium`
- why Nebula chose that path
- whether a fallback from local to premium was used
- whether a cache hit occurred
- whether policy allowed or denied the routed target
- which provider actually served the request

Important boundary:

- routed failures such as policy denials and fallback-blocked outcomes still expose Nebula metadata headers
- request-validation failures do not, because routing never happened

## Failure and policy semantics

The tested public contract includes several inspectable failure paths:

- HTTP `401` for missing or wrong public auth shape
- HTTP `403` for policy-denied explicit model requests
- HTTP `502` when the local provider fails and tenant policy disables premium fallback
- HTTP `422` for invalid request shape such as a missing `user` message

Adopters should rely on both the HTTP status code and the `X-Nebula-*` headers when present.

That distinction matters operationally:

- `403` and `502` routed failures retain route and policy evidence
- `422` request-shape failures expose structured validation detail instead of routing metadata

## Admin Playground is not the public adoption path

Nebula's admin Playground is intentionally a different boundary from the public adoption API.

The Playground endpoint is:

- `POST /v1/admin/playground/completions`
- admin-only, using admin credentials rather than `X-Nebula-API-Key`
- intentionally non-streaming in the tested milestone boundary

Behavior proven by tests:

- public client auth does not work on the admin Playground endpoint
- `stream: true` is rejected on the Playground with HTTP `400`
- Playground responses include `X-Request-ID`
- that request id can be correlated with persisted records through `GET /v1/admin/usage/ledger`

Do not treat Playground behavior as proof of public client compatibility. It is an operator tool, not the adoption surface for application traffic.

## Unsupported or deferred compatibility claims

The following items are intentionally unsupported, deferred, or simply unproven by the current contract tests. They should not be promised to adopters as part of Nebula's stable chat-completions boundary yet:

- full OpenAI API parity beyond the tested `POST /v1/chat/completions` path
- OpenAI-style `Authorization: Bearer ...` authentication for public traffic
- treating admin Playground behavior as equivalent to the public API
- streaming support on `/v1/admin/playground/completions`
- claims about broad compatibility for untested request fields, tools, function calling, multimodal inputs, response formats, or parallel tool execution
- claims that all OpenAI model aliases are accepted or policy-allowed
- claims about unsupported endpoints outside this document

If a feature is not named here and backed by the referenced tests, treat it as outside the current adoption contract.

## How to verify this contract locally

Use the contract-focused checks that back this document:

```bash
pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q
pytest tests/test_chat_completions.py -k "stream or user or auth" -q
pytest tests/test_response_headers.py -k "denied or fallback_blocked or validation_failures" -q
```

For repository-level doc alignment, also verify that the contract file exists, has at least six `##` sections, contains no unfinished placeholder markers, and is referenced from `README.md` plus `docs/architecture.md`.
