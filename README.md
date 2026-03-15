# Nebula

Semantic AI Gateway for optimizing cost, latency, and resilience across LLM workflows.

## Core Stack

- Python 3.12+
- FastAPI
- Pydantic v2
- Qdrant
- Ollama
- Prometheus

## Structure

```text
.
├── docker-compose.yml
├── pyproject.toml
├── src/
│   └── nebula/
│       ├── api/
│       │   └── routes/
│       ├── core/
│       ├── models/
│       ├── observability/
│       ├── providers/
│       └── services/
└── tests/
```

## Local Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
docker compose up -d qdrant
uvicorn nebula.main:app --reload
```

Install Ollama and pull the recommended models:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

To enable a real premium provider, update `.env` with:

```bash
NEBULA_PREMIUM_PROVIDER=openai_compatible
NEBULA_PREMIUM_BASE_URL=https://openrouter.ai/api/v1
NEBULA_PREMIUM_API_KEY=your_openrouter_api_key
NEBULA_PREMIUM_MODEL=openai/gpt-4o-mini
```

The application now fails fast at startup if `openai_compatible` is selected without the required premium credentials.
Premium and fallback requests are billed against the OpenRouter credits attached to the configured API key.

Nebula now boots with a lightweight SQLite governance store and a bootstrap tenant/API key for local development:

```bash
X-Nebula-API-Key: <NEBULA_BOOTSTRAP_API_KEY>
X-Nebula-Tenant-ID: <NEBULA_BOOTSTRAP_TENANT_ID>
X-Nebula-Admin-Key: <NEBULA_ADMIN_API_KEY>
```

By default those resolve to local-only dev values from `.env.example`. Override them in `.env` before using Nebula outside local development.

## Smoke Tests

After configuring `.env`, run:

```bash
make smoke-openrouter
```

This starts Nebula locally, verifies `/health`, forces a premium non-streaming request, and verifies premium streaming.

To verify local-to-premium fallback with one command, run:

```bash
make smoke-fallback
```

This starts Nebula with an intentionally invalid local Ollama URL so `nebula-auto` falls back to the premium provider.

## Benchmarking

Run the full benchmark suite with:

```bash
make benchmark
```

This starts managed local Nebula instances for the normal and fallback scenario groups, runs the versioned dataset in `benchmarks/v1/scenarios.jsonl`, and writes `report.json` plus `report.md` under `artifacts/benchmarks/<timestamp>/`.
Benchmark cost fields are estimated from `benchmarks/pricing.json`; they are not invoice reconciliation.

If you want to target an already-running Nebula instance, pass `BASE_URL`:

```bash
BASE_URL=http://127.0.0.1:8000 .venv/bin/python -m nebula.benchmarking.run
```

When `BASE_URL` is provided, fallback-only scenarios are skipped because the runner cannot safely mutate the external server configuration.

## Self-Hosted Deployment

Nebula's supported Phase 1 deployment path is the premium-first Docker Compose stack in
[`docs/self-hosting.md`](docs/self-hosting.md). Follow that runbook instead of treating the local
development steps above as a second deployment flow.

## Endpoints

`POST /v1/chat/completions`

Implements the base OpenAI-compatible contract for both streaming and non-streaming requests.
Requires `X-Nebula-API-Key`; `X-Nebula-Tenant-ID` resolves the tenant explicitly when needed.
Responses now include tenant/policy headers alongside route, provider, cache, and fallback metadata.

`GET /v1/admin/tenants`

`POST /v1/admin/tenants`

`GET|PUT /v1/admin/tenants/{tenant_id}/policy`

`GET|POST /v1/admin/api-keys`

`POST /v1/admin/api-keys/{api_key_id}/revoke`

`GET /v1/admin/usage/ledger`

Operator APIs are protected with `X-Nebula-Admin-Key` and expose tenant, API key, policy, and usage-ledger management without returning downstream provider secrets.

`GET /health`

Returns the application liveness status.

`GET /health/ready`

Returns readiness for the gateway and governance store, while allowing optional dependencies such as Qdrant or local Ollama to show as `degraded`.

`GET /health/dependencies`

Returns component-level dependency detail for gateway, governance store, semantic cache, and local Ollama.

`GET /metrics`

Exposes Prometheus metrics when metrics are enabled.

Key metrics include HTTP request counts and latency, semantic cache outcomes, routing decisions, provider execution latency, completion totals, and fallback totals.

## Recommended MVP Configuration

- `llama3.2:3b` as the primary local completion model
- `nomic-embed-text` for embeddings
- `mock` as the default premium provider to avoid external spend during local development
- `openai_compatible` when connecting a real premium provider such as OpenAI or OpenRouter
