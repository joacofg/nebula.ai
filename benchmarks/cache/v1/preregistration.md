# Pre-registration: semantic cache measurement

Date: 2026-10-22. Fixed before computing any precision, recall or verdict: the commit of this file, and of its amendment below, precedes every commit that computes one.

Design reference: `docs/superpowers/specs/2026-10-22-semantic-cache-measurement-design.md` (Part B) at spec commit `98015a0`, plus the commit `docs: define the pre-registered cache criterion precisely`, which made the definitions below exact. The spec's "Pre-registration" section carries the same text.

## Definitions

- **Hit** at threshold t: the best cache candidate has cosine >= t.
- **Production embedding**: Ollama `nomic-embed-text` (digest `0a109f422b47`), no prefix, unit-normalized.
- **(a) PAWS-X `es` test**: the 2000 human-translated pairs of the official PAWS-X release (`es/test_2k.tsv` from `x-final.tar.gz`; the archive SHA-256 is recorded with the data). Label 1 = paraphrase. Prediction = cosine(sentence1, sentence2) >= t. Precision = TP / (TP + FP); recall = TP / (TP + FN).
- **(c) Paraphrase replay**: the cache holds the 1000 Spanish corpus originals. Queries are the 200 paraphrases (200 prompts stratified 40 per task, seed `20261022`, one `qwen2.5:7b` rewrite each, temperature 0, fixed seed) and the 1000 originals leave-one-out. A correct hit is a paraphrase whose best candidate is its own original; every other hit is a false hit, including any hit on a leave-one-out original. Precision = correct hits / all hits; recall = correct hits / 200. For the verdict the cache matches on similarity alone (single tenant, empty context, tier rule disabled); tier-aware blocks are reported separately in the savings replay.
- **Estimates**: point estimates only. No confidence intervals are computed or reported (declared here).

## Criterion

The cache is *safe at a threshold t* when precision >= **0.95** on both (a) and (c) at t, with the production embedding. The verdict is reported at the default **t = 0.90**.

## Verdict rule

- **Eligibility:** a grid point t (0.80-0.99, step 0.01) is eligible only if it has >= 20 hits in each of (a) and (c). This avoids 0/0 and tiny-sample precisions. Only an eligible point can pass or be recommended.
- **Pass at 0.90:** both precisions are >= 0.95 at t = 0.90.
- **If it fails at 0.90:** report it as a result. The recommended t is the smallest eligible t on the grid with both precisions >= 0.95; report PAWS-X recall and replay recall there. The criterion does not move.
- **If no eligible t reaches 0.95 on both:** report "no safe threshold on the grid" and recommend the eligible t with the highest min(precision_a, precision_c).
- **Consequence:** on a pass the product default stays 0.90; otherwise the product default becomes the recommended t (new tenants only; stored tenant policies keep their value).
- The 40-item human paraphrase sample and the neighbor labels (b) are reported and never adjust the verdict.

## Declared beforehand

The corpus neighbors (b) were inspected during design: 22 pairs of distinct Spanish prompts at cosine >= 0.90, mostly false hits. These 22 pairs are part of the (b) set (cosine >= 0.85) and were seen non-blind. One of them is the near-identical MBPP pair (`es:code-0113` vs `es:code-0138`, cosine 1.0). The neighbors are therefore descriptive only and do not enter the verdict.

## Sensitivity model

`nomic-embed-text` v1.5 is an English model. `nomic-embed-text-v2-moe` (multilingual) is measured as sensitivity only and does not enter the verdict.

## How the verdict is computed

Computed by `make cache-eval`, which writes the verdict to `benchmarks/cache/v1/report.json` (key `preregistration`).
