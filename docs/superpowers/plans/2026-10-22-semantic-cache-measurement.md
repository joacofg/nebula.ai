# Semantic cache measurement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the semantic cache tier-aware and context-keyed, record its avoided cost, and measure offline when it hits correctly and how much it adds to the router's saving, then write that into the thesis.

**Architecture:** Gateway changes stay inside `SemanticCacheService` (entry identity, filters, robustness) and `ChatService` (one vector per request, chosen tier passed to the cache, cache before spend denials). The measurement lives in a new `scripts/cache_eval/` package that drives the real `SemanticCacheService` over an in-memory Qdrant, writes versioned reports to `benchmarks/cache/v1/`, and feeds new GEN blocks in the thesis.

**Tech Stack:** Python 3.12, FastAPI, qdrant-client (local `:memory:` mode for tests and replay), Ollama (nomic-embed-text, nomic-embed-text-v2-moe, qwen2.5:7b), pytest; Next.js/vitest for one console value.

**Spec:** `docs/superpowers/specs/2026-10-22-semantic-cache-measurement-design.md`

## Global Constraints

- **No paid API calls.** Never start a gateway with a real premium key, never call OpenRouter. Ollama (local) and public dataset downloads only.
- RAM rules: every test run goes through `darwin-throttle` (`~/.local/bin`): `darwin-throttle .venv/bin/pytest <files> -q`; console `darwin-throttle npm --prefix console test -- --run <files> --maxWorkers=2`. Long Ollama jobs (embedding thousands of sentences, generating paraphrases) also run under `darwin-throttle`. Never two suites at once. Never edit test-runner configs.
- Git: a hook blocks plain `git` in the worktree; use `/opt/homebrew/bin/git -C <worktree>`. Stage only your files; never `.superpowers/`, never `artifacts/`.
- Allowed commit prefixes: fix, feat, docs, chore, test. Every commit ends with exactly:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_012JwPQqsnEebt9XQ2BG378E`.
- Every behavior lands red first (`mattpocock-skills:tdd`).
- Repo text in English; thesis and console copy in Spanish (neutral, no voseo in the console; the thesis keeps Joaquín's voice per its existing chapters). Never invent a number in the thesis: every figure comes from a GEN block or a committed report.
- Do not touch `scripts/metric_validation/`, `docs/evaluation.md`, `scripts/ground_truth/label.py`, or the frozen ground-truth files under `benchmarks/ground-truth/v1/`.
- Tier rank: local = 0, economy = 1, frontier = 2 (one constant, defined once).
- Downloaded archives go into their own new empty directory under `artifacts/cache-eval/downloads/`; scripts read them by path; Python that reads them runs with `-I`.

## Review Focus

- A conversation with a system prompt and the same last user message as another conversation without it must miss — Task 2.
- A request routed to economy may receive a frontier answer, but a frontier-routed request must never receive an economy or local answer — Task 2.
- A tenant over its hard budget with a cached answer gets the cached answer; the same tenant with a cache miss gets exactly the old 403, headers and one `policy_denied` row — Task 4.
- The replay must use the gateway's own lookup code, not a re-implementation, or the measurement does not describe the product — Task 8 asserts it imports `SemanticCacheService`.
- With no human label files present, `make cache-eval` and `make thesis-tables --check` still succeed and print "pendiente" for those sections — Tasks 8 and 10.

---

### Task 1: Pre-registration and ADR

**Files:**
- Create: `benchmarks/cache/v1/preregistration.md` (English; criterion, fallback rule, declared prior inspection, sensitivity model — verbatim content of the spec's "Pre-registration" section, dated 2026-10-22)
- Create: `docs/adr/0001-tier-aware-semantic-cache.md` (ADR format: 1–3 sentence context/decision/why; Considered Options: "any similar entry serves" rejected; Consequences: lower hit rate, cold start after upgrade)

- [ ] **Step 1:** Write both files.
- [ ] **Step 2: Commit** `docs: pre-register the cache measurement and record the tier-aware cache decision` — this commit must precede every commit that computes a precision.

### Task 2: Cache entry identity and tier-aware lookup

**Files:**
- Modify: `src/nebula/services/semantic_cache_service.py`
- Modify: `src/nebula/services/chat_service.py` (both paths: compute one vector, pass chosen tier / explicit model and context to lookup and store)
- Modify: `src/nebula/core/container.py` only if needed to inject a client
- Test: `tests/test_semantic_cache_service.py`, `tests/test_chat_completions.py` (or a new `tests/test_cache_identity.py`)

**Interfaces:**
- Produces: `TIER_RANK: dict[str, int] = {"local": 0, "economy": 1, "frontier": 2}` in `semantic_cache_service.py`.
- Produces: `def context_hash(messages: list[ChatMessage]) -> str` (SHA-256 hex of canonical JSON of every message except the latest user message; roles + contents in order).
- Produces: `SemanticCacheService.__init__(settings, embeddings_service, client: AsyncQdrantClient | None = None)` — tests and the replay pass `AsyncQdrantClient(location=":memory:")`.
- Produces: `lookup(prompt, *, tenant_id, similarity_threshold, max_entry_age_hours, context_hash, min_tier_rank: int | None, model: str | None, vector=None) -> CacheHit | None` — exactly one of `min_tier_rank` (auto requests) or `model` (explicit-model requests) is set.
- Produces: `store(response, *, tenant_id, vector, context_hash, tier_rank: int, model: str) -> None` — payload `{tenant_id, context_hash, tier_rank, model, response, created_at}`, no `prompt`.
- Produces: `initialize()` creates indexes for `tenant_id`, `created_at`, `context_hash`, `tier_rank`, `model` and deletes points where `tier_rank` is empty.
- `ChatService` computes the embedding once per request (`_embed_for_routing` result when available, else one embed) and passes it to both lookup and store; the chosen tier is the route tier the request will be served on.

- [ ] **Step 1: Write the failing tests** (in-memory Qdrant, stub embeddings returning fixed vectors):
  - `test_lookup_requires_same_context_hash`: store with context of `[system:"Eres X", user:"hola"]`, look up `[user:"hola"]` → miss; same context → hit.
  - `test_frontier_request_never_gets_lower_tier_answer`: store tier_rank 0 → lookup with `min_tier_rank=2` misses; store tier_rank 2 → lookup with `min_tier_rank=1` hits.
  - `test_explicit_model_matches_only_same_model`.
  - `test_store_payload_has_no_raw_prompt`.
  - `test_initialize_purges_points_without_tier_rank`.
  - `test_chat_embeds_once_per_request_with_router_off` (embeddings stub call count == 1 for a miss + store).
  - `test_two_conversations_same_last_message_do_not_share_answers` (HTTP, `configured_app()` with a real in-memory cache).
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3: Implement.** Keep existing tenant/TTL tests green (adapt their calls to the new signature).
- [ ] **Step 4:** Run the cache, chat, streaming and outage test files — PASS.
- [ ] **Step 5: Commit** `feat(cache): key entries by conversation context and serve only to tiers they satisfy`.

### Task 3: Avoided cost on cache hits

**Files:**
- Modify: `src/nebula/services/chat_service.py` (cache-hit metadata), `src/nebula/services/recommendation_service.py`
- Modify: `console/src/components/observability/cache-summary.tsx` (avoided cost with 4 decimals)
- Test: `tests/test_chat_completions.py` or `tests/test_cache_identity.py`, `tests/test_governance_api.py` (recommendations), the cache-summary vitest file

**Interfaces:**
- Produces: route signal `cache_avoided_cost_usd: float` on cache-hit rows = `PolicyService.estimate_cost(<chosen tier model>, estimated usage)` (0.0 for local); `estimated_cost` stays 0.0.
- `RecommendationService` sums `route_signals["cache_avoided_cost_usd"]` over cache-hit rows into `avoided_premium_cost_usd`.

- [ ] **Step 1: Failing tests:** a frontier-tier hit records `cache_avoided_cost_usd > 0` and `estimated_cost == 0`; `tenant_spend_total` unchanged by the hit; recommendations report the sum; the console renders `USD 0.0123`-style four decimals for `0.012345`.
- [ ] **Step 2:** Run — FAIL. **Step 3:** Implement. **Step 4:** Run — PASS.
- [ ] **Step 5: Commit** `feat(cache): record the cost each cache hit avoided`.

### Task 4: Cache before spend denials

**Files:**
- Modify: `src/nebula/services/policy_service.py` (resolution carries a deferred spend denial), `src/nebula/services/chat_service.py` (lookup before raising it)
- Test: `tests/test_cache_identity.py` (or a new `tests/test_cache_spend_order.py`)

**Interfaces:**
- Produces: `PolicyResolution.spend_denial: SpendDenial | None` where `SpendDenial` is a frozen dataclass `(detail: str, headers: dict[str, str], policy_outcome: str, route_reason: str)`; `PolicyService.resolve()` returns it instead of raising **only** for the hard-budget-deny and per-request-cap denials; every other denial raises as today.
- `ChatService`: if `spend_denial` is set → cache lookup → hit served normally; miss → record the same `policy_denied` row the current 403 path records and raise the same 403 with the same headers.

- [ ] **Step 1: Failing tests** (both stream and non-stream): hard budget exhausted + cached answer → 200 from cache, one `cache_hit` row; hard budget exhausted + miss → 403, identical detail/headers to `main`, one `policy_denied` row; per-request cap exceeded + hit → 200; `local_only` + explicit premium model → still 403 before any cache lookup (cache stub records zero lookups).
- [ ] **Step 2:** Run — FAIL. **Step 3:** Implement. **Step 4:** Run with `tests/test_governance_api.py tests/test_fallback_guardrails.py tests/test_error_contract.py` — PASS.
- [ ] **Step 5: Commit** `feat(cache): serve cached answers before spend guardrails deny`.

### Task 5: Cache robustness

**Files:**
- Modify: `src/nebula/services/semantic_cache_service.py`, `src/nebula/services/embeddings_service.py` (per-call timeout), `src/nebula/services/chat_service.py` (5 s on request-path embeds), `src/nebula/core/container.py` (artifact vs settings check), `src/nebula/services/retention_lifecycle_service.py` (expired-point sweep), `src/nebula/observability/metrics.py` only if label docs live there
- Test: `tests/test_semantic_cache_service.py`, `tests/test_learned_routing.py`, `tests/test_retention_lifecycle_service.py`, `tests/test_phase10_outage_safety.py`

**Interfaces:**
- `SemanticCacheService`: when `enabled` is False, `lookup`/`store` call `initialize()` at most once per 30 s (clock injectable); `health_status()` reports `degraded` when not enabled even if the collection exists; an existing collection with a different vector size leaves it disabled with reason `"Qdrant collection vector size N does not match embedding_dimensions M."`.
- `CACHE_LOOKUPS` results: `hit`, `no_candidate`, `below_threshold`, `disabled`, `embedding_unavailable`, `error` (query top-1 without `score_threshold` and compare in Python).
- `OllamaEmbeddingsService.embed(text, *, timeout: float | None = None)`; request-path callers pass `5.0`.
- Container: artifact `embedding_model` ≠ `settings.embedding_model` → learned router disabled, ERROR log naming both.
- `RetentionLifecycleService` deletes, per tenant, cache points with `created_at < now - max_entry_age_hours*3600`.

- [ ] **Step 1: Failing tests** for each bullet (fake clock for the retry; in-memory Qdrant with a 3-dim collection for the size mismatch; metric counter values for the two miss kinds; a stub embed that sleeps to prove the timeout is passed).
- [ ] **Step 2:** Run — FAIL. **Step 3:** Implement. **Step 4:** Run the touched files — PASS.
- [ ] **Step 5: Commit** `fix(cache): recover from a late Qdrant, bound request-path embeds, tell miss kinds apart`.

### Task 6: Evaluation data — PAWS-X and corpus neighbors

**Files:**
- Create: `scripts/cache_eval/__init__.py`, `scripts/cache_eval/embed.py` (Ollama embed with on-disk cache under `artifacts/cache-eval/vectors/<model>.json`, keyed by text SHA-256), `scripts/cache_eval/pawsx.py`, `scripts/cache_eval/neighbors.py`
- Create: `benchmarks/cache/v1/pawsx/pairs.jsonl` (`id, sentence1, sentence2, label, cos_nomic_v1, cos_nomic_v2`), `benchmarks/cache/v1/pawsx/LICENSE.md` (dataset citation + license notice), `benchmarks/cache/v1/neighbors/pairs.jsonl` (`pair_id, a_id, b_id, a, b, cos_nomic_v1`)
- Modify: `Makefile` (`cache-data` target), `.gitignore` only if `artifacts/cache-eval/` is not already covered
- Test: create `tests/test_cache_eval.py` (pure functions only: pair parsing, cosine, neighbor extraction on tiny fixtures)

**Interfaces:**
- `embed.embed_texts(texts: list[str], *, model: str) -> list[list[float]]` (unit-normalized, cached).
- `pawsx.load_pairs(tsv_path: Path) -> list[PawsPair]`; `neighbors.find_pairs(vectors: dict[str, list[float]], *, min_cos: float) -> list[NeighborPair]` (distinct ids, i<j, sorted by cosine desc).
- Neighbors use the production vectors: copy `artifacts/router-embeddings/none.json` from the main checkout (`/Users/joaquinfernandezdegamboa/Proj/nebula/artifacts/router-embeddings/none.json`) or regenerate with `python -m scripts.router.embed`; only the 1000 `es:` keys; `min_cos=0.85`.
- PAWS-X source: the official `x-final.tar.gz` from the PAWS repo (Google storage link in `github.com/google-research-datasets/paws`), file `es/test_2k.tsv`; record the URL and SHA-256 of the archive in `LICENSE.md`.
- `ollama pull nomic-embed-text-v2-moe` before embedding; v2 vectors also with no prefix.

- [ ] **Step 1: Failing unit tests** for parsing, cosine and neighbor extraction. **Step 2:** FAIL. **Step 3:** Implement. **Step 4:** PASS.
- [ ] **Step 5:** Run `darwin-throttle make cache-data`; check row counts (2000 PAWS-X pairs; neighbor count printed) — do not compute any precision here.
- [ ] **Step 6: Commit** `feat(cache-eval): PAWS-X and corpus-neighbor pairs with cosines`.

### Task 7: Paraphrases and the labeling CLI

**Files:**
- Create: `scripts/cache_eval/paraphrase.py`, `scripts/cache_eval/label.py`
- Create: `benchmarks/cache/v1/paraphrases/paraphrases.jsonl` (`prompt_id, task_type, original, paraphrase, model, seed, cos_nomic_v1, cos_nomic_v2`), `benchmarks/cache/v1/paraphrases/sample.jsonl` (40 blind pairs: `pair_id, a, b`)
- Modify: `Makefile` (`cache-paraphrases`, `cache-label`)
- Test: `tests/test_cache_eval.py` (stratified selection is deterministic; paraphrase cleanup strips quotes/prefixes; labeler appends rows, resumes, accepts only `s`/`n`/`?`)

**Interfaces:**
- `paraphrase.select_prompts(rows, *, per_task: int = 40, seed: int = 20261022) -> list[PromptRow]` over the 1000 ES corpus prompts (`benchmarks/ground-truth/v1/prompts.es.jsonl`).
- Generation: Ollama `qwen2.5:7b`, `/api/chat`, options `{temperature: 0, seed: 20261022}`, the spec's exact instruction; empty or identical outputs are retried once with seed+1, then dropped and logged.
- `label.main(["neighbors"|"paraphrases"])`: shows A and B only, asks the spec's question, writes `{pair_id, label: "sí"|"no"|"?", rater_id: "human-es-1", recorded_at}` to `<set>/labels/human-es-1.jsonl`, skips already-labeled ids.

- [ ] **Steps 1–4:** TDD the pure parts.
- [ ] **Step 5:** `darwin-throttle make cache-paraphrases` (≈200 local generations; run in the background if needed) and write the sample.
- [ ] **Step 6: Commit** `feat(cache-eval): local paraphrases and a blind labeling CLI`.

### Task 8: Replay and report

**Files:**
- Create: `scripts/cache_eval/replay.py`, `scripts/cache_eval/report.py`
- Create: `benchmarks/cache/v1/report.json`, `benchmarks/cache/v1/report.md`
- Modify: `Makefile` (`cache-eval`)
- Test: `tests/test_cache_eval.py`

**Interfaces:**
- `replay.build_cache(originals, *, model_key) -> SemanticCacheService` — uses `nebula.services.semantic_cache_service.SemanticCacheService` with `AsyncQdrantClient(location=":memory:")`, single tenant, empty context hash, each original stored with its router tier at target 0.95 (tiers computed with `nebula.services.learned_router` from `src/nebula/data/learned_router_v1.json` and the production vectors).
- `report.pawsx_curve(pairs, *, model_key, grid) -> list[{t, precision, recall, f05, hits}]`
- `replay.paraphrase_replay(cache, paraphrases, originals, *, t) -> {precision, recall, correct_hits, false_hits, tier_blocked}`
- `replay.savings_curve(..., rates, t, seed=20261022) -> list[{r, cost_per_1000, saving_vs_frontier, extra_saving_vs_router, quality, hit_rate, false_hit_rate}]` with costs from `router_replay_v1.json` and quality from `benchmarks/ground-truth/v1/tiers.jsonl`.
- `report.json` keys: `preregistration` (`verdict`, one of `pass` / `fail` / `no_safe_threshold` / `not_measurable`; `recommended_t`; both precisions and both recalls at 0.90 and at the recommended t; hit counts per set), `pawsx`, `paraphrases`, `neighbors` (counts by cosine band; human-label agreement or `"pendiente"`), `paraphrase_validation` (faithful rate or `"pendiente"`), `savings` (curve + the three cited rates), `models` (production + sensitivity), `provenance` (git sha, file sha256s).

- [ ] **Step 1: Failing tests:** precision/recall on a hand-made 6-pair fixture; the replay imports and uses `SemanticCacheService` (assert type); savings at r=0 equal the router-only cost per 1000 from `router_replay_v1.json` (1.70 ± 0.01 at target 0.95); missing label files yield `"pendiente"`; the verdict function returns each of `pass` / `fail` / `no_safe_threshold` / `not_measurable` on hand-made grids (eligibility needs >= 20 hits in both sets, ties go to the smallest t, comparisons use unrounded values).
- [ ] **Step 2:** FAIL. **Step 3:** Implement. **Step 4:** PASS.
- [ ] **Step 5:** `darwin-throttle make cache-eval`; commit the reports.
- [ ] **Step 6: Commit** `feat(cache-eval): measure cache precision and its saving over the router`.

### Task 9: Default threshold

**Files:** `src/nebula/models/governance.py` (`semantic_cache_similarity_threshold` default), `scripts/demo_prepare.py`, `docs/self-hosting.md`, tests asserting the default.

- [ ] **Step 1:** Read `report.json` `preregistration.verdict` and act on its four outcomes:
  - `pass` → no change; record that in the commit-less ledger note and skip.
  - `not_measurable` → no change; record that in the commit-less ledger note and skip.
  - `fail` (a recommended t exists) → write a failing test asserting the new default equals `recommended_t`, then change the default, the demo tenant policy and the doc line.
  - `no_safe_threshold` → same as `fail` (the default becomes `recommended_t`), and the doc line says the new default does not meet the 0.95 precision criterion.
- [ ] **Step 2:** Run the touched tests — PASS. **Step 3: Commit** `fix(cache): raise the default similarity threshold to the measured safe value` (only if changed).

### Task 10: Thesis

**Files:**
- Modify: `scripts/thesis/tables.py` (builders `cache_pawsx`, `cache_replay`, `cache_savings`, `cache_verdict` reading `benchmarks/cache/v1/report.json`), `tests/test_thesis_tables.py`
- Modify: `docs/tfc/tesis/11-implantacion.md` (new §11.2.x "Medición del caché" with the GEN blocks; new CP-18 row in Table 11.3 for the pre-registered criterion with P/F from the verdict; analysis paragraph in 11.2.4; threats in 11.2.5: English embedding model, synthetic paraphrases, single human rater), `06-resumen.md` (both languages, ≤ 300 words each), `12-conclusiones.md` (§12.2 hypothesis answer adds the cache saving as a function of repetition at the cited rates; limitation 2 reworded; future line 3 reworded; repeated-queries claim corrected), `14-anexos.md` (CP-18 test reference), `07-introduccion.md:157-159` claim
- Read first: `docs/tfc/tesis/README.md` conventions, and keep citations IEEE-numbered (renumber if a new reference is added; cite PAWS-X, MeanCache, LMSYS-Chat-1M, WildChat with full references in `13-bibliografia.md`).

- [ ] **Step 1:** Failing test: `python -m scripts.thesis.tables --check` fails until each new GEN block has a builder and a marker (existing test pattern).
- [ ] **Step 2:** Implement builders + markers; write the prose (Spanish, first person plural/impersonal as the chapters do; no invented figures — every number inside a GEN block or quoted from `report.md`).
- [ ] **Step 3:** `make thesis-tables` then `python -m scripts.thesis.tables --check` — up to date; `darwin-throttle .venv/bin/pytest tests/test_thesis_tables.py -q` — PASS; word count of each abstract ≤ 300.
- [ ] **Step 4: Commit** `docs(tesis): medición del caché y su aporte al ahorro`.

### Task 11: Full verification

- [ ] `darwin-throttle make test`, `make lint`, `darwin-throttle npm --prefix console test -- --run --maxWorkers=2`, `npx --prefix console tsc --noEmit -p console/tsconfig.json`, `npm --prefix console run lint`, `python -m scripts.thesis.tables --check` — all green, summary lines quoted.
