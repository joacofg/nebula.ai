# M003 / S01 — Research

**Date:** 2026-03-23

## Summary

S01 directly owns **R020** and is the runtime foundation for later slices that support **R021–R023**. The codebase already has the two critical halves needed for a narrow public embeddings surface: authenticated public-route patterns (`src/nebula/api/routes/chat.py`, `src/nebula/api/dependencies.py`, `src/nebula/observability/middleware.py`) and an internal Ollama-backed embeddings capability (`src/nebula/services/embeddings_service.py`). This looks like **targeted/light research**, not a novel subsystem: the safest path is to add a sibling FastAPI route for `POST /v1/embeddings`, define a small OpenAI-style request/response schema in `src/nebula/models/openai.py`, and keep the supported contract intentionally narrow per D015.

The important implementation constraint is that the existing embeddings service only exposes `embed(text: str) -> list[float] | None` and always uses `settings.embedding_model`, while the milestone contract says the public request must accept `input` + `model`, including simple batch input. That means S01 is not just route wiring: the executor will likely need to extend `OllamaEmbeddingsService` to support explicit model forwarding and batch inputs, then make the public route validate only the strict happy path. Reuse the existing public auth path and `X-Request-ID` middleware behavior; do not invent a new auth scheme, helper layer, or broad embeddings-option parity surface.

## Recommendation

Build the slice in this order: **(1)** define the narrow OpenAI-style embeddings schemas, **(2)** extend the internal embeddings service so the public route can actually honor the S01 contract (`model`, string input, simple batch input), **(3)** add a dedicated `src/nebula/api/routes/embeddings.py` route that mirrors the chat route’s dependency/auth shape, and **(4)** add focused API + service tests proving authenticated happy-path behavior, validation boundaries, and durable evidence via the existing usage ledger path.

Use the chat route as the pattern to copy, but do **not** force embeddings through `ChatService`. Chat-specific routing, cache, fallback, and chat ledger semantics are tightly coupled to messages and completions. For S01, the narrowest credible design is a small dedicated embeddings path that depends on `get_tenant_context`, calls the embeddings service directly, returns an OpenAI-style embeddings response, and records enough durable evidence in the existing `usage_ledger` surface for later slices to correlate by `request_id`. If the team wants correlation without a schema migration, the current ledger shape can already carry `request_id`, `tenant_id`, `requested_model`, `final_route_target`, `final_provider`, `response_model`, token counts (likely zero), `terminal_status`, and `route_reason`; the planner should explicitly evaluate whether that is sufficient for embeddings proof or whether a tiny ledger extension is required.

## Implementation Landscape

### Key Files

- `src/nebula/services/embeddings_service.py` — existing internal Ollama client. Today it only supports single-string embedding via `embed(text)` and silently uses `settings.embedding_model`. This is the main runtime gap versus the public S01 contract.
- `src/nebula/models/openai.py` — current home for public OpenAI-style schemas. Add the narrow embeddings request/response models here to keep the compatibility surface centralized.
- `src/nebula/api/routes/chat.py` — best reference for public-route shape: `APIRouter`, `get_tenant_context`, `Request`/`Response`, request ID handling, and response header conventions.
- `src/nebula/api/dependencies.py` — already exposes `get_tenant_context`; embeddings should reuse this exact dependency so auth/tenant behavior matches the existing adoption path.
- `src/nebula/main.py` — includes routers under `settings.api_v1_prefix`. S01 will need to register a new embeddings router here.
- `src/nebula/core/container.py` — already constructs `self.embeddings_service = OllamaEmbeddingsService(settings)`. No new container concept is needed; route code can depend on the existing service from the container.
- `src/nebula/observability/middleware.py` — assigns `request.state.request_id` and always emits `X-Request-ID`. Embeddings should lean on this rather than reimplementing request correlation.
- `src/nebula/services/governance_store.py` — `record_usage()` / `list_usage_records()` define the current durable evidence surface. Later slices will depend on whatever S01 records here.
- `src/nebula/models/governance.py` and `src/nebula/db/models.py` — current ledger record + table schema. Review before deciding whether embeddings evidence fits the current fields without migration.
- `tests/support.py` — `configured_app()` bootstraps migrated test apps and `auth_headers()` provides the public auth contract. New embeddings API tests should follow this pattern.
- `tests/test_chat_completions.py` — best template for public API assertions: authenticated request, OpenAI-like response body, and Nebula headers.
- `tests/test_response_headers.py` — shows current expectations around `X-Nebula-*` metadata on public routes. If embeddings emits fewer headers than chat, docs/tests must state that clearly.
- `tests/test_governance_api.py` — current proof that public requests can be correlated to `/v1/admin/usage/ledger?request_id=...`. This is the right place to add or extend evidence tests for embeddings if S01 records ledger rows.
- `tests/test_service_flows.py` — useful if the executor introduces a dedicated embeddings service/orchestrator and wants fast unit coverage without full FastAPI setup.

