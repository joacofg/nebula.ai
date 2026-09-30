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

Nebula also exposes a narrow public embeddings surface at `POST /v1/embeddings`. It follows the same auth, routing, and evidence seams as the chat-completions path.

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

Qdrant stores the semantic-cache vectors used to short-circuit repeat traffic when cache eligibility and similarity thresholds are satisfied. Every point carries the owning `tenant_id`, the source `model` and a `created_at` timestamp in its payload. A lookup filters on the authenticated tenant and on `created_at` newer than the tenant policy's `semantic_cache_max_entry_age_hours`, and uses the policy's `semantic_cache_similarity_threshold` as the Qdrant score threshold, so a cached answer is never served across tenants and both knobs in the console are enforced on every request. The hit's similarity score is persisted in the ledger's `route_signals` as `cache_similarity_score`.

### Providers

Nebula supports two main execution paths:

- local inference through Ollama for lower-cost traffic
- premium execution through an OpenAI-compatible provider for higher-value or fallback traffic

Fallback behavior is intentionally visible. If local execution is unavailable and fallback is allowed, Nebula routes to premium and marks that outcome in response metadata and downstream records.

### Learned three-tier router

With `NEBULA_LEARNED_ROUTER_ENABLED=true`, a `nebula-auto` request is routed by two logistic models over the nomic embedding of the latest user message: one estimates whether the local model's answer would serve the reader as well as the frontier model's, the other whether the economy model's would. A cascade over two thresholds picks `local`, `economy` (`NEBULA_ECONOMY_MODEL`) or `frontier` (`NEBULA_PREMIUM_MODEL`). The thresholds are an operating point measured out of fold during training (`src/nebula/data/learned_router_v1.json`, built by `python -m scripts.router.train`); each tenant chooses one through its policy's `routing_quality_target`, and the router takes the cheapest point that meets it. The prompt is embedded once and the vector is shared with the semantic cache. If embedding fails, routing falls back to the token/keyword heuristic and says so in `route_signals.learned_router`. The ledger target stays `premium` for both premium tiers; the tier is in `route_signals.tier` and in the `X-Nebula-Route-Tier` header. Explicit models, `local_only`/`premium_only` and `calibrated_routing_enabled=false` bypass the learned router.

### Per-tenant rate limit

A tenant policy may set `rate_limit_requests_per_minute`. The public chat and embeddings endpoints check it right after authentication and before routing, with an in-memory token bucket per tenant (burst = the limit, refill = limit/60 per second), so a rejected request costs neither an embedding nor a model call. Over the limit the gateway answers `429` with `Retry-After`, `X-Nebula-Route-Target: denied` and `X-Nebula-Route-Reason: rate_limited`, records a `rate_limited` ledger row and increments `nebula_rate_limited_total`; limited responses (streaming included) carry `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset`. The buckets live in the gateway process: the supported self-hosted stack runs a single uvicorn process, and running several would multiply the effective limit.

### Operator console

The Next.js console is a separate service that proxies same-origin browser traffic to `/v1/admin/*`. It is the operator entrypoint for:

- admin login with `NEBULA_ADMIN_API_KEY`
- tenant and API-key management
- policy inspection and edits
- Playground requests
- usage-ledger inspection
- runtime health and Observability views

The Playground is intentionally distinct from the public `POST /v1/chat/completions` adoption contract. It is an admin-only inspection surface, not the public client integration path, and the tested milestone boundary keeps it non-streaming.

For the supported first-request flow, see [quickstart.md](quickstart.md).

## Benchmark harness

Nebula includes a repo-native benchmark harness in `src/nebula/benchmarking/run.py`. It runs versioned scenario datasets and writes:

- `report.json`
- `report.md`

under `artifacts/benchmarks/<timestamp>/` (disposable) — runs cited by the docs are copied to
`benchmarks/results/`.

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
- Embeddings requests surface the same public headers and usage-ledger evidence, correlated through `GET /v1/admin/usage/ledger?request_id=...`

That split matters: the immediate response proves what just happened, while the usage ledger proves what the system persisted and can explain later.

## Self-hosted deployment shape

The supported deployment path is `docker compose -f docker-compose.selfhosted.yml up -d`.

That topology runs:

- the gateway on port `8000`
- the console on port `3000`
- PostgreSQL
- Qdrant

See [self-hosting.md](self-hosting.md) for the canonical runbook and [quickstart.md](quickstart.md) for the supported adoption flow.
