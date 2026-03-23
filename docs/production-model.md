# Production model

This document is Nebula's canonical operating-model reference for the current self-hosted product boundary.

Use it to understand which entities exist in the runtime today, which credentials belong to operators versus applications, and where `app` / `workload` labels are guidance only. For the public request and response contract, see [`docs/adoption-api-contract.md`](adoption-api-contract.md). For the supported deployment runbook, see [`docs/self-hosting.md`](self-hosting.md).

## What is a real runtime entity today

Nebula's current self-hosted runtime has a small set of authoritative entities:

- **Tenant** — the primary governance boundary for requests, policy, and usage attribution.
- **Tenant policy** — the routing and cost-control configuration enforced for a tenant at request time.
- **API key** — the client credential used on the public `POST /v1/chat/completions` path.
- **Operator admin session** — the admin-key-backed console and `/v1/admin/*` surfaces used to manage tenants, policies, API keys, Playground requests, and usage inspection.

These boundaries are grounded in the current implementation:

- public client auth resolves a tenant context through `AuthService.resolve_tenant_context()`
- admin access is protected by `AuthService.authenticate_admin()`
- `/v1/admin/*` exposes tenant, policy, API-key, Playground, and usage-ledger surfaces
- production settings require explicit non-default admin and bootstrap keys outside local mode

## Tenant is the authoritative governance boundary

A tenant is the unit Nebula uses to make runtime decisions.

In M001, tenant identity drives:

- policy lookup
- request authorization
- usage-ledger attribution
- admin filtering for keys and usage records
- Playground execution context

That means Nebula is not routing by arbitrary application names or business-unit labels at runtime. It is routing and recording against tenants plus tenant policy.

The public response headers also report tenant context back to the caller through `X-Nebula-Tenant-ID` when a request reaches routing. Treat that header as evidence of the resolved runtime boundary, not just a documentation label.

## API keys are client credentials, not operator credentials

Nebula intentionally separates application traffic from operator traffic.

For the public chat-completions path:

- clients send `X-Nebula-API-Key`
- the key is looked up in the governance store
- the key must be authorized for the resolved tenant
- the request then runs under that tenant's policy

For operator and console actions:

- operators send `X-Nebula-Admin-Key`
- the console login experience is a wrapper around that same trust model
- browser traffic stays same-origin, then the console proxies requests to `/v1/admin/*`
- the console keeps the admin key in memory only, so refresh clears the session by design

Do not reuse `X-Nebula-Admin-Key` for application traffic. The admin key is for operators and admin APIs only.

## When X-Nebula-Tenant-ID is required

`X-Nebula-Tenant-ID` is only required when Nebula cannot unambiguously infer the tenant from the API key alone.

The runtime rules are:

- if an API key is bound to a single `tenant_id`, Nebula uses that tenant automatically
- if an API key has exactly one `allowed_tenant_ids` entry, Nebula can also infer the tenant automatically
- if an API key is authorized for multiple tenants and the caller omits `X-Nebula-Tenant-ID`, Nebula rejects the request with `403` and `Tenant header is required for this API key.`
- if the caller supplies `X-Nebula-Tenant-ID`, it must be one of the key's allowed tenants

This is why multi-tenant keys are an operator choice with an extra calling requirement, not the default happy path.

## Bootstrap key versus tenant-scoped keys

Nebula ships with a bootstrap tenant and bootstrap API key so a self-hosted operator can bring the system up and reach a working first request without creating extra records first.

That bootstrap material is configured through settings such as:

- `NEBULA_BOOTSTRAP_TENANT_ID`
- `NEBULA_BOOTSTRAP_TENANT_NAME`
- `NEBULA_BOOTSTRAP_API_KEY_NAME`
- `NEBULA_BOOTSTRAP_API_KEY`

In a production-like self-hosted deployment, operators should treat the bootstrap key as a starting credential, not the full long-term key-management story. The admin surfaces exist so operators can:

- create tenants
- issue tenant-scoped keys
- revoke keys
- inspect which tenant a key is intended to reach

The console's API-key dialog already reflects this model by creating keys with explicit `allowed_tenant_ids` and a selected `tenant_id`.

## Operator responsibilities and surfaces

The operator is the human or automation boundary that configures and inspects Nebula.

In the current product boundary, operators are responsible for:

- setting non-default secrets in the self-hosted environment
- keeping `NEBULA_ADMIN_API_KEY` and `NEBULA_BOOTSTRAP_API_KEY` distinct
- creating and maintaining tenants and tenant policy
- issuing or revoking client API keys
- validating request behavior through Playground, usage ledger, and Observability

The operator surfaces that exist today are:

- console login with the admin key
- `/v1/admin/session`
- `/v1/admin/tenants`
- `/v1/admin/tenants/{tenant_id}/policy`
- `/v1/admin/api-keys`
- `/v1/admin/playground/completions`
- `/v1/admin/usage/ledger`

Playground is an operator tool. It is not the public adoption boundary and it is intentionally different from the public API: it is admin-only, uses the admin trust model, and currently supports non-streaming requests only.

## App and workload are guidance, not first-class runtime entities

Teams often need to talk about which app is calling Nebula and which workload a request belongs to. That language is useful, but in M001 it remains conceptual guidance rather than an authoritative runtime object.

Today Nebula does **not** expose first-class admin resources such as:

- `/v1/admin/apps`
- `/v1/admin/workloads`
- runtime policy objects keyed directly by app or workload
- public auth headers that require an app identifier

So when you document or operate Nebula today:

- treat **tenant** as the enforceable boundary
- treat **API key** as the public client credential
- treat **app** and **workload** as naming, grouping, or documentation conventions your team applies around tenants and keys

A practical pattern is to encode app or workload intent in tenant naming, API-key naming, or external runbooks without claiming that Nebula itself enforces app/workload entities as separate runtime objects.

## Production configuration boundaries

Nebula's settings enforce a stricter boundary outside local mode.

When `NEBULA_ENV` is not `local`:

- `NEBULA_RUNTIME_PROFILE` must be `premium_first`
- `NEBULA_ADMIN_API_KEY` must not remain the default development value
- `NEBULA_BOOTSTRAP_API_KEY` must not remain the default development value
- `NEBULA_PREMIUM_PROVIDER=mock` is not allowed
- `NEBULA_DATABASE_URL` must be set

When `NEBULA_PREMIUM_PROVIDER=openai_compatible`:

- `NEBULA_PREMIUM_BASE_URL` is required
- `NEBULA_PREMIUM_API_KEY` is required
- `NEBULA_PREMIUM_MODEL` is required

Those checks are the reason the self-hosted runbook insists on editing the environment template before startup.

## How to apply this model in practice

Use this mental model when adopting Nebula:

1. Deploy the supported self-hosted stack from [`docs/self-hosting.md`](self-hosting.md).
2. Log into the console with `X-Nebula-Admin-Key` semantics, not a client key.
3. Use the bootstrap tenant and bootstrap API key only for initial access or controlled demos.
4. Create tenant-scoped API keys for real application traffic whenever possible.
5. Require callers to send `X-Nebula-Tenant-ID` only when a key is intentionally authorized for multiple tenants.
6. Verify behavior through the public `X-Nebula-*` headers, Playground request IDs, usage ledger, and Observability views.

## Related docs

- [`docs/quickstart.md`](quickstart.md) — supported happy path from env setup to first public request
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public request/response contract
- [`docs/self-hosting.md`](self-hosting.md) — canonical deployment runbook
- [`docs/architecture.md`](architecture.md) — request flow, runtime components, trust boundary, and benchmark context
