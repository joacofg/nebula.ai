# Self-Hosting Nebula

This document is the canonical deployment runbook for Nebula pilot onboarding. There is one supported self-hosted path: `docker-compose.selfhosted.yml` plus `deploy/selfhosted.env.example`.

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

## Related docs

- [README](../README.md)
- [Architecture](architecture.md)
- [Evaluation](evaluation.md)
- [Demo script](demo-script.md)
