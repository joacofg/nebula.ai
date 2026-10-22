# Semantic cache: tier-aware design and offline measurement — design

Date: 2026-10-22. Second of three PRs before the defense (backend → **semantic cache** → console).
Decisions come from the 2026-10-21 grill (round 2, items C1–C12 of the audit inventory).
Constraint: **no paid API calls**. Local Ollama models and public datasets only.

## Goal

1. Make the cache safe by construction: an answer is only reused for the same conversation
   context, by a request whose tier it satisfies, and its avoided cost is recorded.
2. Measure, offline, when the cache hits correctly and how much it adds to the router's saving,
   so the thesis no longer says "el aporte del caché no se pudo medir".

## Part A — gateway behavior

### Cache entry identity (C3, C4, C6)

A cache entry stores: tenant, embedding of the latest user message, `context_hash`,
`tier_rank`, `model`, `created_at`, `response`. It no longer stores the raw prompt.

- `context_hash` = SHA-256 of the canonical JSON of every message **except the latest user
  message** (roles and contents, in order). A single-turn request without a system prompt has
  the hash of an empty list. Lookups only match entries with the same `context_hash`.
- `tier_rank`: local = 0, economy = 1, frontier = 2 — the tier that produced the answer
  (`CompletionMetadata.route_tier` at store time).
- **Tier-aware rule**: for an `auto` request, a lookup only matches entries with
  `tier_rank >= rank(chosen tier)`. A request routed to frontier never receives a local answer.
- A request for an **explicit model** only matches entries whose `model` equals the served model
  of that request's route (no tier rule).
- Startup deletes points that lack `tier_rank` (written before this change; they could never
  match). Payload indexes: `tenant_id`, `created_at`, `context_hash`, `tier_rank`, `model`.
- The embedding for routing and caching is computed once per request and reused for lookup and
  store, also when the learned router is off.

### Avoided cost (C5)

On a cache hit the ledger row's `route_signals` gains `cache_avoided_cost_usd`: the estimated cost
of serving the request on its chosen tier (0 for local). `estimated_cost` of the hit stays 0, so
spend and the hard budget are unchanged. The recommendations' `avoided_premium_cost_usd` sums
`cache_avoided_cost_usd`. The console's cache summary shows it with four decimals. Under
`metadata_minimization_level=strict` route signals are suppressed and the hit contributes 0
(documented).

### Cache before spend guardrails (C9)

When the only reason to deny a request is a spend guardrail (hard budget with `deny`, or the
per-request premium cap), the gateway first looks the request up in the cache. A hit is served
(cost 0, normal cache-hit row). A miss gets the same 403, headers and `policy_denied` ledger row
as today. Every other denial (routing mode, explicit-model conflict, model allowlist) still
happens before the cache.

### Cache robustness (C7, C8, C10, C11)

- When the cache is disabled because initialization failed, lookups and stores retry
  initialization at most once every 30 s; health reports `degraded` while it is disabled.
- Request-path embeddings (routing/cache) time out after 5 s; `/v1/embeddings` keeps its timeout.
- At startup: a learned-router artifact whose `embedding_model` differs from
  `settings.embedding_model` disables the learned router with an ERROR log (heuristic routing
  keeps serving); an existing collection whose vector size differs from
  `settings.embedding_dimensions` disables the cache with that degraded reason.
- `nebula_cache_lookups_total{result}` distinguishes `no_candidate` (nothing passed the
  tenant/TTL/context/tier filters) from `below_threshold` (best candidate under the threshold);
  `hit`, `disabled`, `embedding_unavailable`, `error` stay.
- The retention lifecycle job deletes cache points older than their tenant's
  `semantic_cache_max_entry_age_hours`.

## Part B — offline measurement (`scripts/cache_eval/`, data in `benchmarks/cache/v1/`)

The cache is treated as a classifier of "this request was already answered".

### Pre-registration (committed before any measurement)

`benchmarks/cache/v1/preregistration.md` fixes, before computing any precision (same text as
that file):

