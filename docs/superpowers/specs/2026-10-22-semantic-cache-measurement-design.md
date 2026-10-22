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

When the only reason to deny a request is a spend guardrail (hard budget with `deny`, or with
`downgrade` when the request cannot be downgraded (explicit premium model or premium_only), or the
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

`benchmarks/cache/v1/preregistration.md` fixes, before computing any precision (condensed from
that file):

- **Definitions:**
  - A *hit* at threshold t: the best cache candidate has cosine ≥ t.
  - Production embedding: Ollama `nomic-embed-text` (digest `0a109f422b47`), no prefix,
    unit-normalized.
  - (a) PAWS-X `es` test: the 1999 valid human-translated pairs of the PAWS-X `es` test split
    (2000 rows minus one `NS` placeholder row; source, checksums and cleaning are in the
    data-acquisition amendment below and in `benchmarks/cache/v1/pawsx/LICENSE.md`).
    Label 1 = paraphrase. Prediction = cosine(sentence1, sentence2) ≥ t; a hit in (a) is a
    positive prediction (TP + FP). Precision = TP / (TP + FP); recall = TP / (TP + FN).
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
  - If it does not pass at 0.90 (including when 0.90 is not eligible): report it as a result.
    The recommended t is the smallest eligible t on the grid with both precisions ≥ 0.95; report
    PAWS-X recall and replay recall there. The criterion does not move.
  - If no eligible t reaches 0.95 on both: report "no safe threshold on the grid" and recommend
    the eligible t with the highest min(precision_a, precision_c); among ties, the smallest t.
  - If no grid point is eligible, the verdict is "not measurable with these data", the product
    default stays 0.90, and the report says so.
  - Comparisons (against 0.95, the minimum, ties) use unrounded values.
  - Consequence: on a pass the product default stays 0.90; when a t is recommended, the product
    default becomes that t (new tenants only; stored tenant policies keep their value).
  - The 40-item human paraphrase sample and the neighbor labels (b) are reported and never
    adjust the verdict.
- **Declared beforehand:** the corpus neighbors (b) were inspected during design: 20 pairs of
  distinct Spanish prompts at cosine ≥ 0.90, mostly false hits (the first version said 22, a count
  that included the English subset; see the amendment below). These 20 pairs are part of the (b)
  set (cosine ≥ 0.85) and were seen non-blind; one of them is the near-identical MBPP pair
  (`es:code-0113` vs `es:code-0138`, cosine 1.0). The neighbors are therefore descriptive only and
  do not enter the verdict. The same pairs are corpus originals, so in (c) they also appear as
  leave-one-out false hits by rule (including `es:code-0113` vs `es:code-0138`, which is
  semantically a correct hit). The author saw them before fixing this criterion, which makes a
  fail of (c) at 0.90 likely and known in advance; the criterion was kept because a cache that
  serves a different question's answer at 0.90 is exactly what it must reject.
- **Sensitivity model:** `nomic-embed-text` v1.5 is an English model; `nomic-embed-text-v2-moe`
  (multilingual) is measured as sensitivity only and does not enter the verdict.
- **Computed by:** `make cache-eval`, which writes the verdict to
  `benchmarks/cache/v1/report.json` (key `preregistration`).
- **Amendment (data acquisition, 2026-10-22, before any precision was computed):**
  1. *Source of (a).* The official archive `https://storage.googleapis.com/paws/pawsx/x-final.tar.gz`
     answered HTTP 403 to every anonymous request, so the archive and its SHA-256 are not
     available. The `es` test split (2000 rows) was taken from the Hugging Face dataset
     `google-research-datasets/paws-x` (same publisher, revision
     `4cd8187c404bda33cb1f62b49b001115862acf37`) and checked row for row against its parquet file
     `es/test-00000-of-00001.parquet`, SHA-256
     `5ba872e113a79c783616e59d3d28ec0e922b6db745d797e5eb95010a32928bee`. Byte identity with
     `x-final/es/test_2k.tsv` could not be verified.
  2. *Size of (a).* 1999 valid pairs, not 2000: one `NS` placeholder row (id 5815, label 0) is
     dropped, as the dataset README instructs.
  3. *Declared prior inspection, corrected.* At cosine ≥ 0.90 there are 20 pairs of distinct
     Spanish prompts (22 counting the 250-prompt English subset; the two extra pairs are
     `en:code-0021` vs `en:code-0046` at 0.946 and `en:summarisation-0050` vs
     `es:summarisation-0050` at 0.906). The (b) set at ≥ 0.85 has 265 Spanish pairs. The
     leave-one-out disclosure stands as written: it refers to the Spanish pairs.

  None of these changes touches the criterion, the threshold, the grid, the eligibility rule or
  the verdict rule. Condensed from the end of `benchmarks/cache/v1/preregistration.md`.
- **Amendment (paraphrase validity, 2026-10-22, before any hit, precision or recall was
  computed):** the first generation put the instruction and the prompt in one message and
  `qwen2.5:7b` answered instead of rewriting in some cases (27 of 200 under 30 % of the
  original's length; only lengths were inspected). Paraphrases are regenerated with the
  instruction as the system message and the prompt as the user message. A paraphrase is valid
  when its length is between 0.5 and 2.0 times the original's (characters); invalid ones are
  dropped and counted. (c) uses only valid paraphrases: recall = correct hits / valid
  paraphrases. The 40-item human sample is drawn from valid paraphrases. If fewer than 150 are
  valid, the report says so. The criterion, threshold, grid, eligibility and verdict rule are
  unchanged. Condensed from the end of `benchmarks/cache/v1/preregistration.md`.

### Data sets

- **(a) PAWS-X `es` test**: 1999 valid human-translated, human-labeled pairs (label 1 = paraphrase;
  the 2000-row split minus one `NS` placeholder row).
  Adversarial word-swap Wikipedia sentences, so it stresses false hits. Committed as
  `pawsx/pairs.jsonl` with both models' cosines and the dataset's license notice.
- **(b) Corpus neighbors**: every pair of distinct prompts among the 1000 Spanish corpus prompts
  with cosine ≥ 0.85 (production embedding; 265 pairs), committed as `neighbors/pairs.jsonl`.
  Joaquín labels them ("¿una respuesta a A sirve para B?"); labels go to
  `neighbors/labels/human-es-1.jsonl`. The 20 pairs at cosine ≥ 0.90 were seen by the author
  during design (non-blind); the remaining pairs are labeled blind. Descriptive only.
- **(c) Paraphrases**: 200 corpus prompts stratified by task (40 per task, seed `20261022`),
  each rewritten once by local `qwen2.5:7b` (temperature 0, fixed seed) with the instruction
  "Reescribe la siguiente consulta con otras palabras, sin cambiar lo que pide ni agregar
  información. Devuelve solo la consulta reescrita." Only valid rewrites are kept (length 0.5 to
  2.0 times the original's, per the paraphrase-validity amendment above), so (c) has the valid
  count, not 200 (173 valid): committed as `paraphrases/paraphrases.jsonl`, the dropped ones with
  their reason as `paraphrases/dropped.jsonl`. A blind random sample of 40 valid ones goes to
  Joaquín ("¿B pide lo mismo que A?") in `paraphrases/sample.jsonl`; labels to `paraphrases/labels/human-es-1.jsonl`. The sample
  validates the assumption "paraphrase ⇒ the cached answer serves".
- A labeling CLI (`python -m scripts.cache_eval.label {neighbors|paraphrases}`, `make cache-label`)
  shows one pair at a time, blind (no cosine, no tier), resumable, writing one JSONL row per answer
  (`sí` / `no` / `?`). It does not reuse the frozen `scripts/metric_validation/` labeler.

### Measures

- **PAWS-X curve:** precision, recall and F0.5 of "cosine ≥ t" vs the human label, t = 0.80…0.99.
- **Paraphrase replay:** the real `SemanticCacheService` over an in-memory Qdrant holds the 1000
  Spanish originals (each with its router tier at target 0.95 and its answer at that tier). Queries:
  the valid paraphrases (173 of 200, per the paraphrase-validity amendment above; a correct hit is
  the paraphrase's own original) and the 1000 originals leave-one-out (any hit is a false hit).
  Precision = correct hits / hits; recall = correct paraphrase hits / valid paraphrases. The
  verdict-precision pass runs with the tier rule off (similarity only);
  the savings replay runs with the tier rule on and counts tier-aware blocks.
- **Savings vs repetition rate:** a deterministic trace of 1000 requests per repetition rate
  r ∈ {0, 0.05, …, 0.40} with exactly round(r·1000) repeats of earlier prompts at seeded
  positions, nested across rates (the repeats of a lower rate are among those of a higher one),
  half exact repeats and half paraphrases from (c), replayed through the same service at the
  pre-registered default 0.90 and at the recommended threshold.
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

If the verdict at 0.90 does not pass and a t is recommended (a fail with a recommended t, or no
safe threshold), the default `semantic_cache_similarity_threshold` for new tenants becomes the
recommended t (pydantic default; `scripts/demo_prepare.py` policy; docs); with no safe threshold
the docs say that the recommended t does not meet 0.95. A pass, or "not measurable", leaves the
default at 0.90. Stored tenant policies keep their value (no migration).

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
