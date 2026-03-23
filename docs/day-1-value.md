# Day-1 value proof

This document is Nebula's canonical walkthrough for proving day-1 value after a successful adoption request.

It starts from the same public-path truth established in [`docs/quickstart.md`](quickstart.md) and [`docs/reference-migration.md`](reference-migration.md): a real `POST /v1/chat/completions` request, inspectable `X-Nebula-*` headers, and a correlation handle through `X-Request-ID`. It then shows how operators corroborate that outcome through Playground, the persisted usage ledger, and Observability without changing the public adoption boundary.

Use this guide only after the public request is already working. Keep these documents in their canonical roles:

- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — the only canonical public compatibility boundary
- [`docs/quickstart.md`](quickstart.md) — supported self-hosted setup and first-request flow
- [`docs/reference-migration.md`](reference-migration.md) — canonical before/after migration proof for existing callers
- [`docs/production-model.md`](production-model.md) — operator, tenant, API-key, and surface boundaries

## What day-1 value means in Nebula

Nebula's day-1 value is not just that a request returns text. It is that the first successful request is immediately explainable.

A team should be able to answer these questions from one coherent proof path:

- which tenant handled the request
- which route target Nebula chose
- the route reason behind that choice
- which provider actually served the response
- whether cache or fallback behavior was involved
- what policy mode and policy outcome applied
- how to find the same request in persisted operator evidence
- whether optional dependencies were healthy or degraded at the time operators inspected the system

The public request remains the adoption target. Operator surfaces exist to corroborate and persist that same story.

## Canonical proof sequence

Follow this sequence in order. Do not substitute the admin Playground for the public request.

### 1. Start with one real public `POST /v1/chat/completions` request

Use the supported public path from [`docs/quickstart.md`](quickstart.md) or the migration path from [`docs/reference-migration.md`](reference-migration.md).

The proof starts only after a real public request succeeds with:

- HTTP `200`
- an OpenAI-like `chat.completion` response body
- public `X-Nebula-*` headers

That keeps the day-1 story grounded in the actual application boundary rather than an operator-only shortcut.

### 2. Read the public response headers as immediate evidence

Nebula's first explainability surface is the public response itself.

Record these headers from the successful response:

- `X-Request-ID`
- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

These fields establish the immediate story of the request:

- **tenant** — where governance and attribution landed
- **route target + route reason** — why Nebula chose `local`, `cache`, or `premium`
- **provider** — which backend actually served the answer
- **cache/fallback state** — whether cost-saving or resilience behaviors were exercised
- **policy mode/outcome** — whether the request ran under the expected tenant policy
- **request id** — how operators correlate the same outcome later

If this public evidence is missing or inconsistent, the day-1 proof is already incomplete even if the body returned text.

### 3. Use Playground as admin-only immediate corroboration

Playground is useful after the public request works because it gives operators a second immediate inspection surface.

Playground helps corroborate day-1 value by showing the same family of runtime metadata on an operator-issued request, including the route target, route reason, provider, fallback state, policy framing, and `X-Request-ID`.

Keep the boundary explicit:

- Playground uses the admin trust model, not `X-Nebula-API-Key`
- Playground is admin-only and intentionally different from the public adoption path
- Playground is corroboration, not migration proof and not the app integration target

Use Playground when an operator wants to compare what Nebula reports immediately on a controlled request after the public call has already established adoption success.

### 4. Correlate the request in the persisted usage ledger

The next step is persistence.

Use the `X-Request-ID` from the public response or Playground response to find the same request in the usage ledger:

```bash
curl "http://localhost:8000/v1/admin/usage/ledger?request_id=<x-request-id>" \
  -H "X-Nebula-Admin-Key: <admin-api-key>"
```

The ledger is the persisted operator evidence that the runtime outcome was recorded, not just observed transiently in headers. The day-1 proof should line up across at least these fields:

- `request_id`
- `tenant_id`
- `final_route_target`
- `route_reason`
- `final_provider`
- `cache_hit`
- `fallback_used`
- `policy_outcome`
- `terminal_status`
- token and timing fields

This is where `X-Request-ID` becomes operationally valuable: it ties the immediate public response to a durable operator record.

### 5. Use Observability as the persisted explanation surface

Observability is where operators validate that the request outcome sits inside a healthy, inspectable runtime.

For day-1 proof, Observability should answer two categories of questions:

#### Request explanation

Operators should be able to inspect the persisted request outcome and confirm that route, provider, fallback, and policy evidence remain visible after the original response is gone.

#### Dependency-health context

Operators should also be able to see whether supporting dependencies are healthy, degraded, or unavailable when they inspect the system.

That matters because day-1 trust is not only about one successful response. It is also about whether optional dependency degradation remains visible instead of being hidden behind a vague "something failed" experience.

In other words:

- headers provide **immediate request evidence**
- Playground provides **admin-side immediate corroboration**
- the usage ledger provides **persisted request evidence**
- Observability provides **persisted explanation plus dependency-health context**

## How the proof surfaces fit together

Use this table when explaining Nebula's day-1 value to a team.

| Surface | Boundary | What it proves | What it must not replace |
|---|---|---|---|
| Public `POST /v1/chat/completions` response | Public application path | The app integration works and emits `X-Nebula-*` plus `X-Request-ID` | Admin-only corroboration |
| Playground | Admin-only operator path | Immediate operator-side metadata inspection on a controlled request | Public adoption or migration proof |
| Usage ledger | Admin persisted data | The request outcome was recorded with tenant, route, provider, fallback, and policy evidence | Live dependency-health inspection |
| Observability | Admin persisted explanation surface | Request explanation and dependency-health context remain visible for operators | The public request contract |

## Minimal day-1 walkthrough

Use this concise sequence when you want one canonical proof path:

1. Send one real public `POST /v1/chat/completions` request.
2. Confirm the body is a successful `chat.completion` response.
3. Record `X-Request-ID` and inspect the `X-Nebula-*` headers, especially route target, route reason, provider, fallback state, and policy outcome.
4. Optionally run a Playground request to compare the same metadata family from the operator side.
5. Query or open the usage ledger and confirm the persisted row matches the request evidence.
6. Open Observability and confirm the request remains explainable there alongside current dependency-health state.

That is the canonical Nebula day-1 value proof.

## What not to treat as day-1 proof

Do not collapse these boundaries:

- Playground alone is not proof of public adoption.
- A successful text response without `X-Nebula-*` header inspection is not enough.
- A ledger row without public-path correlation through `X-Request-ID` is incomplete.
- Observability without request-level correlation does not prove the first request story.
- Docs that restate setup or contract details from scratch are not a better proof path than the existing quickstart and migration guides.

## When this proof is considered complete

The day-1 proof is complete when one team can point to one successful public request and say, with evidence:

- this is the tenant that handled it
- this is the route target and route reason
- this is the provider that served it
- this is whether fallback or cache behavior occurred
- this is the policy outcome
- this is the persisted ledger record for the same request
- this is the current dependency-health context operators see while validating it

That is the explicit proof surface Nebula needs immediately after adoption.

## Related docs

- [`docs/quickstart.md`](quickstart.md) — start here for the supported self-hosted setup and first request
- [`docs/reference-migration.md`](reference-migration.md) — use this when replacing an existing OpenAI-style caller
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public contract for `POST /v1/chat/completions`
- [`docs/production-model.md`](production-model.md) — canonical runtime and operator boundary reference