- **Definitions:**
  - A *hit* at threshold t: the best cache candidate has cosine ≥ t.
  - Production embedding: Ollama `nomic-embed-text` (digest `0a109f422b47`), no prefix,
    unit-normalized.
  - (a) PAWS-X `es` test: the 2000 human-translated pairs of the official PAWS-X release
    (`es/test_2k.tsv` from `x-final.tar.gz`; the archive SHA-256 is recorded with the data).
    Label 1 = paraphrase. Prediction = cosine(sentence1, sentence2) ≥ t. Precision =
    TP / (TP + FP); recall = TP / (TP + FN).
  - (c) Paraphrase replay: the cache holds the 1000 Spanish corpus originals. Queries are the 200
    paraphrases (200 prompts stratified 40 per task, seed `20261022`, one `qwen2.5:7b` rewrite
    each, temperature 0, fixed seed) and the 1000 originals leave-one-out. A correct hit is a
    paraphrase whose best candidate is its own original; every other hit is a false hit,
    including any hit on a leave-one-out original. Precision = correct hits / all hits; recall =
    correct hits / 200. For the verdict the cache matches on similarity alone (single tenant,
    empty context, tier rule disabled); tier-aware blocks are reported separately in the savings
    replay.
  - Point estimates only; no confidence intervals are computed or reported (declared).
- **Criterion:** the cache is *safe at a threshold t* when precision ≥ **0.95** on both
  (a) and (c) at t, with the production embedding. The verdict is reported at the default
  **t = 0.90**.
- **Verdict rule:**
  - A grid point t (0.80–0.99, step 0.01) is eligible only if it has ≥ 20 hits in each of (a)
    and (c) (avoids 0/0 and tiny-sample precision). Only an eligible point can pass or be
    recommended.
  - Pass at 0.90 = both precisions ≥ 0.95 at t = 0.90.
  - If it fails at 0.90: report it as a result. The recommended t is the smallest eligible t on
    the grid with both precisions ≥ 0.95; report PAWS-X recall and replay recall there. The
    criterion does not move.
  - If no eligible t reaches 0.95 on both: report "no safe threshold on the grid" and recommend
    the eligible t with the highest min(precision_a, precision_c).
  - If no grid point is eligible, the verdict is "not measurable with these data", the product
    default stays 0.90, and the report says so.
  - Consequence: on a pass the product default stays 0.90; when a t is recommended, the product default
    becomes that t (new tenants only).
  - The 40-item human paraphrase sample and the neighbor labels (b) are reported and never
    adjust the verdict.
- **Declared beforehand:** the corpus neighbors (b) were inspected during design: 22 pairs of
  distinct Spanish prompts at cosine ≥ 0.90, mostly false hits. These 22 pairs are part of the (b)
  set (cosine ≥ 0.85) and were seen non-blind; one of them is the near-identical MBPP pair
  (`es:code-0113` vs `es:code-0138`, cosine 1.0). The neighbors are therefore descriptive only.
- **Sensitivity model:** `nomic-embed-text` v1.5 is an English model; `nomic-embed-text-v2-moe`
  (multilingual) is measured as sensitivity only and does not enter the verdict.
- **Computed by:** `make cache-eval`, which writes the verdict to
  `benchmarks/cache/v1/report.json` (key `preregistration`).

### Data sets

- **(a) PAWS-X `es` test**: 2000 human-translated, human-labeled pairs (label 1 = paraphrase).
  Adversarial word-swap Wikipedia sentences, so it stresses false hits. Committed as
  `pawsx/pairs.jsonl` with both models' cosines and the dataset's license notice.
- **(b) Corpus neighbors**: every pair of distinct prompts among the 1000 Spanish corpus prompts
  with cosine ≥ 0.85 (production embedding), committed as `neighbors/pairs.jsonl`. Joaquín labels
  them blind ("¿una respuesta a A sirve para B?"); labels go to `neighbors/labels/human-es-1.jsonl`.
  Descriptive only.
