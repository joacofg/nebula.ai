# Quickstart

This document is Nebula's canonical happy-path quickstart for the supported self-hosted deployment.

It shows how to configure real credentials, start the Compose stack, sign into the console as an operator, send a first public `POST /v1/chat/completions` request, and confirm success through the product's existing evidence surfaces. If you are migrating an existing caller after the first request works, continue with [`docs/reference-migration.md`](reference-migration.md). For the exact public API boundary, see [`docs/adoption-api-contract.md`](adoption-api-contract.md). For the runtime entity model behind the steps below, see [`docs/production-model.md`](production-model.md).

## Before you start

Use this quickstart only with the supported deployment path in [`docs/self-hosting.md`](self-hosting.md):

- `docker-compose.selfhosted.yml`
- `deploy/selfhosted.env.example`

Have these ready:

- Docker with Compose support
- a real premium-provider API key
- one long random value for `NEBULA_ADMIN_API_KEY`
- one different long random value for `NEBULA_BOOTSTRAP_API_KEY`

Do not reuse the admin key as an application credential.

## Configure the self-hosted environment

Copy the supported environment template:

```bash
cp deploy/selfhosted.env.example deploy/selfhosted.env
```

Open `deploy/selfhosted.env` and set at least these values:

- `NEBULA_DATABASE_URL`
- `NEBULA_PREMIUM_API_KEY`
- `NEBULA_ADMIN_API_KEY`
- `NEBULA_BOOTSTRAP_API_KEY`
- `NEBULA_BOOTSTRAP_TENANT_ID`

The template already encodes the supported self-hosted runtime shape:

- `NEBULA_RUNTIME_PROFILE=premium_first`
- `NEBULA_PREMIUM_PROVIDER=openai_compatible`
- `NEBULA_DEFAULT_MODEL=nebula-auto`
- `NEBULA_QDRANT_URL=http://qdrant:6333`

Outside local mode, Nebula refuses to start if the admin key or bootstrap key are left at their default development values.

## Start the supported stack

Bring the stack up:

```bash
docker compose -f docker-compose.selfhosted.yml up -d
```

Useful checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/dependencies
```

Open the console at `http://localhost:3000` after the services are ready.

If you need logs while starting up:

```bash
docker compose -f docker-compose.selfhosted.yml logs -f nebula
```

## Sign into the operator console

The console is an operator surface backed by the admin API.

Use the value of `NEBULA_ADMIN_API_KEY` to sign in at `http://localhost:3000`.

Important boundaries:

- the login flow represents `X-Nebula-Admin-Key`, not `X-Nebula-API-Key`
- the console keeps the admin key in memory only, so a browser refresh ends the session
- browser requests stay same-origin while the console proxies to `/v1/admin/*`
- successful sign-in lands you on the tenant management flow

Use the console for tenant, policy, API-key, Playground, and usage inspection work. Do not hand the admin key to application callers.

## Decide whether to use the bootstrap key or create a tenant-scoped key

Nebula starts with a bootstrap tenant and bootstrap API key so you can reach a first successful public request without extra setup.

Use the bootstrap key when:

- you want the fastest first request on a fresh deployment
- you are validating that the stack is alive end to end
- you are working inside the bootstrap tenant on purpose

Create a tenant-scoped key when:

- you want a clearer separation between bootstrap access and real application traffic
- you are onboarding a specific tenant through the console
- you want the key's `tenant_id` and `allowed_tenant_ids` to reflect the intended usage explicitly

From the console, create keys through the API-key flow backed by `/v1/admin/api-keys`. The UI issues keys with explicit `allowed_tenant_ids`, which is the runtime field Nebula checks during public auth.

## Know which header goes on which path

Nebula uses different credentials for different boundaries.

### Public application traffic

For `POST /v1/chat/completions`, send:

- `X-Nebula-API-Key`
- `Content-Type: application/json`
- optionally `X-Nebula-Tenant-ID` when the API key can access multiple tenants

### Operator and admin traffic

For `/v1/admin/*` and the console trust model, use:

- `X-Nebula-Admin-Key`

