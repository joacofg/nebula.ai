# Integrated adoption proof

This document is Nebula's canonical final integrated adoption walkthrough.

It assembles the existing adoption canonicals into one joined proof path without redefining setup, the public API contract, or the runtime operating model. Keep these documents in their canonical roles:

- [`docs/quickstart.md`](quickstart.md) — supported self-hosted setup and first public request
- [`docs/reference-migration.md`](reference-migration.md) — canonical before/after migration proof for an existing caller
- [`docs/day-1-value.md`](day-1-value.md) — canonical operator-visible value proof
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — the only canonical public compatibility boundary for `POST /v1/chat/completions`
- [`docs/production-model.md`](production-model.md) — canonical tenant, policy, API-key, operator, and app/workload framing

Use this walkthrough when you need one discoverable story that proves Nebula's documented happy path is completable as a joined system.

## What this integrated proof establishes

The integrated adoption proof is complete only when one team can start from production structuring grounded in [`docs/production-model.md`](production-model.md), issue one real public `POST /v1/chat/completions` request, and then corroborate that same request across the operator surfaces without changing the public adoption boundary.

That means the proof must stay grounded in:

1. tenant and API-key structure as the real runtime boundary
2. one real public request
3. public `X-Nebula-*` response headers plus `X-Request-ID`
4. usage-ledger correlation for the same request
5. Playground corroboration as an admin-only surface
6. Observability corroboration as the persisted explanation and dependency-health surface

If this order changes, the adoption story weakens. Playground is not the public target, and Observability is not a substitute for the public request.

## Canonical proof order

Follow this sequence in order.

### 1. Start with production structuring, not with console clicks

Before sending traffic, align on the runtime boundary described in [`docs/production-model.md`](production-model.md).

Keep this framing explicit:

- **tenant** is Nebula's enforced governance boundary for policy, authorization, and usage attribution
- **API keys** carry caller scope on the public `POST /v1/chat/completions` path
- **operator admin sessions** are separate from application credentials and exist only for `/v1/admin/*` and console work
- **app** and **workload** remain naming guidance for your team, not first-class Nebula runtime or admin objects

This matters because the integrated proof is supposed to show a truthful production-structuring path, not invent a new adoption model around conceptual labels.

Use [`docs/quickstart.md`](quickstart.md) for supported self-hosted setup after this framing is clear. Use [`docs/reference-migration.md`](reference-migration.md) if you are mapping an existing OpenAI-style caller onto Nebula's public route.

### 2. Decide whether the public caller needs `X-Nebula-Tenant-ID`

Before the first request, make the tenant-header rule explicit instead of treating it as boilerplate.

As defined in [`docs/production-model.md`](production-model.md) and exercised in [`docs/reference-migration.md`](reference-migration.md):

- if the API key resolves to one tenant unambiguously, Nebula infers the tenant automatically
- if the API key is intentionally authorized for multiple tenants, the caller must send `X-Nebula-Tenant-ID`
- if that multi-tenant caller omits the header, Nebula rejects the request because the tenant is ambiguous

So the happy path is still tenant-scoped structure first. `X-Nebula-Tenant-ID` is required only for intentionally multi-tenant keys, not for every public request.

### 3. Send the supported public request on the real adoption boundary

Begin with [`docs/quickstart.md`](quickstart.md) to configure the supported self-hosted deployment and send the first successful public `POST /v1/chat/completions` request.

If you are adopting Nebula from an existing OpenAI-style caller, use [`docs/reference-migration.md`](reference-migration.md) immediately after quickstart. That guide preserves the same public route while showing the minimal caller diff.

At this stage, keep two boundaries explicit:

- [`docs/adoption-api-contract.md`](adoption-api-contract.md) remains the only canonical public compatibility boundary
- [`docs/production-model.md`](production-model.md) remains the runtime-truth reference for tenant, policy, API key, and operator boundaries

This integrated proof does not restate those details. It depends on them.

### 4. Record the public `X-Nebula-*` and `X-Request-ID` evidence

After the real public request succeeds, inspect the response headers before moving to any admin surface.

The canonical public evidence includes:

- `X-Request-ID`
- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

This is the first proof seam because it shows, on the public route itself:

- which tenant handled the request
- which route target Nebula chose and why
- which provider actually served the response
- whether cache or fallback behavior was involved
- which policy framing applied
- which `X-Request-ID` operators can use for later correlation

If the public route does not expose this evidence, the integrated adoption proof is incomplete even if the response body is successful.

### 5. Correlate the same request in the usage ledger

Use the `X-Request-ID` from the public response to inspect the persisted operator record in `GET /v1/admin/usage/ledger`.

This is the canonical persistence check because it proves the public request is not only visible in headers but also recorded in operator evidence. The ledger confirmation should align with the public request on fields such as:

- `request_id`
- `tenant_id`
- `final_route_target`
- `final_provider`
- `route_reason`
- `policy_outcome`
- `terminal_status`
- cache, fallback, token, and timing fields

For the exact public-to-ledger migration proof language, follow [`docs/reference-migration.md`](reference-migration.md). For the broader operator-visible explanation flow, continue through [`docs/day-1-value.md`](day-1-value.md).

### 6. Use Playground only as admin-side corroboration

