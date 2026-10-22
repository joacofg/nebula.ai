# Pre-registration: semantic cache measurement

Date: 2026-10-22. Fixed before computing any precision, recall or verdict: the commit of this file, its two amendments (`5bd4632` and `2f20e53`) and the final tightening commit `docs: tighten the cache pre-registration before measuring` precede every commit that computes one.

Design reference: `docs/superpowers/specs/2026-10-22-semantic-cache-measurement-design.md` (Part B) at spec commit `98015a0`, plus the amendments named above, which made the definitions exact and covered the edge cases. The spec's "Pre-registration" section carries the same text.

## Definitions

- **Hit** at threshold t: the best cache candidate has cosine >= t.
- **Production embedding**: Ollama `nomic-embed-text` (digest `0a109f422b47`), no prefix, unit-normalized.
- **(a) PAWS-X `es` test**: the 2000 human-translated pairs of the official PAWS-X release (`es/test_2k.tsv` from `x-final.tar.gz`; the archive SHA-256 is recorded with the data). Label 1 = paraphrase. Prediction = cosine(sentence1, sentence2) >= t; a hit in (a) is a positive prediction (TP + FP). Precision = TP / (TP + FP); recall = TP / (TP + FN).
- **(c) Paraphrase replay**: the cache holds the 1000 Spanish corpus originals. Queries are the 200 paraphrases (200 prompts stratified 40 per task, seed `20261022`, one `qwen2.5:7b` rewrite each, temperature 0, fixed seed) and the 1000 originals leave-one-out. A correct hit is a paraphrase whose best candidate is its own original; every other hit is a false hit, including any hit on a leave-one-out original. Precision = correct hits / all hits; recall = correct hits / 200. For the verdict the cache matches on similarity alone (single tenant, empty context, tier rule disabled); tier-aware blocks are reported separately in the savings replay.
- **Estimates**: point estimates only. No confidence intervals are computed or reported (declared here).

## Criterion

The cache is *safe at a threshold t* when precision >= **0.95** on both (a) and (c) at t, with the production embedding. The verdict is reported at the default **t = 0.90**.

## Verdict rule

- **Eligibility:** a grid point t (0.80-0.99, step 0.01) is eligible only if it has >= 20 hits in each of (a) and (c). This avoids 0/0 and tiny-sample precisions. Only an eligible point can pass or be recommended.
- **Pass at 0.90:** both precisions are >= 0.95 at t = 0.90.
- **If it does not pass at 0.90 (including when 0.90 is not eligible):** report it as a result. The recommended t is the smallest eligible t on the grid with both precisions >= 0.95; report PAWS-X recall and replay recall there. The criterion does not move.
- **If no eligible t reaches 0.95 on both:** report "no safe threshold on the grid" and recommend the eligible t with the highest min(precision_a, precision_c); among ties, the smallest t.
- **If no grid point is eligible:** the verdict is "not measurable with these data", the product default stays 0.90, and the report says so.
- **Comparisons** (against 0.95, the minimum, ties) use unrounded values.
- **Consequence:** on a pass the product default stays 0.90; when a t is recommended, the product default becomes that t (new tenants only; stored tenant policies keep their value).
- The 40-item human paraphrase sample and the neighbor labels (b) are reported and never adjust the verdict.

## Declared beforehand

The corpus neighbors (b) were inspected during design: 22 pairs of distinct Spanish prompts at cosine >= 0.90, mostly false hits. These 22 pairs are part of the (b) set (cosine >= 0.85) and were seen non-blind. One of them is the near-identical MBPP pair (`es:code-0113` vs `es:code-0138`, cosine 1.0). The neighbors are therefore descriptive only and do not enter the verdict.

The same pairs are corpus originals, so in (c) they also appear as leave-one-out false hits by rule (including `es:code-0113` vs `es:code-0138`, which is semantically a correct hit). The author saw them before fixing this criterion, which makes a fail of (c) at 0.90 likely and known in advance; the criterion was kept because a cache that serves a different question's answer at 0.90 is exactly what it must reject.

## Sensitivity model

`nomic-embed-text` v1.5 is an English model. `nomic-embed-text-v2-moe` (multilingual) is measured as sensitivity only and does not enter the verdict.

## How the verdict is computed

Computed by `make cache-eval`, which writes the verdict to `benchmarks/cache/v1/report.json` (key `preregistration`).
