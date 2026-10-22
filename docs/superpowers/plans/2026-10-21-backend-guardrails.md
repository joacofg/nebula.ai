# Backend guardrails and robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make tenant governance hold on every gateway path the audit found broken (fallback, ledger, restart, admin errors, rate limits) and clean the dead code around it.

**Architecture:** Fixes land at the seam that owns each behavior: `PolicyService` decides whether a premium fallback is allowed, `ChatService` gets one failure helper shared by streaming and non-streaming, `GovernanceStore` owns idempotent bootstrap and typed admin errors, `main.py` owns the OpenAI-shaped error body. No migration.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, pytest (asyncio auto), Next.js 15 / vitest for one console label change.

**Spec:** `docs/superpowers/specs/2026-10-21-backend-guardrails-design.md`

## Global Constraints

- RAM rules: every test run goes through `darwin-throttle` (`~/.local/bin`): `darwin-throttle .venv/bin/pytest <files> -q`; console: `darwin-throttle npm --prefix console test -- --run <files> --maxWorkers=2`. Never two suites at once. Never edit test-runner configs for this.
- The worktree `.env` comes from `.env.example` (no real premium key); never copy the main checkout's `.env`.
- Every behavior lands red first (`mattpocock-skills:tdd`): write the test, see it fail for the stated reason, then implement.
- Repo text in English; console copy in neutral Spanish without voseo (PRODUCT.md).
- Conventional commits (`fix:`, `feat:`, `chore:`, `test:`, `docs:`); one commit per task minimum. Commit messages end with the attribution lines from the session.
- Do not touch `scripts/metric_validation/` or `docs/evaluation.md`.
- Tests use the existing helpers in `tests/support.py`: `configured_app()`, `StubProvider`, `FakeCacheService`, `auth_headers()`, `admin_headers()`, `usage()`, `provider_error()`.

## Review Focus

- Streaming fallback that fails **after** the first chunk (mid-stream provider error) must still record exactly one ledger row, not two (Task 2 + Task 3 interaction) — test in Task 3.
- A tenant whose `allowed_premium_models` is empty means "any model": the fallback guard must not treat an empty list as "nothing allowed" — test in Task 2.
- The OpenAI error body must not break the console's admin playground, which goes through `/v1/admin/...` and reads `detail` — test in Task 7 asserts admin routes keep `{"detail": …}`.
- A rate-limited tenant sending a valid request after an invalid one must still be limited normally (moving the check into the handler must not skip it on any route) — test in Task 6 for both chat and embeddings.
- Bootstrap idempotency must not stop a fresh database from getting the bootstrap tenant, policy and key — test in Task 4.

---

### Task 1: Provider responses and errors

**Files:**
- Modify: `src/nebula/providers/openai_compatible.py`
- Modify: `src/nebula/providers/ollama.py`
- Test: `tests/test_openai_compatible_provider.py`, `tests/test_ollama_provider.py`

**Interfaces:**
- Produces: `ProviderError` messages of the form `"<Provider> completion failed: HTTP <status>: <first 300 chars of body>"` for `httpx.HTTPStatusError`; other `httpx.HTTPError`s keep `str(exc)`.