Once the public request and usage-ledger correlation are established, use Playground as a controlled operator-side corroboration surface.

Keep the boundary explicit:

- Playground is admin-only
- Playground uses the operator trust model, not `X-Nebula-API-Key`
- Playground is not the public adoption target
- Playground is not the migration proof target
- Playground does not create a new app or workload boundary; it corroborates the tenant- and key-structured runtime already proved on the public path

What Playground contributes to the integrated proof is immediate operator-side metadata corroboration. It can help an operator compare route target, provider, fallback state, policy framing, and `X-Request-ID` behavior on a controlled request after the public route already proved adoption.

Do not invert that order. If a team starts with Playground, they have skipped the public contract boundary that adoption actually depends on.

### 7. Use Observability as the persisted explanation surface

Finish by validating the request in Observability.

Observability closes the integrated proof because it shows that operators can still explain the request after the immediate response is gone. In this final step, operators should be able to verify:

- the persisted request remains explainable through recorded route, provider, fallback, and policy evidence
- current dependency-health state is visible alongside that request-level inspection
- the same tenant-structured runtime story remains visible without implying separate app/workload admin objects

That makes Observability the persisted explanation plus dependency-health corroboration surface.

It does not replace:

- the public request itself
- the public `X-Nebula-*` headers
- the `X-Request-ID` correlation step
- the usage-ledger persistence check

## How the canonicals fit together

Use this map when deciding which document to open next.

| Need | Canonical doc | Why it stays separate |
|---|---|---|
| Runtime-truth tenant, policy, API-key, and operator model | [`docs/production-model.md`](production-model.md) | Keeps the enforced boundary and app/workload guidance from drifting into walkthrough shorthand |
| Supported self-hosted setup and first public request | [`docs/quickstart.md`](quickstart.md) | Keeps deployment and first-request instructions in one place |
| Minimal before/after migration proof for an existing caller | [`docs/reference-migration.md`](reference-migration.md) | Keeps the adoption diff and public-to-ledger proof executable |
| Operator-visible request explanation after adoption | [`docs/day-1-value.md`](day-1-value.md) | Keeps the value proof focused on headers, ledger, Playground, and Observability |
| Public request/response boundary | [`docs/adoption-api-contract.md`](adoption-api-contract.md) | Prevents contract drift from being copied into walkthrough docs |

## Minimal integrated walkthrough

Use this concise path when you need the final integrated adoption proof in one sequence:

1. Use [`docs/production-model.md`](production-model.md) to choose tenant structure and decide whether callers should use tenant-scoped keys or intentionally multi-tenant keys.
2. Complete the supported self-hosted startup in [`docs/quickstart.md`](quickstart.md).
3. Send one real public `POST /v1/chat/completions` request.
4. Add `X-Nebula-Tenant-ID` only when the API key is intentionally authorized for multiple tenants.
5. Confirm the OpenAI-like response body and record `X-Request-ID` plus the public `X-Nebula-*` headers.
6. Query or inspect `GET /v1/admin/usage/ledger` for the same request id.
7. Optionally use [`docs/reference-migration.md`](reference-migration.md) to frame the same proof as a before/after caller migration.
8. Use Playground only as admin-side corroboration, not as the adoption target.
9. Finish in Observability to confirm the persisted explanation and dependency-health context.

That is Nebula's canonical integrated adoption proof.

## What this walkthrough intentionally does not duplicate

This document should not become a second contract or setup reference.

It intentionally does not restate:

- the full self-hosted deployment runbook from [`docs/self-hosting.md`](self-hosting.md)
- the complete public request/response boundary from [`docs/adoption-api-contract.md`](adoption-api-contract.md)
- the complete tenant, policy, API-key, and operator model from [`docs/production-model.md`](production-model.md)
- the complete migration diff already documented in [`docs/reference-migration.md`](reference-migration.md)
- the complete day-1 operator walkthrough already documented in [`docs/day-1-value.md`](day-1-value.md)

If one of those details changes, update the canonical source rather than copying it here.

## Failure modes this integrated proof makes obvious

This walkthrough is useful because it makes adoption-story drift visible.

The integrated proof has failed if any of these become true:

- production structuring is no longer the explicit first step before the public request
- tenants or API keys are no longer described as the enforced runtime boundary
- app or workload labels are described as first-class Nebula runtime or admin entities
- `X-Nebula-Tenant-ID` is described as always required instead of conditionally required for intentionally multi-tenant keys
- the public `POST /v1/chat/completions` request is no longer the first runtime proof step
- `X-Request-ID` is missing from the joined proof path
- public `X-Nebula-*` headers are no longer treated as the first explainability surface
- usage-ledger correlation is omitted or no longer lines up with the public request
- Playground is described as the public adoption target instead of admin-only corroboration
- Observability is described as replacing the public contract rather than corroborating persisted explanation and dependency health

## Related docs

- [`docs/quickstart.md`](quickstart.md) — supported self-hosted setup and first request
- [`docs/reference-migration.md`](reference-migration.md) — minimal before/after public-route migration proof
- [`docs/day-1-value.md`](day-1-value.md) — operator-visible request explanation walkthrough
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public API boundary
- [`docs/production-model.md`](production-model.md) — canonical runtime-truth operating model
