# Self-Hosting Nebula

This document is the canonical deployment runbook for Nebula pilot onboarding. There is one supported self-hosted path: `docker-compose.selfhosted.yml` plus `deploy/selfhosted.env.example`.

Use [`quickstart.md`](quickstart.md) for the first successful public request after deployment, and [`production-model.md`](production-model.md) for the tenant, API-key, operator, app, and workload boundaries behind that flow.

Local development is useful for coding, but it is not a second supported production-ish topology.

## Supported topology

`docker-compose.selfhosted.yml` starts:

- `console` on port `3000`
- `nebula` on port `8000`
- `postgres` as the canonical governance store
- `qdrant` for semantic-cache vectors

The `nebula` service runs:

```bash
alembic upgrade head && uvicorn nebula.main:app --host 0.0.0.0 --port 8000
```

## Prerequisites

- Docker with Compose support
- a real premium-provider API key
- long random values for:
  - `NEBULA_ADMIN_API_KEY`
  - `NEBULA_BOOTSTRAP_API_KEY`

## Configure the environment

Copy the supported environment template:

```bash
cp deploy/selfhosted.env.example deploy/selfhosted.env
```

Review `deploy/selfhosted.env` and set these values before startup:

- `NEBULA_DATABASE_URL`
- `NEBULA_PREMIUM_API_KEY`
- `NEBULA_ADMIN_API_KEY`
- `NEBULA_BOOTSTRAP_API_KEY`
- `NEBULA_BOOTSTRAP_TENANT_ID`

The supported self-hosted profile is already encoded in the template:

- `NEBULA_RUNTIME_PROFILE=premium_first`
- `NEBULA_PREMIUM_PROVIDER=openai_compatible`
- `NEBULA_DEFAULT_MODEL=nebula-auto`
- `NEBULA_QDRANT_URL=http://qdrant:6333`

`NEBULA_ADMIN_API_KEY` is required for the operator console login flow.

For the supported first request and credential split, continue with [`quickstart.md`](quickstart.md). For when `X-Nebula-Tenant-ID` is required and how tenant-scoped keys differ from bootstrap access, see [`production-model.md`](production-model.md).

## Start the supported stack

```bash
docker compose -f docker-compose.selfhosted.yml up -d
```

Stop it with:

```bash
docker compose -f docker-compose.selfhosted.yml down
```

Inspect logs with:

```bash
docker compose -f docker-compose.selfhosted.yml logs -f nebula
```

## Verify the deployment

Check liveness:

```bash
curl http://localhost:8000/health
```

Check readiness and dependency detail:

```bash
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/dependencies
```

Open the console:

```bash
open http://localhost:3000
```

Paste `NEBULA_ADMIN_API_KEY` into the login screen. The console keeps the key in memory and proxies browser traffic to `/v1/admin/*`.

## What the deployment is optimized for

This topology is designed for product proof and pilot evaluation:

- premium-first routing with explicit fallbacks
- operator-visible governance and policy controls
- semantic caching through Qdrant
- benchmark and demo flows that use the same runtime shape as the deployed gateway

## Important deployment notes

- `docs/self-hosting.md` is the only supported deployment guide in this repo.
- PostgreSQL is the canonical governance store for self-hosted runtime.
- Local Ollama is optional. It is an optimization path, not a deployment prerequisite.
- A `degraded` dependency state can still be acceptable when optional services such as Qdrant or local Ollama are unavailable.
- Estimated premium cost in benchmark artifacts is based on `benchmarks/pricing.json`, not provider invoice reconciliation.

## Outbound-only hosted linking

Nebula can optionally link a self-hosted deployment to a hosted control plane. Any such linking is outbound-only: the self-hosted gateway initiates connections to the hosted plane, not the other way around. Hosted linking is optional for self-hosted deployments and does not affect the gateway's ability to serve traffic.

The data sent during hosted linking is limited by the same metadata-only default export contract defined in [`docs/hosted-default-export.schema.json`](hosted-default-export.schema.json). That contract explicitly excludes raw prompts, raw responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state.

Richer diagnostics beyond the default export are operator-initiated exceptions, not automatic behavior. See [architecture.md](architecture.md) for the full trust-boundary narrative.

## Hosted pilot workflow

- Operators create a deployment slot in the hosted plane, generate a short-lived enrollment token, and pass that token to the self-hosted gateway for one outbound exchange.
- After enrollment, steady-state hosted communication uses a deployment-scoped credential instead of the enrollment token.
- If the hosted plane is unreachable, Nebula keeps serving traffic locally; hosted inventory simply becomes stale or offline until heartbeat visibility returns.
- The only hosted remote-management action in v2.0 is rotate_deployment_credential, and it fails closed when local policy or deployment state does not allow it.
- The hosted plane is metadata-and-intent only; local runtime policy and request serving remain authoritative inside the self-hosted gateway.
- The default hosted export contract is defined in docs/hosted-default-export.schema.json.

## Related docs

- [README](../README.md)
- [Quickstart](quickstart.md)
- [Production model](production-model.md)
- [Adoption API contract](adoption-api-contract.md)
- [Architecture](architecture.md)
- [Evaluation](evaluation.md)
- [Demo script](demo-script.md)
