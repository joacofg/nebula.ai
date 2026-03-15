# Codebase Concerns

**Analysis Date:** 2026-03-15

## Tech Debt

**`src/nebula/services/chat_service.py`:**
- Issue: One file owns routing, cache lookup, fallback handling, SSE assembly, metrics, and usage ledger writes
- Why: The gateway behavior is centralized in a single orchestrator class
- Impact: Small changes can affect multiple request paths at once, especially parity between streaming and non-streaming flows
- Fix approach: Extract dedicated collaborators for cache/ledger recording and streaming assembly while preserving the public service contract

**`src/nebula/services/governance_store.py`:**
- Issue: Schema definition, bootstrap logic, CRUD, and reporting all live in one SQLite repository module with no migrations layer
- Why: SQLite support is intentionally lightweight and self-bootstrapping
- Impact: Schema evolution and partial refactors are risky because initialization logic and data access are tightly coupled
- Fix approach: Split schema management from query methods and introduce explicit migration/versioning support

## Known Bugs

**Policy capture flags are stored but not acted on:**
- Symptoms: `prompt_capture_enabled` and `response_capture_enabled` can be written to policy records but do not change runtime behavior
- Trigger: Update tenant policy through `PUT /v1/admin/tenants/{tenant_id}/policy`
- Workaround: None in code; treat the flags as reserved/no-op settings
- Root cause: The flags exist in `src/nebula/models/governance.py` and `src/nebula/services/governance_store.py` but are never consumed by `ChatService` or any persistence path

**Benchmark subprocess diagnostics are hard to inspect:**
- Symptoms: Managed benchmark runs can fail with only a generic health timeout
- Trigger: `make benchmark` when the spawned Uvicorn process fails during startup
- Workaround: Run the app manually with visible logs before retrying the benchmark
- Root cause: `src/nebula/benchmarking/run.py` redirects both subprocess stdout and stderr to `DEVNULL`

## Security Considerations

**Default bootstrap and admin credentials:**
- Risk: The repo defaults to usable local keys such as `nebula-dev-key` and `nebula-admin-key`
- Current mitigation: README guidance says to override them outside local development
- Recommendations: Fail startup outside `NEBULA_ENV=local` when defaults remain unchanged, or require explicit secrets in non-local environments

**Premium provider secret handling:**
- Risk: `NEBULA_PREMIUM_API_KEY` is trusted directly from environment configuration with no secret manager integration or masking policy in repo
- Current mitigation: The key is never intentionally returned by the admin API
- Recommendations: Document deployment-time secret handling and add tests ensuring premium secrets never leak into responses or logs

## Performance Bottlenecks

**Semantic cache embed-on-read/write path:**
- Problem: Every cache lookup and store requires an embedding request before Qdrant access
- Measurement: No benchmark number is checked in; the cost is visible in the implementation path
- Cause: `src/nebula/services/semantic_cache_service.py` always calls `OllamaEmbeddingsService.embed()` before lookup/store
- Improvement path: Add batching, short-circuit heuristics, or a local embedding cache if throughput becomes an issue

**SQLite-backed usage ledger:**
- Problem: All governance and usage writes go through one SQLite connection guarded by an `RLock`
- Measurement: No load-test figures are available in-repo
- Cause: `src/nebula/services/governance_store.py` uses serialized local writes for simplicity
- Improvement path: Move to a multi-process-safe database or isolate writes behind an async queue when concurrency increases

## Fragile Areas

**Streaming response assembly in `ChatService`:**
- Why fragile: Streaming behavior depends on prefetching the first provider event, reconstructing assistant role chunks, and mirroring ledger/caching side effects
- Common failures: Broken SSE framing, wrong reported model, mismatched fallback metadata, or ledger gaps
- Safe modification: Change streaming helpers together with `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and `tests/test_service_flows.py`
- Test coverage: Good relative coverage, but behavior is concentrated in a large file

**Container mutation in tests and runtime wiring:**
- Why fragile: Many tests replace providers and cache services by mutating `app.state.container` after app creation
- Common failures: Forgetting to update both `container.<service>` and the dependent `chat_service` or `provider_registry`
- Safe modification: Keep container attribute names stable or introduce dedicated test helpers for swap-in wiring
- Test coverage: Covered indirectly, but helper misuse is easy when adding new services

## Scaling Limits

**Single-process gateway state:**
- Current capacity: Not benchmarked in-repo
- Limit: Long-lived HTTP clients, SQLite writes, and Qdrant round trips are all process-local assumptions
- Symptoms at limit: Request contention around SQLite, slower cache paths, and operational complexity for horizontal scaling
- Scaling path: Externalize durable state and add deployment/worker guidance before multi-instance rollout

## Dependencies at Risk

**Ollama availability:**
- Risk: Local routing and embeddings both depend on the Ollama base URL being healthy
- Impact: Cache lookups degrade to misses and local completions trigger fallback or request failures
- Migration plan: Support a second local provider implementation or abstract embeddings away from Ollama-specific transport

**Qdrant optionality:**
- Risk: Semantic cache silently disables itself on startup or lookup/store errors
- Impact: The product keeps working but loses an optimization path, which can hide regressions until costs rise
- Migration plan: Add a stronger health signal and surface cache-disabled state in operator-facing diagnostics

## Missing Critical Features

**Explicit migration/deployment story:**
- Problem: The repo has local dev and benchmark tooling but no checked-in deployment manifests or DB migration workflow
- Current workaround: Manual environment setup plus runtime bootstrap
- Blocks: Predictable promotion to staging/production and repeatable infra changes
- Implementation complexity: Medium

## Test Coverage Gaps

**Production-like infrastructure failure modes:**
- What's not tested: Qdrant outages, persistent SQLite corruption/migration scenarios, and full benchmark subprocess failure reporting
- Risk: Operational failures may appear only in integrated environments
- Priority: Medium
- Difficulty to test: Moderate because current tests favor stubbed providers and in-process app setup

---

*Concerns audit: 2026-03-15*
*Update as issues are fixed or new ones discovered*