- [ ] **Step 1: Write the failing tests** (use `httpx.MockTransport` on the provider's client, as the existing tests do)
  - `test_null_content_is_an_empty_answer`: upstream `{"choices":[{"message":{"content":null},"finish_reason":"length"}],"usage":{...}}` → `result.content == ""`, usage parsed.
  - `test_http_error_keeps_upstream_status_and_body`: upstream 402 with body `{"error":{"message":"Insufficient credits"}}` → `ProviderError` whose message contains `"402"` and `"Insufficient credits"`.
  - `test_http_error_body_is_truncated`: 500 with a 2000-char body → message length of the body part ≤ 300.
  - Ollama: `test_http_error_keeps_upstream_status_and_body` with a 404 `{"error":"model 'x' not found"}`.
- [ ] **Step 2:** Run `darwin-throttle .venv/bin/pytest tests/test_openai_compatible_provider.py tests/test_ollama_provider.py -q` — expect the new tests to FAIL.
- [ ] **Step 3: Implement** `content or ""` in `complete()`, and a module-level `_describe_http_error(exc: httpx.HTTPError) -> str` in each provider (status + `exc.response.text[:300]` for `HTTPStatusError`) used by `_post` and `stream_complete`. For streams, read the body with `await response.aread()` before describing it.
- [ ] **Step 4:** Re-run — PASS.
- [ ] **Step 5: Commit** `fix(providers): keep upstream error text and accept null content`.

### Task 2: Premium fallback obeys the tenant; one failure helper for both paths

**Files:**
- Modify: `src/nebula/services/policy_service.py` (`PolicyResolution`, new method)
- Modify: `src/nebula/services/chat_service.py` (`create_completion_with_metadata`, `stream_completion_with_metadata`, `_prepare_stream_provider`, `_fallback_model`, `_route_tier`)
- Modify: `console/src/components/system/labels.ts` (add `local_provider_error_fallback_blocked: "fallback bloqueado por política"` to `ROUTE_REASONS`)
- Test: create `tests/test_fallback_guardrails.py`

**Interfaces:**
- Produces: `PolicyResolution.max_premium_cost_per_request: float | None = None` (filled from the policy in `resolve()`).
- Produces: `PolicyService.premium_fallback_block_reason(request: ChatCompletionRequest, resolution: PolicyResolution, model: str) -> str | None` — returns the spec's 502 detail for the first blocking condition in table order (`fallback_enabled` false, `local_only`, hard budget exceeded, model not in a non-empty allowlist, projected cost above the cap), else `None`. Projected cost uses the existing `_estimate_request_cost(request, model)`.
- Produces: `ChatService._fallback_model(resolution) -> str` — economy when configured and (allowlist empty or contains it), else `settings.premium_model`. `_route_tier` compares that model with `settings.economy_model` instead of testing truthiness.
- Produces: `ChatService._fail_provider(*, request, request_id, tenant_id, resolution, route_target, route_reason, provider_name, fallback_used, detail, started_at, cause) -> NoReturn` — records the `provider_error` ledger row with those values and raises a 502 `HTTPException(detail=detail, headers=self._error_headers(...))`. Every 502 in both paths goes through it; the streaming path's outer `except HTTPException` ledger write is deleted (pass `request_id` and `started_at` into `_prepare_stream_provider`).

- [ ] **Step 1: Write the failing tests**, each parametrized over `stream` in `{False, True}`, local `StubProvider` raising `provider_error("ollama down")`, premium `StubProvider` that records calls:
  - `test_fallback_blocked_by_local_only` — policy `routing_mode_default="local_only"`: 502, detail `"Local provider failed and tenant policy restricts routing to local only."`, premium call count 0, header `X-Nebula-Route-Reason: local_provider_error_fallback_blocked`, one ledger row with that reason, `fallback_used=False`.
  - `test_fallback_blocked_by_hard_budget` — `hard_budget_limit_usd=0.0`, `hard_budget_enforcement="downgrade"` (spend 0 ≥ 0): 502 with `"Local provider failed and the tenant hard budget is exhausted."`, premium not called.
  - `test_fallback_blocked_by_allowlist` — `allowed_premium_models=["some/other-model"]`, no economy model: detail `"Local provider failed and premium model '<settings.premium_model>' is not allowed for this tenant."`.
  - `test_fallback_blocked_by_cost_cap` — `max_premium_cost_per_request=0.0000001`, `max_tokens=4000`: detail `"Local provider failed and the premium fallback exceeds the tenant per-request cost limit."`.
  - `test_fallback_allowed_with_empty_allowlist` — `allowed_premium_models=[]`: 200, `X-Nebula-Fallback-Used: true`.
  - `test_fallback_sends_explicit_premium_model` — request `model=settings.local_model`, no economy: the premium stub receives `request.model == settings.premium_model`.
  - `test_failed_fallback_records_premium_row` — premium stub also raises: 502 with `X-Nebula-*` headers, ledger row `route_target="premium"`, `route_reason="local_provider_error_fallback"`, `fallback_used=True` — identical for stream and non-stream.
- [ ] **Step 2:** Run `darwin-throttle .venv/bin/pytest tests/test_fallback_guardrails.py -q` — FAIL (premium is called; stream rows differ).
- [ ] **Step 3: Implement** the interfaces above.
- [ ] **Step 4:** Run the new file plus `tests/test_chat_completions.py tests/test_response_headers.py tests/test_phase10_outage_safety.py tests/test_learned_routing.py` — PASS (update an existing assertion only where it asserted the old divergent streaming row; say which in the commit body).
- [ ] **Step 5: Commit** `fix(chat): premium fallback honors tenant guardrails on both paths`.

### Task 3: Abandoned streams reach the ledger

**Files:**
- Modify: `src/nebula/models/governance.py` (`TerminalStatus` gains `"client_disconnected"`)
- Modify: `src/nebula/services/chat_service.py` (`_wrap_stream_with_ledger`, `_record_usage` literal)
- Modify: `console/src/components/system/labels.ts` (`STATUSES.client_disconnected = "cortado por el cliente"`)
- Test: `tests/test_fallback_guardrails.py` (same file, new section) and the console labels test if one exists (`grep -rl "STATUSES\|statusLabel" console/src --include=*.test.*`)

**Interfaces:**
- Consumes: `_fail_provider` from Task 2 (a mid-stream provider error after the first chunk is recorded once, by the wrapper).
- Produces: `_wrap_stream_with_ledger` records exactly one row per stream in a `finally`, guarded by a `recorded` flag: normal end → existing status; provider error mid-stream → `provider_error`; `GeneratorExit` / `asyncio.CancelledError` → `client_disconnected` with usage estimated from the content seen so far.

- [ ] **Step 1: Write the failing tests**
  - `test_abandoned_premium_stream_is_recorded`: premium stub streaming 5 chunks; consume the first content event via the envelope's iterator, then `await stream.aclose()` → exactly one ledger row, `terminal_status == "client_disconnected"`, `completion_tokens > 0`, `estimated_cost > 0`.
  - `test_mid_stream_error_records_one_row`: stub yields one chunk then raises `ProviderError` → exactly one row, `terminal_status == "provider_error"`.
- [ ] **Step 2:** Run — FAIL (zero rows on abandon).
- [ ] **Step 3: Implement.** Record synchronously-safe: the ledger write must not await anything that can be cancelled (the store call is synchronous; keep it that way inside the `finally`).
- [ ] **Step 4:** Run the file plus `tests/test_chat_completions.py` — PASS; console labels test PASS.
- [ ] **Step 5: Commit** `fix(chat): record streams the client abandons`.

### Task 4: Restart-safe bootstrap and one operator key

**Files:**
- Modify: `src/nebula/services/governance_store.py` (`ensure_bootstrap`, `ensure_api_key`, new `operator_api_key`)
- Modify: `src/nebula/api/routes/admin.py` (recommendations, simulate), `src/nebula/services/auth_service.py` (`resolve_playground_context`)
- Test: `tests/test_governance_runtime_hardening.py`

**Interfaces:**
- Produces: `GovernanceStore.find_api_key_by_secret(raw_key: str, *, include_revoked: bool) -> StoredApiKey | None` (the existing `find_api_key(raw)` becomes `find_api_key_by_secret(raw, include_revoked=False)` or calls it).
- Produces: `GovernanceStore.operator_api_key() -> ApiKeyRecord` — the bootstrap key record, revoked or not, created only if no row has its hash.
- `ensure_bootstrap()` creates the bootstrap tenant (with `default_policy()`) only when `get_tenant` returns `None`, then calls `operator_api_key()`.

- [ ] **Step 1: Write the failing tests**
  - `test_restart_keeps_bootstrap_tenant_policy`: initialize; set the default tenant's policy to `rate_limit_requests_per_minute=5, routing_quality_target=0.8, hard_budget_limit_usd=1.0` and `active=False`; call `ensure_bootstrap()` again → all four values unchanged.
  - `test_restart_with_revoked_bootstrap_key`: revoke the bootstrap key; `ensure_bootstrap()` raises nothing; `find_api_key(bootstrap)` is `None` (still revoked).
  - `test_operator_flows_work_with_revoked_bootstrap_key` (API, `configured_app()`): after revoking, `GET /v1/admin/tenants/default/recommendations`, `POST /v1/admin/tenants/default/policy/simulate` and the admin playground completion each return 200.
  - `test_fresh_database_gets_bootstrap_tenant_and_key`: empty DB → tenant, policy and an unrevoked bootstrap key exist.
- [ ] **Step 2:** Run `darwin-throttle .venv/bin/pytest tests/test_governance_runtime_hardening.py -q` — FAIL (`IntegrityError`, policy reset).
- [ ] **Step 3: Implement**; replace the three find-or-create blocks with `operator_api_key()`.
- [ ] **Step 4:** Run the file plus `tests/test_governance_api.py tests/test_admin_playground_api.py` — PASS.
- [ ] **Step 5: Commit** `fix(governance): make bootstrap idempotent across restarts`.

### Task 5: Typed admin errors

**Files:**
- Modify: `src/nebula/services/governance_store.py` (exceptions, `create_tenant`, `create_api_key`, `list_api_keys`)
- Modify: `src/nebula/api/routes/admin.py` (create tenant, create key)
- Modify: `scripts/seed_demo_data.py` (skip keys with `revoked_at`)
- Test: `tests/test_governance_api.py`, `tests/test_demo_prepare.py` if it covers the seed check

**Interfaces:**
- Produces in `governance_store.py`: `class TenantAlreadyExistsError(ValueError)`, `class UnknownTenantError(ValueError)`, `class ApiKeyAlreadyExistsError(ValueError)`. `create_api_key` checks the hash (revoked or not) before inserting.
- Admin routes map them to 409 / 404 / 409 with the spec's exact details.

- [ ] **Step 1: Write the failing tests**: duplicate tenant → 409 `"Tenant 'acme' already exists."`; key with an existing raw `key` → 409 `"An API key with this secret already exists."`; key for tenant `ghost` → 404 `"Unknown tenant: ghost"`; `GET /v1/admin/api-keys?tenant_id=b` includes a key created with `tenant_id=None, allowed_tenant_ids=["a","b"]`; seed check treats a revoked `acme-demo-key` as absent.
- [ ] **Step 2:** Run — FAIL (500s).
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run the touched test files — PASS.
- [ ] **Step 5: Commit** `fix(admin): 409 and 404 instead of 500 on duplicate or unknown records`.

### Task 6: Rate limiter edges

**Files:**
- Modify: `src/nebula/services/rate_limiter.py`
- Modify: `src/nebula/api/dependencies.py` (`get_rate_limited_tenant_context` → `enforce_rate_limit`)
- Modify: `src/nebula/api/routes/chat.py`, `src/nebula/api/routes/embeddings.py`
- Test: `tests/test_rate_limiter.py`, `tests/test_rate_limiting.py`

**Interfaces:**
- Produces: `async def enforce_rate_limit(request: Request, response: Response, tenant_context: AuthenticatedTenantContext) -> None` in `dependencies.py`, called as the first statement of both handlers (which now depend on plain `get_tenant_context`), so a body that fails validation never reaches it. Same 429, ledger row and headers as today.
- Produces: `_Bucket.capacity: float`; on `acquire`, a higher capacity adds `new - old` tokens; buckets with `now - updated_at >= 60` are swept at most once per 60 s; `RateLimiter.bucket_count` property for tests.

- [ ] **Step 1: Write the failing tests**
  - `test_invalid_body_does_not_spend_a_token` (chat and embeddings): limit 1; POST a schema-invalid body (`{"messages": []}` / `{"input": []}`) → 422; then a valid request → 200.
  - `test_raising_the_limit_grants_tokens_now`: fake clock; limit 2, spend 2; `acquire(limit=5)` → allowed, `remaining == 2`.
  - `test_idle_buckets_are_swept`: fake clock; acquire `t1`; advance 61 s; acquire `t2` → `bucket_count == 1`.
  - `test_limit_still_applies_after_valid_requests`: limit 1, two valid requests → 200 then 429 (chat and embeddings).
- [ ] **Step 2:** Run both files — FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run both files plus `tests/test_embeddings_api.py tests/test_chat_completions.py` — PASS.
- [ ] **Step 5: Commit** `fix(rate-limit): validate before spending, sweep idle buckets, honor raised limits`.

### Task 7: OpenAI-shaped errors with every header

**Files:**
- Modify: `src/nebula/main.py` (exception handlers)
- Test: create `tests/test_error_contract.py`

**Interfaces:**
- Consumes: `request.state.rate_limit_headers` (set by `enforce_rate_limit`).
- Produces: handlers for `HTTPException` and `RequestValidationError` that, for paths under `{api_v1_prefix}/chat/completions` and `{api_v1_prefix}/embeddings`, return the spec's body and merge `exc.headers` with `request.state.rate_limit_headers`; every other path delegates to FastAPI's default handlers unchanged.

- [ ] **Step 1: Write the failing tests**: 401 on chat → `body["error"]["type"] == "authentication_error"` and `body["detail"]` equals the message; a policy 403 on a tenant with `rate_limit_requests_per_minute=10` → `X-RateLimit-Limit: 10` present and `error.code` equals the route reason header; a 502 (local stub failing, fallback disabled) → `X-RateLimit-Limit` and `X-Nebula-Route-Tier` present; 422 validation → `type == "invalid_request_error"`; `GET /v1/admin/tenants/missing` → body is exactly `{"detail": "Tenant not found."}`.
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run the new file plus `tests/test_chat_completions.py tests/test_embeddings_api.py tests/test_rate_limiting.py tests/test_governance_api.py` — PASS (existing tests reading `detail` keep working).
- [ ] **Step 5: Commit** `feat(api): OpenAI-shaped errors that keep rate-limit and route headers`.

### Task 8: Remove the dead budget signal

**Files:**
- Modify: `src/nebula/services/router_service.py` (`CalibratedScoreBreakdown`, `_build_breakdown`, signal and score-component serialization)
- Modify: `console/src/components/ledger/ledger-request-detail.tsx` (drop the "Penalidad de presupuesto" and proximity rows), its type in `console/src/lib/admin-api.ts` if declared
- Test: update `tests/test_router_signals.py`, `tests/test_response_headers.py`, `tests/test_chat_completions.py`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx` (paths per `grep -rn budget_penalty\|budget_proximity tests console/src`)

- [ ] **Step 1:** Change the assertions first: `score_components` no longer contains `budget_penalty`; signals no longer contain `budget_proximity`; the ledger detail renders no "Penalidad de presupuesto". Run — FAIL.
- [ ] **Step 2: Implement** the removal; `total_score` formula drops the `- budget_penalty` term.
- [ ] **Step 3:** Run the backend files and the two console test files — PASS; `grep -rn "budget_penalty\|budget_proximity" src console/src tests` returns nothing.
- [ ] **Step 4: Commit** `refactor(router): drop the budget penalty that was always zero`.

### Task 9: Security hygiene

**Files:**
- Modify: `docker-compose.selfhosted.yml` (`"127.0.0.1:5432:5432"`, `"127.0.0.1:6333:6333"`)
- Modify: `src/nebula/services/auth_service.py` (`hmac.compare_digest`)
- Modify: `src/nebula/models/openai.py` (`model: str = Field(default="nebula-auto", max_length=255)`), the tenant create request model (`id` max 255), `src/nebula/observability/middleware.py` (`X-Request-ID` truncated to 128)
- Test: `tests/test_chat_completions.py`, `tests/test_governance_api.py`, `tests/test_health.py` (or the file covering the middleware)

- [ ] **Step 1: Write the failing tests**: model of 300 chars → 422; tenant id of 300 chars → 422; `X-Request-ID` of 500 chars → response `X-Request-ID` has length 128; admin auth still accepts the right key and rejects a key differing in the last char (401).
- [ ] **Step 2:** Run — FAIL on the first three.
- [ ] **Step 3: Implement**; add a one-line comment in the compose file that the data stores are reachable only from the host.
- [ ] **Step 4:** Run — PASS.
- [ ] **Step 5: Commit** `fix(security): bound client strings, constant-time admin key, local-only data stores`.

### Task 10: Dead code, deprecation, docs

**Files:**
- Modify: `src/nebula/services/policy_service.py`, `router_service.py`, `governance_store.py`, `recommendation_service.py`, `core/container.py`, `models/governance.py`, `chat_service.py`, `api/routes/embeddings.py`, `api/routes/admin.py`
- Modify: `tests/test_service_flows.py`, `tests/test_learned_routing.py` (move off the removed wrappers)
- Modify: `docs/self-hosting.md`, `TODOS.md`

- [ ] **Step 1:** Remove the symbols listed in the spec's Cleanup section; replace `HTTP_422_UNPROCESSABLE_ENTITY` with `HTTP_422_UNPROCESSABLE_CONTENT` (3 sites); tests that called `create_completion` / `stream_completion` call the `_with_metadata` variants.
- [ ] **Step 2:** `grep -rn "_enforce_explicit_model_constraints\|uses_embeddings\|HTTP_422_UNPROCESSABLE_ENTITY\|M009\|Phase 3" src` returns nothing; `darwin-throttle .venv/bin/pytest -q -W error::DeprecationWarning tests/test_embeddings_api.py tests/test_governance_api.py` — PASS.
- [ ] **Step 3:** Docs: in `docs/self-hosting.md`, correct the `runtime_profile` description and add the rolling-budget note (B9) under budgets; in `TODOS.md`, delete the "Admin create endpoints return 500" and "`budget_penalty` is a dead routing signal" sections.
- [ ] **Step 4:** `make lint` clean.
- [ ] **Step 5: Commit** `chore: remove dead code and deprecated status constant`.

### Task 11: CI builds the console and runs e2e

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1:** Add to the console job, after Test: `- name: Build` → `npm run build`. Add a job `console-e2e` (needs nothing else; `working-directory: console`; Node 22 with npm cache; `npm ci`; `npx playwright install --with-deps chromium`; `npm run e2e`).
- [ ] **Step 2:** Locally, with no dev server running: `darwin-throttle npm --prefix console run e2e` — all specs pass. If a spec fails, fix the spec or the component it exposes in this task and say so in the commit body.
- [ ] **Step 3: Commit** `ci: build the console and run the Playwright suite`.

### Task 12: Full verification

- [ ] `darwin-throttle make test` — summary line `N passed, 0 failed`.
- [ ] `make lint` — clean.
- [ ] `darwin-throttle npm --prefix console test -- --run --maxWorkers=2`, `npx --prefix console tsc --noEmit -p console/tsconfig.json`, `npm --prefix console run lint` — green.
- [ ] `python -m scripts.thesis.tables --check` — no stale blocks (no thesis number moved).
