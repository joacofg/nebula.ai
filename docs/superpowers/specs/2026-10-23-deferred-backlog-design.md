# Deferred backlog (PR 4): backend B16–B20 and the PR 2 / PR 3 deferred minors

Date: 2026-10-23. Branch `fix/2026-10-23-deferred-backlog` from `origin/main` c78fbde.
Source inventory: the 2026-10-21 audits (IDs B16–B20), the PR #23 deferred list (cache) and the PR #24 deferred list (console).

## Why

PRs #22–#25 closed the guardrail, cache and console blocks. The audits also found smaller contract, performance and
observability gaps, deferred so they would not hold up those PRs. Before the February 2027 defense the
gateway should follow the OpenAI contract it claims, keep the event loop free, and log what it needs to debug a
failure. No paid API calls (premium runs use `NEBULA_PREMIUM_PROVIDER=mock`).

## Decisions

### B16 — OpenAI contract
- **finish_reason is passed through.** Non-stream responses return the provider's `finish_reason` instead of the model
  default `"stop"`. Ollama maps `done_reason == "length"` to `"length"`, anything else to `"stop"`. One normalizer
  maps a provider value into the response Literal (`stop | length | content_filter | tool_calls`):
  `function_call` → `tool_calls`, `None` or any unknown value (OpenRouter's `"error"`) → `"stop"`. It is applied
  wherever a chunk or response is built, so a value outside the Literal never raises mid-stream. Cache hits keep `"stop"`.
- **`n` > 1 is rejected** with the existing 422 shape (`n` is `ge=1, le=1`). Nebula returns one choice and does not
  forward `n`. Accepting `n=8` and returning one answer (or, when streaming, interleaving eight) is worse than a clear error.
- **Streaming premium cost uses the provider's usage.** The OpenAI-compatible provider sends
  `stream_options: {"include_usage": true}`. It reads usage from a usage-only chunk (`choices: []`) or from the finish
  chunk, and `CompletionChunk` carries an optional `usage`. The chat stream keeps reading after `finish_reason` until
  the provider closes, so the usage chunk is not lost, and the ledger records provider tokens and cost. It falls
  back to the chars/4 estimate only when the provider sends no usage, as today.

### B17 — no sync SQLAlchemy on the event loop
- Every sync governance-store call made while handling chat, embeddings or admin requests runs off the event loop
  (`run_in_threadpool`). Admin handlers that await nothing become plain `def`, which FastAPI already runs in its
  threadpool. Auth is already a sync dependency and stays as is.
- `PolicyService.evaluate` reads the tenant spend off the loop and hands it to `evaluate_decision` through a new
  `tenant_spend_total` parameter (B19 reuses it).
- **Exception: the ledger write in the streaming `finally` stays synchronous.** It runs while the generator may be
  closing after a client disconnect, where awaiting is unsafe. Losing that row would undercount the hard budget
  (B5). The cost is one SQLite insert of a few milliseconds per stream. The code comment there says this.
- SQLite connections already cross threads: auth runs in the threadpool today.

### B18 — outcome-evidence summary
- **Off the per-request path:** `PolicyService` memoizes `summarize_calibration_evidence` per tenant for
  `NEBULA_EVIDENCE_SUMMARY_TTL_SECONDS` (default 30, `0` disables), computed off the loop. The summary only adjusts
  the reported score (`outcome_bonus`, `evidence_penalty`) and never the chosen target, so a 30-second lag changes
  no route. Replay and override paths are unchanged.
- **Classification fix:** embeddings rows (`message_type == "embeddings"`) and rows with
  `terminal_status in {"policy_denied", "rate_limited"}` are excluded from the eligible set, not counted as
  `missing_route_signals`. They no longer flip a tenant to "degraded".

### B19 — simulation spend in one pass
- The simulation computes the spend before each replayed row from one query instead of one per row. The query
  selects the tenant's spend rows (timestamp, cost) before the latest replayed row, and a running total gives each
  row its value. The comparison is strict `<`, the same as `tenant_spend_total(before_timestamp=…)`. The prefix sum
  is exactly rounded (the `math.fsum` recipe), which is what SQLite's SUM returns for the per-row query. It reuses
  the spend-status list the store already defines.

### B20 — observability
- `JsonFormatter` adds `exc_info` (formatted traceback) and `stack_info` when present.
- The Prometheus `path` label is the matched route template (`/v1/admin/tenants/{tenant_id}`), or `"unmatched"`
  when no route matched, never the raw URL.

### PR 2 cache deferred
- **Re-init off the request path:** when the cache is down, a lookup, store or health check schedules one background
  `initialize()` (one in-flight task, the existing 30 s throttle) and answers as "disabled" without waiting.
  `close()` cancels the task.
- **Retention per tenant:** one tenant's purge failure is logged with its tenant id and the sweep continues.
- **Embedding model names:** `nomic-embed-text` and `nomic-embed-text:latest` are the same model wherever Nebula
  compares embedding model names (learned-router artifact check in `core/container.py`).

### PR 3 console deferred
- Recommendation evidence `routing_mode_default` shows through `routingModeLabel` ("Automático", not "auto").
- The Evaluación language labels move to `labels.ts` as `LANGUAGES` + `languageLabel()`.
- `useTenantTarget` does not expose an unguarded `apply.mutateAsync`. It is left out of the returned object (no caller uses it).
- **"Por qué este nivel" on a fallback row** shows the tier that served the request, not the router's choice, and
  says so in one line: `Se sirvió con {served} por un fallback; el router había elegido {chosen}.` (tier names via `tierLabel`).
- **Policy decision source in the simulation:** rows decided by the policy, not by a router, count as `policy`.
  Those are reasons `explicit_local_model`, `explicit_premium_model`, `policy_local_only`, `policy_premium_only`
  and `calibrated_routing_disabled`. The summary gains `policy_rows`. The console adds ` · N por la política` only
  when N > 0, so the wording in figure 10.3 is unchanged.
- **Test hygiene:** one shared `TENANT_A` fixture under `console/src/test/`; the admin proxy test asserts the
  forwarded method, body and `X-Nebula-Admin-Key`, and that hop-by-hop headers are stripped; two
  `CreateApiKeyDialog` instances get distinct input ids (`useId`).

## Dropped (with reason)
- **TIERS vs ROUTES casing ("Caché" / "caché"):** the split is deliberate (routes are sentence-case labels, tiers are
  the thesis terms; the comment in `labels.ts` says so). Either way of unifying changes figure 10.7's Ruta value or
  figure 11.1's tier badge.
- API-keys table scrolling at 1024–1060 px: a non-goal (the console is shown at 1280 and above).
- Recapturing the `after/` captures that show the degraded-cache card: they are a design record, not thesis figures.
- The native date placeholder "dd/mm/yyyy": the browser's control, locale-bound.
- Premium rows without signals under strict minimization: there is nothing to classify them by.

## Thesis figures
No change may alter what figures 10.3, 10.6, 10.7 or 11.1 show. If one would, stop and report or recapture
(Docker and Qdrant needed). The policy-source clause shows only when it is non-zero, and the fallback note only on
fallback rows. Neither appears in the captured data.

## Out of scope
- The cache labels (`make cache-label`): Joaquín does those himself.
- Deleting the outcome-evidence machinery (the "M" option of B18).