### When X-Nebula-Tenant-ID is required

You must send `X-Nebula-Tenant-ID` on the public path when the API key is authorized for more than one tenant and Nebula cannot infer the tenant automatically.

You do **not** need to send it when:

- the key has a single bound `tenant_id`, or
- the key has exactly one allowed tenant

If a multi-tenant key omits `X-Nebula-Tenant-ID`, Nebula rejects the request with `403` because the tenant is ambiguous.

For the supported public request and response semantics, do not copy examples from the admin API. Use [`docs/adoption-api-contract.md`](adoption-api-contract.md) as the canonical contract.

## Send the first public chat-completions request

This is the happy-path public request using the bootstrap client key or a tenant-scoped client key.

```bash
curl -i http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Nebula-API-Key: <client-api-key>" \
  -d '{
    "model": "nebula-auto",
    "messages": [
      {"role": "system", "content": "You are Nebula."},
      {"role": "user", "content": "Reply with a short health check confirmation."}
    ]
  }'
```

If you intentionally use a multi-tenant API key, add:

```bash
-H "X-Nebula-Tenant-ID: <tenant-id>"
```

Expected success indicators:

- HTTP `200`
- an OpenAI-like `chat.completion` JSON response body
- `X-Nebula-*` response headers describing the resolved tenant, route target, provider, cache/fallback behavior, and policy outcome

## Confirm the request through operator-visible evidence

A successful first request should be inspectable in more than one place.

### 1. Inspect public response headers

From the `curl -i` output, confirm headers such as:

- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

Those headers are the public-path evidence for what Nebula actually did.

### 2. Use Playground for operator-side confirmation

Open the console Playground and run a non-streaming request against the same tenant.

Playground is useful because it:

- exercises the admin-only `/v1/admin/playground/completions` path
- returns `X-Request-ID`
- mirrors the same `X-Nebula-*` metadata headers on the operator request

Remember that Playground is not the public adoption boundary. It is an operator inspection tool that helps you compare runtime behavior.

### 3. Check the usage ledger

Inspect the persisted request record through the console or directly through:

```bash
curl http://localhost:8000/v1/admin/usage/ledger \
  -H "X-Nebula-Admin-Key: <admin-api-key>"
```

Use the usage ledger to confirm:

- tenant attribution
- route target and terminal status
- request timing and timestamps
- correlation with Playground request IDs when you used Playground

### 4. Review Observability

Use the console Observability views to inspect the request after the public call succeeds.

For this quickstart, Observability is the place to verify that the request shows up in the same operator-facing surfaces your team will use later for troubleshooting and governance review.

If you want the single canonical walkthrough that ties the supported quickstart, the public route, `X-Nebula-*` / `X-Request-ID`, usage-ledger correlation, Playground corroboration, and Observability corroboration into one final path, continue with [`docs/integrated-adoption-proof.md`](integrated-adoption-proof.md). If you want the same proof focused specifically on operator-visible day-1 value after adoption succeeds, continue with [`docs/day-1-value.md`](day-1-value.md).

## What to do next

Once the first request works:

1. If you are replacing an existing OpenAI-style integration, use [`docs/reference-migration.md`](reference-migration.md) for the canonical before/after migration proof.
2. Create tenant-specific API keys instead of sharing the bootstrap key broadly.
3. Review tenant policy defaults and allowed premium models in the console.
4. Use [`docs/production-model.md`](production-model.md) to align your team on operator versus application boundaries.
5. Keep [`docs/adoption-api-contract.md`](adoption-api-contract.md) as the source of truth for public request/response behavior.

## Related docs

- [`docs/production-model.md`](production-model.md) — operating-model reference for tenant, API key, operator, app, and workload boundaries
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public API contract
- [`docs/reference-migration.md`](reference-migration.md) — canonical before/after migration proof grounded in `tests/test_reference_migration.py`
- [`docs/self-hosting.md`](self-hosting.md) — supported Compose deployment runbook
- [`docs/architecture.md`](architecture.md) — request flow, runtime components, trust boundary, and operator surfaces
