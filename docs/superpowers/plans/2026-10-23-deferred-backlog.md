# Deferred Backlog (PR 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close B16–B20 and the PR 2 / PR 3 deferred minors without changing what thesis figures 10.3, 10.6, 10.7 and 11.1 show.

**Architecture:** Backend fixes stay inside the existing seams: provider adapters, `ChatService`, `PolicyService`,
`GovernanceStore`, the simulation service, the observability module and the semantic cache service. Console fixes
touch `labels.ts`, three components and one hook, plus test fixtures. One task per seam, each red-green.

**Tech Stack:** Python 3.12, FastAPI 0.135, SQLAlchemy 2 (sync), httpx, pytest; Next.js 15, React 19, TanStack Query, vitest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-23-deferred-backlog-design.md`

## Global Constraints

- No paid API calls; premium runs use `NEBULA_PREMIUM_PROVIDER=mock`; Ollama local only. Never `make demo`.
- Never modify `scripts/metric_validation/`, `docs/evaluation.md`, `scripts/ground_truth/label.py`, `benchmarks/ground-truth/v1/`, `benchmarks/cache/v1/`.
- Console copy in neutral Spanish without voseo; colors only through DESIGN.md roles; admin session and selected tenant in memory only.
- Do not change what figures 10.3, 10.6, 10.7 or 11.1 show; if a change would, stop and report.
- The finish-reason Literal is exactly `stop | length | content_filter | tool_calls`.
- New setting `NEBULA_EVIDENCE_SUMMARY_TTL_SECONDS`, default `30`, `0` disables the memo.
- Prometheus `path` label for unmatched requests is exactly `"unmatched"`.
- Fallback note copy, exact: `Se sirvió con {served} por un fallback; el router había elegido {chosen}.`
- Policy-source clause, exact: ` · {N} por la política`, rendered only when N > 0.
- Commit prefixes fix/feat/docs/chore/test; trailers exactly `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_012JwPQqsnEebt9XQ2BG378E`.

## Review Focus

- A client disconnecting mid-stream after B16c's "keep reading after finish" must still write exactly one ledger row (B5 must not regress).
- A premium stream whose provider sends no usage chunk (mock, older OpenRouter routes) must still record the chars/4 estimate, not zero tokens.
- A tenant with no ledger rows and a simulation window with ties on timestamp: the batched spend must equal the per-row query (strict `<`).
- When Qdrant is down at startup and comes back, a request during the background re-init must answer as a cache miss/disabled quickly, never raise, and never start a second concurrent `initialize()`.
- A ledger row whose `route_signals` is `None` because it was a cache hit or an embeddings call must not render "Por qué este nivel" as a fallback, and the playground (no ledger row) must keep today's behavior.

---

### Task 1: finish_reason passthrough and n > 1 rejection (B16a, B16b)

**Files:**
- Modify: `src/nebula/models/openai.py` (`n` field, `FinishReason` alias, normalizer)
- Modify: `src/nebula/providers/ollama.py` (`done_reason`), `src/nebula/providers/openai_compatible.py` (stop forwarding `n`; normalize)
- Modify: `src/nebula/services/chat_service.py` (`_build_response` takes `finish_reason`; caller passes `result.finish_reason`; stream chunks normalize)
- Test: `tests/test_chat_completions.py`, `tests/test_ollama_provider.py`, `tests/test_openai_compatible_provider.py`, `tests/test_error_contract.py`

**Interfaces:**
- Produces: `FinishReason = Literal["stop", "length", "content_filter", "tool_calls"]` and `normalize_finish_reason(value: str | None) -> FinishReason` in `nebula.models.openai`.

- [ ] **Step 1: Failing tests**
  - `test_normalize_finish_reason_maps_into_the_literal`: parametrize `("stop","stop"), ("length","length"), ("content_filter","content_filter"), ("tool_calls","tool_calls"), ("function_call","tool_calls"), (None,"stop"), ("error","stop")`.
  - `test_chat_completion_returns_provider_finish_reason`: StubProvider returns `CompletionResult(finish_reason="length")`, so the response has `choices[0].finish_reason == "length"`.
  - `test_ollama_maps_done_reason_length`: MockTransport body with `"done_reason": "length"` → `CompletionResult.finish_reason == "length"`; with `"done_reason": "load"` → `"stop"`. Same for the stream's final chunk.
  - `test_premium_stream_with_unknown_finish_reason_does_not_break`: SSE finish chunk with `"finish_reason": "error"` → the client receives a final chunk with `"stop"` and `[DONE]`.
  - `test_n_greater_than_one_is_rejected`: POST with `n: 2` → 422 in the existing error shape (copy the assertions the file already uses for a 422); `n: 1` still 200.
  - `test_payload_does_not_forward_n`: `_build_payload` output has no `"n"` key.
- [ ] **Step 2: Run them** with `darwin-throttle .venv/bin/pytest tests/test_chat_completions.py tests/test_ollama_provider.py tests/test_openai_compatible_provider.py tests/test_error_contract.py -q`. Expected: the new tests fail.
- [ ] **Step 3: Implement.** `n: int | None = Field(default=1, ge=1, le=1)`. Normalize at every place a `ChatCompletionChoice` or `ChatCompletionChunkChoice` is built from a provider value. The cache-hit paths keep `"stop"`.
- [ ] **Step 4: Run the full backend suite** (`darwin-throttle .venv/bin/pytest -q`) and `.venv/bin/ruff check .`. Expected: all green.
- [ ] **Step 5: Commit** `fix: pass finish_reason through and reject n > 1`.

### Task 2: streaming premium cost from provider usage (B16c)

**Files:**
- Modify: `src/nebula/providers/base.py` (`CompletionChunk.usage: CompletionUsage | None = None`)
- Modify: `src/nebula/providers/openai_compatible.py` (send `stream_options`, parse usage-only and finish chunks, skip chunks with empty `choices` for content)
- Modify: `src/nebula/providers/mock_premium.py` (final chunk carries usage, so mock runs exercise the path)
- Modify: `src/nebula/services/chat_service.py` (`_stream_provider` keeps reading after the finish chunk until the provider iterator ends and yields no content after finish; `_wrap_stream_with_ledger` uses the usage when one arrived, else `estimate_usage`)
- Test: `tests/test_openai_compatible_provider.py`, `tests/test_chat_completions.py` (or the stream ledger test file that already covers B5)

**Interfaces:**
- Consumes: `normalize_finish_reason` (Task 1).
- Produces: `CompletionChunk.usage`. A chunk with `delta == ""` and `usage` set is a usage-only chunk.

- [ ] **Step 1: Failing tests**
  - `test_stream_payload_requests_usage`: `_build_payload(stream=True)` includes `"stream_options": {"include_usage": True}`; non-stream omits it.
  - `test_stream_parses_usage_only_chunk`: raw SSE `finish chunk`, then `{"choices": [], "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}}`, then `[DONE]` → the last chunk yielded has `usage == CompletionUsage(11, 7, 18)` and no IndexError.
  - `test_stream_parses_usage_on_finish_chunk`: usage in the same chunk as `finish_reason` → captured.
  - `test_premium_stream_ledger_uses_provider_usage`: stub premium provider streams `"hola"` then a usage chunk (11/7), so the ledger row has `prompt_tokens == 11`, `completion_tokens == 7`, and the cost is priced from those tokens.
  - `test_premium_stream_without_usage_falls_back_to_estimate`: no usage chunk, so the ledger tokens equal `estimate_usage(...)` output (the pre-change behavior).
  - `test_stream_disconnect_after_finish_writes_one_row`: client disconnects after the finish chunk but before the usage chunk, so exactly one ledger row is written (`terminal_status` as today for a completed stream; estimate tokens).
- [ ] **Step 2: Run them.** Expected: they fail.
- [ ] **Step 3: Implement.** The usage travels from `_stream_provider` to the ledger wrapper through a small mutable holder owned by the wrapper (a dataclass with `usage: CompletionUsage | None`). No new globals.
- [ ] **Step 4: Run the full backend suite and ruff.** Expected: green.
- [ ] **Step 5: Commit** `fix: price streamed premium responses from provider usage`.

### Task 3: governance store off the event loop (B17)

**Files:**
- Modify: `src/nebula/api/dependencies.py` (rate-limit rejection writes at `:58`, `:103`)
- Modify: `src/nebula/services/policy_service.py` (`evaluate` reads spend and the evidence summary via `run_in_threadpool`; `evaluate_decision(..., tenant_spend_total: float | None = None)` uses the value when given, else calls the store as today)
- Modify: `src/nebula/services/chat_service.py` (`_record_usage` and `_record_policy_denial` in non-stream paths are awaited through `run_in_threadpool`; the stream `finally` write stays sync with a comment that cites the reason in the spec)
- Modify: `src/nebula/api/routes/embeddings.py` (`:122`), `src/nebula/api/routes/admin.py` (handlers that await nothing become `def`; handlers that await keep `async def` and wrap their store calls)
- Create: `tests/test_event_loop_offload.py`

**Interfaces:**
- Produces: `PolicyService.evaluate_decision(*, request, tenant_context, route_decision, before_timestamp=None, evidence_summary=None, tenant_spend_total: float | None = None) -> PolicyEvaluation`.
- Use `from starlette.concurrency import run_in_threadpool`.

- [ ] **Step 1: Failing tests** in `tests/test_event_loop_offload.py`, using a helper `record_loop_calls(store, names) -> list[tuple[str, bool]]`. It wraps the named methods on the container's governance store and records `(name, on_loop)`, where `on_loop` is whether `asyncio.get_running_loop()` succeeds inside the call.
  - `test_chat_completion_store_calls_run_off_the_loop`: non-stream chat with the stub local provider. Every recorded call to `tenant_spend_total`, `summarize_calibration_evidence` and `record_usage` has `on_loop is False`.
  - `test_streaming_ledger_write_is_the_only_on_loop_call`: a stream request. `record_usage` is on the loop (documented exception) and the policy reads are off.
  - `test_embeddings_ledger_write_runs_off_the_loop`.
  - `test_rate_limited_rejection_write_runs_off_the_loop`: exhaust the bucket (copy the setup from the existing rate-limit tests).
  - `test_admin_store_calls_run_off_the_loop`: parametrize over `GET /v1/admin/tenants`, `GET …/policy`, `PUT …/policy`, `GET /v1/admin/usage/ledger`, `POST …/policy/simulate`, `GET /v1/admin/api-keys`.
- [ ] **Step 2: Run them.** Expected: they fail with `on_loop is True`.
- [ ] **Step 3: Implement.** Keep behavior identical otherwise. The B10 error handling around store failures must still produce the same status codes.
- [ ] **Step 4: Run the full backend suite and ruff.** Expected: green.
- [ ] **Step 5: Commit** `fix: run governance store calls off the event loop`.

### Task 4: outcome-evidence memo and classification (B18)

**Files:**
- Modify: `src/nebula/core/config.py` (`evidence_summary_ttl_seconds: float = 30`, env `NEBULA_EVIDENCE_SUMMARY_TTL_SECONDS`)
- Modify: `src/nebula/services/policy_service.py` (per-tenant memo `{tenant_id: (expires_at, summary)}`. The clock is injectable: `PolicyService(..., clock: Callable[[], float] = time.monotonic)`. TTL `0` means always recompute. The memo is filled through the off-loop read from Task 3.)
- Modify: `src/nebula/core/container.py` (pass the setting)
- Modify: `src/nebula/services/governance_store.py` (exclusion: `message_type == "embeddings"` → excluded reason `embeddings_request`; `terminal_status in {"policy_denied", "rate_limited"}` → excluded reason `denied_request`. Exclusions are checked before the degraded check.)
- Modify: tests that seed rows and then expect the updated evidence within one app: set `NEBULA_EVIDENCE_SUMMARY_TTL_SECONDS=0` in their `configured_app(...)` call. Do not change their assertions.
- Test: `tests/test_service_flows.py`, `tests/test_governance_api.py`

**Interfaces:**
- Consumes: Task 3's off-loop `evaluate`.

- [ ] **Step 1: Failing tests**
  - `test_evidence_summary_is_reused_within_ttl`: fake clock at 0, two `resolve` calls → `store.evidence_summary_calls == ["default"]`. Advance to 31, third call → `["default", "default"]`.
  - `test_evidence_summary_ttl_zero_recomputes_every_request`.
  - `test_embeddings_rows_are_excluded_not_degraded`: 5 sufficient calibrated rows + 1 embeddings row → `state == "sufficient"`, `degraded_request_count == 0`, `excluded_request_count == 1`.
  - `test_denied_rows_are_excluded_not_degraded`: the same, with one `policy_denied` row and one `rate_limited` row → `excluded_request_count == 2`.
- [ ] **Step 2: Run them.** Expected: they fail.
- [ ] **Step 3: Implement.** The console's reason labels: if a new excluded reason key reaches the console (`labels.ts` reason map), add its Spanish label. Use `embeddings_request` → `"pedido de embeddings"` and `denied_request` → `"pedido denegado"`, with a labels test row each.
- [ ] **Step 4: Run the full backend suite and ruff.** If `labels.ts` changed, also run the console checks from rules.md. Expected: green.
- [ ] **Step 5: Commit** `fix: memoize the outcome-evidence summary and exclude embeddings and denied rows`.

### Task 5: simulation spend in one pass (B19)

**Files:**
- Modify: `src/nebula/services/governance_store.py`. Add `tenant_spend_before(tenant_id: str, timestamps: Sequence[datetime]) -> list[float]`, one value per input timestamp, in input order, each equal to `tenant_spend_total(tenant_id, before_timestamp=t)`. It uses the spend-status list `tenant_spend_total` uses.
- Modify: `src/nebula/services/policy_simulation_service.py` (call it once for the replayed rows; pass each value as `tenant_spend_total=` to `evaluate_decision` / `evaluate`)
- Modify: `src/nebula/services/policy_service.py` (`evaluate(..., tenant_spend_total: float | None = None)` forwards it)
- Test: `tests/test_governance_store.py` (or the file that tests `tenant_spend_total`), `tests/test_service_flows.py`

**Interfaces:**
- Consumes: `evaluate_decision(..., tenant_spend_total=)` (Task 3).

- [ ] **Step 1: Failing tests**
  - `test_tenant_spend_before_matches_per_row_query`. Rows at t1 < t2 = t2 < t3, plus one before the window, one non-spend status and one other tenant. Query timestamps `[t3, t1, t2, t_before_all]` → equals `[tenant_spend_total(before_timestamp=t) for t in …]` exactly.
  - `test_tenant_spend_before_empty_tenant_returns_zeros`.
  - `test_simulation_queries_spend_once`: simulate over 20 rows with a counting store → `tenant_spend_total` calls `== 0` and `tenant_spend_before` calls `== 1`, and the `PolicySimulationResponse` is identical to the one produced with a store subclass whose `tenant_spend_before` returns `[tenant_spend_total(tenant_id, before_timestamp=t) for t in timestamps]`.
- [ ] **Step 2: Run them.** Expected: they fail.
- [ ] **Step 3: Implement** with two queries: a SUM before `min(timestamps)` and an ordered `(timestamp, cost)` select in `[min, max)`. Then a prefix sum with `bisect_left`.
- [ ] **Step 4: Run the full backend suite and ruff.** Expected: green.
- [ ] **Step 5: Commit** `fix: compute simulation spend in one pass`.

### Task 6: observability and small backend fixes (B20, retention, embedding model names)

**Files:**
- Modify: `src/nebula/observability/logging.py`, `src/nebula/observability/middleware.py`
- Modify: `src/nebula/services/retention_lifecycle_service.py` (`try` inside the tenant loop; `logger.exception("retention sweep failed", extra={"tenant_id": …})`, matching how the file logs today)
- Modify: `src/nebula/core/container.py:112`. Add `same_embedding_model(a: str, b: str) -> bool` (strips one trailing `:latest` from both), in the module that owns embedding settings, and use it for every embedding-model name comparison (`grep -rn "embedding_model" src/nebula`).
- Create: `tests/test_observability.py`
- Test: `tests/test_retention_lifecycle_service.py`, `tests/test_learned_routing.py`

- [ ] **Step 1: Failing tests**
  - `test_json_formatter_includes_traceback`: `LogRecord` with `exc_info` from a raised `ValueError("boom")` → parsed JSON `exc_info` contains `"ValueError: boom"` and `"Traceback"`.
  - `test_json_formatter_includes_stack_info`.
  - `test_metrics_path_label_uses_route_template`: GET two different tenant ids on the admin tenant route → `REQUEST_COUNT` has a sample with `path == "/v1/admin/tenants/{tenant_id}"` and none with either raw id.
  - `test_metrics_path_label_unmatched`: GET `/nope/123` → sample `path == "unmatched"`.
  - `test_retention_sweep_continues_after_one_tenant_fails`: two tenants, the first one's purge raises → the second is purged and caplog has the first's tenant id.
  - `test_learned_router_accepts_latest_tag`: parametrize `NEBULA_EMBEDDING_MODEL` over `"nomic-embed-text"` and `"nomic-embed-text:latest"` → `learned is not None`.
  - `test_same_embedding_model`: `("a", "a:latest") → True`, `("a:v1.5", "a") → False`.
- [ ] **Step 2: Run them.** Expected: they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the full backend suite and ruff.** Expected: green.
- [ ] **Step 5: Commit** `fix: tracebacks in JSON logs, route-template metric paths, per-tenant retention, :latest embedding names` (or split into two commits by area).

### Task 7: cache re-init in the background (PR 2 deferred)

**Files:**
- Modify: `src/nebula/services/semantic_cache_service.py` (`_retry_initialize` schedules `asyncio.create_task(self.initialize())` into `self._init_task` when none is running and the 30 s throttle allows; it never awaits it; `close()` cancels and awaits a pending task)
- Test: `tests/test_semantic_cache_service.py` (update the tests at `:503-580` that assert inline recovery)

- [ ] **Step 1: Failing tests**
  - `test_lookup_while_down_schedules_one_background_init`: LateQdrant down. Three concurrent `lookup` calls → each returns the disabled/miss result, and `initialize` was started once.
  - `test_background_init_recovers_for_the_next_request`: let the task finish (`await service._init_task`). The next `lookup` uses the cache.
  - `test_lookup_does_not_wait_for_a_slow_init`: initialize blocks on an `asyncio.Event`. `lookup` returns before the event is set (use `asyncio.wait_for(..., 0.1)`).
  - `test_close_cancels_pending_init`.
  - Health: `health_status` while the task runs reports the current (degraded) state without awaiting.
- [ ] **Step 2: Run them.** Expected: they fail.
- [ ] **Step 3: Implement.** Keep the throttle semantics (FakeClock) the existing tests use.
- [ ] **Step 4: Run the full backend suite and ruff.** Expected: green.
- [ ] **Step 5: Commit** `fix: re-initialize the semantic cache in the background`.

### Task 8: console deferred minors (labels, hook guard, fallback note)

**Files:**
- Modify: `console/src/components/system/labels.ts` (`LANGUAGES`, `languageLabel(code: string): string` via the existing `lookup`), `console/src/app/(console)/evaluacion/page.tsx` (use it; delete `LANG_LABELS`)
- Modify: `console/src/components/recommendations/recommendations.tsx:47-49` (`routing_mode_default` → `routingModeLabel(value)`)
- Modify: `console/src/hooks/use-tenant-target.ts:100-108` (the returned `apply` has no `mutateAsync`)
- Modify: `console/src/components/ledger/ledger-request-detail.tsx:220` (`routeTier={rowTier(entry)}`), `console/src/components/playground/playground-decision.tsx` (for a learned decision with `fallback` set and a `routeTier`, the badge shows `routeTier`; `note` is the exact fallback copy from Global Constraints with `tierLabel(routeTier)` and `tierLabel(computed)`; the path keeps `computed`)
- Test: `labels.test.ts`, `recommendations.test.tsx`, `use-tenant-target.test.tsx`, `playground-decision.test.tsx`, `ledger-request-detail.test.tsx`

- [ ] **Step 1: Failing tests**
  - `languageLabel("es") === <the Spanish label page.tsx uses today>`, same for every key in today's `LANG_LABELS`; an unknown code returns the code.
  - Recommendations: an evidence item `{label: "routing_mode_default", value: "auto"}` renders "Automático".
  - `useTenantTarget`: `"mutateAsync" in result.current.apply === false`.
  - `playground-decision.test.tsx:191`: fix the fixture to `signals.tier: "local"` with `fallback` set and `routeTier="economy"`. The badge reads `economy` and the text `Se sirvió con economy por un fallback; el router había elegido local.` is present. A non-fallback learned row with `routeTier` keeps today's badge and has no note.
  - The ledger detail fallback row passes the served tier (assert the badge in the detail).
- [ ] **Step 2: Run them** (`cd console && darwin-throttle npm test -- --run --maxWorkers=2 <files>`). Expected: they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Full console suite, `npx tsc --noEmit -p tsconfig.json`, eslint.** Expected: green.
- [ ] **Step 5: Commit** `fix: console labels for language and routing mode, guarded apply, served tier on fallback rows`.

### Task 9: policy decision source in the simulation

**Files:**
- Modify: `src/nebula/models/governance.py:197` (Literal gains `"policy"`), `:219-220` (`policy_rows: int = 0`)
- Modify: `src/nebula/services/policy_simulation_service.py:124,153-173`. A row whose evaluated `route_decision.reason` is in `{"explicit_local_model", "explicit_premium_model", "policy_local_only", "policy_premium_only", "calibrated_routing_disabled"}` counts as `policy`, not `heuristic`. Learned stays learned.
- Modify: `console/src/lib/admin-api.ts:103,119-120` (`"policy"` in `SimulationDecisionSource`, `policy_rows?: number`), `console/src/components/policy/policy-form.tsx` `DecisionSources` (append the exact clause from Global Constraints only when `policy_rows > 0`)
- Test: `tests/test_policy_simulation_learned.py`, `console/src/components/policy/policy-form.test.tsx`

- [ ] **Step 1: Check figure 10.3's data.** Find how PR 3 seeded the capture (`grep -rn "politica-simulada\|seed" scripts/ docs/design/2026-10-22-console-coherence/`). Confirm no seeded row has an explicit model, local_only/premium_only routing or calibrated routing off. Write the finding in your report. If any does, STOP and report BLOCKED.
- [ ] **Step 2: Failing tests**
  - Backend: a draft with `routing_mode_default="local_only"` over 3 rows → `policy_rows == 3`, `heuristic_rows == 0`, `learned_router_rows == 0`. A draft with calibrated routing off counts as policy too. An explicit-model row under auto counts as policy. Learned + heuristic + policy + cache equals `evaluated_rows`.
  - Console: `policy_rows: 4` renders `… con la heurística · 4 por la política`. `policy_rows: 0` or absent renders today's exact text.
- [ ] **Step 3: Run them.** Expected: they fail.
- [ ] **Step 4: Implement.**
- [ ] **Step 5: Full backend suite + ruff, full console suite + tsc + eslint.** Expected: green.
- [ ] **Step 6: Commit** `feat: count policy-decided rows separately in the policy simulation`.

### Task 10: console test hygiene

**Files:**
- Create: `console/src/test/tenants.ts` (`export const TENANT_A: Tenant`, with the fields the current copies share; check each copy and keep per-test overrides via spread)
- Modify: `app/(console)/tenants/page.test.tsx:29`, `components/tenants/tenant-editor-drawer.test.tsx:8,24`, `api-keys/page.test.tsx:75`, `layout.test.tsx:75`, `create-api-key-dialog.test.tsx:10`, `policy-page.test.tsx:37` (import it)
- Modify: `console/src/app/api/admin/[...path]/route.test.ts` (assert `fetchMock.mock.calls[0][1]` method, body, `X-Nebula-Admin-Key`; a hop-by-hop header like `connection` sent by the client is absent from the forwarded headers)
- Modify: `console/src/components/api-keys/create-api-key-dialog.tsx:93,101` (ids from `useId`, labels keep `htmlFor`)
- Test: `create-api-key-dialog.test.tsx` (`renders two dialogs with distinct input ids`: render two, and all `id` attributes in the document are unique)

- [ ] **Step 1: Failing test:** the two-dialog uniqueness test (red on today's hard-coded ids). The proxy assertions should pass on today's code. If one fails, that is a real bug: report it.
- [ ] **Step 2: Implement** the ids and the fixture move.
- [ ] **Step 3: Full console suite, tsc, eslint.** Expected: green, with the same test count plus the new tests.
- [ ] **Step 4: Commit** `test: shared tenant fixture, proxy forwarding assertions, unique dialog ids`.
