# Nebula Architecture

Nebula is a self-hosted gateway that routes LLM traffic across local, cached, fallback, and premium paths while keeping policy decisions and operator evidence visible.

## Request flow

1. A client sends `POST /v1/chat/completions` with `X-Nebula-API-Key`.
2. The FastAPI gateway resolves tenant policy and runtime settings.
3. Nebula decides whether the request should use:
   - a local model
   - a semantic cache hit
   - a premium provider
   - a premium fallback after local-provider trouble
4. The response returns route metadata in the `X-Nebula-*` header contract.
5. Usage and outcome details are persisted so operators can inspect them later in the usage ledger and console.

Nebula also exposes a narrow public embeddings surface at `POST /v1/embeddings`. The canonical request/response, evidence, and exclusion contract for that path lives in [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md); this architecture guide intentionally does not restate those details. For the minimal-change caller walkthrough that proves how an OpenAI-style embeddings integration moves onto that path, see [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md). For the joined final proof order from public request to `X-Request-ID`/`X-Nebula-*` headers to usage-ledger correlation and Observability corroboration, see [`docs/embeddings-integrated-adoption-proof.md`](embeddings-integrated-adoption-proof.md).

## Runtime components

### Gateway

The backend runs as a FastAPI application and owns:

- request routing
- provider selection
- cache lookup behavior
- fallback handling
- health and dependency reporting
- admin and tenant management APIs

### Governance store

PostgreSQL is the canonical governance store for the supported self-hosted topology. It persists tenants, API keys, policy state, and usage-ledger records.

### Semantic cache

Qdrant stores the semantic-cache vectors used to short-circuit repeat traffic when cache eligibility and similarity thresholds are satisfied.

### Providers

Nebula supports two main execution paths:

- local inference through Ollama for lower-cost traffic
- premium execution through an OpenAI-compatible provider for higher-value or fallback traffic

Fallback behavior is intentionally visible. If local execution is unavailable and fallback is allowed, Nebula routes to premium and marks that outcome in response metadata and downstream records.

### Operator console

The Next.js console is a separate service that proxies same-origin browser traffic to `/v1/admin/*`. It is the operator entrypoint for:

- admin login with `NEBULA_ADMIN_API_KEY`
- tenant and API-key management
- policy inspection and edits
- Playground requests
- usage-ledger inspection
- runtime health and Observability views

The Playground is intentionally distinct from the public `POST /v1/chat/completions` adoption contract. It is an admin-only inspection surface, not the public client integration path, and the tested milestone boundary keeps it non-streaming.

For the canonical operator/application split and the current tenant-versus-app/workload model, see [production-model.md](production-model.md). For the supported first-request flow, see [quickstart.md](quickstart.md).

## Benchmark harness

Nebula includes a repo-native benchmark harness in `src/nebula/benchmarking/run.py`. It runs versioned scenario datasets and writes:

- `report.json`
- `report.md`

under `artifacts/benchmarks/<timestamp>/`.

The benchmark harness is intentionally black-box:

- it calls the public gateway API
- it reads response headers and payload usage
- it estimates premium cost with `benchmarks/pricing.json`
- it records expectation mismatches when observed behavior diverges from scenario expectations

## Benchmark story layers

Phase 5 packages the benchmark around six comparison groups:

- premium control
- local control
- auto-routing cold
- auto-routing warm cache
- fallback resilience
- supporting premium-routed evidence

This keeps the human-facing product proof focused while preserving the underlying raw scenario rows.

## Observability and product proof

Nebula's operator-facing proof depends on two views working together:

- Playground shows immediate route, provider, fallback, and latency metadata for a live request
- Observability shows dependency health and recorded usage-ledger evidence after the fact
- Embeddings adopters should use the canonical [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md) when they need the exact `POST /v1/embeddings` evidence surface, supported behavior, and explicit exclusions
- The pointer-only joined walkthrough in [`docs/embeddings-integrated-adoption-proof.md`](embeddings-integrated-adoption-proof.md) is the discoverability layer for following one embeddings request through public headers, `GET /v1/admin/usage/ledger?request_id=...`, and Observability corroboration without redefining the contract

That split matters: the immediate response proves what just happened, while the usage ledger proves what the system persisted and can explain later.

## Hybrid trust boundary

Nebula is self-hosted with an optional hosted control plane. This section defines the trust boundary between the self-hosted gateway and the hosted plane.

**Core invariants:**

- Nebula's hosted control plane is not in the request-serving path.
- Local runtime enforcement remains authoritative.
- Default hosted export is metadata-only.
- Hosted freshness states are connected, degraded, stale, and offline.

**Excluded by default:** raw prompts, raw responses, provider credentials, raw usage-ledger rows, tenant secrets, authoritative runtime policy state. These categories never leave the self-hosted environment under the default export contract.

Richer diagnostics are operator-initiated exceptions to the default contract. Any future expansion of the default export must update the canonical schema artifact first.

This section is derived from [`docs/hosted-default-export.schema.json`](hosted-default-export.schema.json). Future edits to trust-boundary language must update the contract artifact first and then propagate here.

## Self-hosted deployment shape

The supported deployment path is `docker compose -f docker-compose.selfhosted.yml up -d`.

That topology runs:

- the gateway on port `8000`
- the console on port `3000`
- PostgreSQL
- Qdrant

See [self-hosting.md](self-hosting.md) for the canonical runbook, [quickstart.md](quickstart.md) for the supported adoption flow, and [adoption-api-contract.md](adoption-api-contract.md) for the public `POST /v1/chat/completions` compatibility boundary.