### Build Order

1. **Prove the runtime gap first in `embeddings_service.py`.** The internal service must support the milestone contract: requested model passthrough and both string + simple list input. Until this is solved, route work is superficial.
2. **Add schema models in `src/nebula/models/openai.py`.** This locks the public contract boundary early and gives tests a stable target.
3. **Add `src/nebula/api/routes/embeddings.py` and register it in `src/nebula/main.py`.** Reuse `get_tenant_context` and request ID middleware. Keep the route strict and happy-path only.
4. **Add focused API tests first, then evidence tests.** Start with authenticated 200 response coverage for single-string and simple batch inputs; then add negative validation tests for unsupported edges; finally add request-correlation / ledger assertions if S01 records embeddings usage.
5. **Only then decide whether a ledger/schema change is needed.** The current ledger can likely hold minimal embeddings evidence, but this should be tested against R020/R023 proof needs instead of assumed.

### Verification Approach

- Run focused API tests for the new route, likely a new `tests/test_embeddings_api.py` or additions near `tests/test_chat_completions.py`:
  - authenticated `POST /v1/embeddings` returns 200
  - string input returns OpenAI-style `data[0].embedding`
  - simple batch input returns ordered `data[*]`
  - missing/invalid auth returns existing public auth errors
  - unsupported shapes/options return FastAPI validation errors or explicit narrow-contract failures
- Run governance/evidence tests if usage is recorded:
  - public embeddings request emits `X-Request-ID`
  - `/v1/admin/usage/ledger?request_id=...` returns a correlatable row for that request
- Suggested commands:
  - `pytest tests/test_embeddings_api.py`
  - `pytest tests/test_governance_api.py -k embeddings`
  - if coverage is added there: `pytest tests/test_service_flows.py -k embedding`

## Constraints

- D015 is the hard contract boundary: support only the strict happy path — `POST /v1/embeddings` with `input` + `model`, string input and simple batch input, and standard float embeddings response shape.
- `src/nebula/services/embeddings_service.py` currently hardcodes `settings.embedding_model`; public `model` support requires explicit change.
- The existing embeddings service returns `None` on blank input or upstream HTTP failure. Public-route behavior must convert that into an intentional API outcome; silent `None` is not a valid public response.
- `RequestContextMiddleware` already owns `X-Request-ID`; do not add custom request ID generation in the route.
- The current public auth contract is `X-Nebula-API-Key` plus existing tenant resolution rules from `AuthService`; S01 should not introduce bearer auth or a separate embeddings auth path.
- There is no active LSP server in this worktree, so planners/executors should rely on direct file reads and focused pytest coverage rather than semantic tooling.

## Common Pitfalls

- **Assuming the internal embeddings helper already matches OpenAI-style public needs** — it does not; it only embeds one string and ignores caller-supplied model names.
- **Overusing chat-route metadata conventions without deciding the embeddings contract** — chat’s `X-Nebula-*` headers are tied to routing/cache/fallback semantics. Reuse only what is truthful for embeddings.
- **Skipping durable evidence design until later** — S04 will depend on whatever S01 records. If embeddings requests are not persisted in a correlatable way now, later slices may need avoidable rework.
- **Letting “simple batch input” drift into broad parity** — keep support to string or flat list-of-strings only unless tests prove another shape is essential.

## Open Risks

- The current `usage_ledger` schema may be only barely sufficient for embeddings evidence; if later slices need dimensions/input-count/object-type visibility, S01 may need a small schema extension sooner than expected.
- Upstream Ollama `/api/embed` request/response behavior for batch inputs is implied by current code usage but not proven in repo tests yet; executor should lock this down with stubbed tests around the service boundary.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| FastAPI | installed skills list does not include a FastAPI-specific local skill; external option `wshobson/agents@fastapi-templates` | available |
