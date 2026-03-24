# Nebula

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility.

## Why Nebula exists

Application teams often need premium models for some requests, but not all of them. Nebula sits in front of those requests and makes the tradeoff explicit:

- route simple or repeat traffic toward lower-cost local or cached paths
- preserve premium capacity for requests that actually need it
- surface route, cache, fallback, and cost signals to operators instead of hiding them

Nebula is self-hosted with an optional hosted control plane. The hosted control plane is recommended for pilots because it improves onboarding and fleet visibility, but it is not required for serving traffic. The default hosted export is metadata-only; see [`docs/hosted-default-export.schema.json`](docs/hosted-default-export.schema.json) for the canonical machine-readable contract.

## Product proof

Nebula's core claim is simple: it can reduce estimated premium spend on repeatable traffic patterns while staying explainable when requests route to premium, hit cache, or fall back after local-provider trouble.

Use these repo-native proof paths:

- `make benchmark` runs the canonical benchmark suite and writes `report.json` plus `report.md` under `artifacts/benchmarks/<timestamp>/`
- `make benchmark-demo` runs the smaller live-demo subset through the same benchmark runner
- the operator console shows request routing, fallback metadata, and recorded ledger outcomes
- the Observability page shows dependency health and degraded optional services without pretending the whole gateway is down

## Who it is for

- startup and scale-up engineering teams evaluating a self-hosted gateway
- operators who need a focused control plane and visible runtime behavior
- academic or technical reviewers who need the architecture, deployment, and evaluation story to be inspectable from the repository

## Hosted control plane

Nebula can optionally connect to a hosted control plane for fleet visibility, deployment health, and streamlined pilot onboarding. The hosted plane is not in the request-serving path and is not authoritative for local runtime enforcement. Local policy decisions, routing, and governance remain under operator control at all times.

The default metadata exported to the hosted plane is defined in [`docs/hosted-default-export.schema.json`](docs/hosted-default-export.schema.json). That contract explicitly excludes raw prompts, raw responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state. Richer diagnostics beyond the default export are operator-initiated exceptions, not automatic behavior.

## Documentation map

- [Self-hosting](docs/self-hosting.md): the only supported deployment path for pilot onboarding
- [Architecture](docs/architecture.md): request flow, runtime components, trust boundary, governance, cache, providers, console, and benchmark harness
- [Embeddings adoption contract](docs/embeddings-adoption-contract.md): the canonical public `POST /v1/embeddings` boundary, supported evidence surface, and explicit exclusions
- [Embeddings reference migration](docs/embeddings-reference-migration.md): the minimal-change before/after guide derived from `tests/test_embeddings_reference_migration.py`
- [Evaluation](docs/evaluation.md): benchmark commands, artifact interpretation, and estimated-cost framing
- [Demo script](docs/demo-script.md): benchmark-led walkthrough tied to Playground and Observability

## Quick start

### Supported self-hosted path

Nebula's supported deployment path is the Compose stack documented in [docs/self-hosting.md](docs/self-hosting.md).

```bash
cp deploy/selfhosted.env.example deploy/selfhosted.env
docker compose -f docker-compose.selfhosted.yml up -d
```

That path runs:

- the FastAPI gateway on `http://localhost:8000`
- the operator console on `http://localhost:3000`
- PostgreSQL as the canonical governance store
- Qdrant as the semantic-cache backing service

Use the self-hosting runbook instead of treating local development as a second deployment story.

### Local development

Local development remains useful for implementation work, but it is not the supported pilot deployment path.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
docker compose up -d qdrant
uvicorn nebula.main:app --reload
```

Optional local-model setup:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

## Benchmark commands

Run the full repeatable proof package:

```bash
make benchmark
```

Run the smaller live-demo subset:

```bash
make benchmark-demo
```

Run against an already-running Nebula instance:

```bash
BASE_URL=http://127.0.0.1:8000 .venv/bin/python -m nebula.benchmarking.run
```

When `BASE_URL` is set, fallback-only scenarios are skipped because the runner cannot safely reconfigure an external server.

## Operator surfaces

- `Playground` proves immediate route target, provider, cache-hit, fallback, and latency metadata for a live request
- `Recorded outcome` ties that request back to persisted usage-ledger data
- `Observability` shows runtime dependency health, degraded optional services, and filtered ledger history

## Admin and bootstrap access

The gateway and console use explicit bootstrap/admin credentials. In self-hosted mode, set real values for:

- `NEBULA_ADMIN_API_KEY`
- `NEBULA_BOOTSTRAP_API_KEY`
- `NEBULA_BOOTSTRAP_TENANT_ID`
- `NEBULA_DATABASE_URL`

The supported self-hosted environment template lives at `deploy/selfhosted.env.example`.

## Selected endpoints

- `POST /v1/chat/completions`
- `POST /v1/embeddings` — see `docs/embeddings-adoption-contract.md` for the canonical supported boundary and exclusions
- `GET /v1/admin/session`
- `GET|PUT /v1/admin/tenants/{tenant_id}/policy`
- `GET /v1/admin/usage/ledger`
- `GET /health`
- `GET /health/ready`
- `GET /health/dependencies`
- `GET /metrics`