- **(c) Paraphrases**: 200 corpus prompts stratified by task (40 per task, seed `20261022`),
  each rewritten once by local `qwen2.5:7b` (temperature 0, fixed seed) with the instruction
  "Reescribe la siguiente consulta con otras palabras, sin cambiar lo que pide ni agregar
  información. Devuelve solo la consulta reescrita." Committed as `paraphrases/paraphrases.jsonl`.
  A blind random sample of 40 goes to Joaquín ("¿B pide lo mismo que A?") in
  `paraphrases/sample.jsonl`; labels to `paraphrases/labels/human-es-1.jsonl`. The sample
  validates the assumption "paraphrase ⇒ the cached answer serves".
- A labeling CLI (`python -m scripts.cache_eval.label {neighbors|paraphrases}`, `make cache-label`)
  shows one pair at a time, blind (no cosine, no tier), resumable, writing one JSONL row per answer
  (`sí` / `no` / `?`). It does not reuse the frozen `scripts/metric_validation/` labeler.

### Measures

- **PAWS-X curve:** precision, recall and F0.5 of "cosine ≥ t" vs the human label, t = 0.80…0.99.
- **Paraphrase replay:** the real `SemanticCacheService` over an in-memory Qdrant holds the 1000
  Spanish originals (each with its router tier at target 0.95 and its answer at that tier). Queries:
  the 200 paraphrases (a correct hit is the paraphrase's own original) and the 1000 originals
  leave-one-out (any hit is a false hit). Precision = correct hits / hits; recall = correct
  paraphrase hits / 200. Tier-aware blocks are counted separately.
- **Savings vs repetition rate:** a deterministic trace of 1000 requests per repetition rate
  r ∈ {0, 0.05, …, 0.40}, where each request is a repeat with probability r (half exact repeats,
  half paraphrases from (c)), replayed through the same service at the recommended threshold.
  Costs per tier from `src/nebula/data/router_replay_v1.json`; a correct hit costs 0 and keeps the
  quality of the cached answer (ground-truth substitutability of its tier); a false hit counts as
  quality 0. Report cost per 1000 requests, saving vs all-frontier and extra saving vs router-only,
  and quality, at r = 3.7 % (WildChat), 12.1 % (LMSYS exact duplicates) and 31 % (MeanCache), cited.
- Everything above for both embedding models; the verdict uses only the production one.

Outputs: `benchmarks/cache/v1/report.json` and `report.md`, regenerated by
`make cache-eval` (no network, no paid API; Ollama only for the embedding/generation steps, which
cache their vectors under `artifacts/cache-eval/`). Human-label sections read "pendiente" until the
label files exist.

### Threshold decision (C1)

If the verdict at 0.90 fails, the default `semantic_cache_similarity_threshold` for new tenants
becomes the recommended t (pydantic default; `scripts/demo_prepare.py` policy; docs). Stored
tenant policies keep their value (no migration).

## Part C — thesis and docs

- `docs/adr/0001-tier-aware-semantic-cache.md`: the tier-aware rule and context key, why
  (quality over hit rate), and the rejected alternative (any similar entry serves).
- Thesis (Spanish, Joaquín's voice, optimistic verdict without invented numbers): new
  §11.2.x "Medición del caché" with GEN blocks from `report.json`, a new CP row in Table 11.3 for
  the pre-registered criterion, and updates to the abstract (≤ 300 words), §12.2 (hypothesis:
  router saving plus cache saving as a function of repetition), limitation 2, future line 3,
  the threat that the embedding is an English model, and the corrected claim about repeated
  queries in the corpus (one near-identical pair).

## Out of scope

Console UX beyond the avoided-cost decimals (PR 3), changing the production embedding model,
online learning, re-labeling code answers.

## Deploy

One gateway release plus the console build. No migration. Existing Qdrant points are purged at
startup (they lack `tier_rank`), so the cache starts cold once.
