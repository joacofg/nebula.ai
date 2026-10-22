# Pre-registration: semantic cache measurement

Date: 2026-10-22. Fixed before computing any precision, recall or verdict: the commit of this file, its two amendments (`5bd4632` and `2f20e53`) and the final tightening commit `docs: tighten the cache pre-registration before measuring` and the data-acquisition amendment at the end of this file (commit `docs: record the data-acquisition amendment to the cache pre-registration`) and the paraphrase-validity amendment at the end of this file (commit `docs: fix the paraphrase validity rule before regenerating`) precede every commit that computes one.

Design reference: `docs/superpowers/specs/2026-10-22-semantic-cache-measurement-design.md` (Part B) at spec commit `98015a0`, plus the amendments named above, which made the definitions exact and covered the edge cases. The spec's "Pre-registration" section condenses it.

## Definitions

- **Hit** at threshold t: the best cache candidate has cosine >= t.
- **Production embedding**: Ollama `nomic-embed-text` (digest `0a109f422b47`), no prefix, unit-normalized.
- **(a) PAWS-X `es` test**: the 1999 valid human-translated pairs of the PAWS-X `es` test split (2000 rows minus one `NS` placeholder row; source, checksums and cleaning are recorded in the data-acquisition amendment below and in `benchmarks/cache/v1/pawsx/LICENSE.md`). Label 1 = paraphrase. Prediction = cosine(sentence1, sentence2) >= t; a hit in (a) is a positive prediction (TP + FP). Precision = TP / (TP + FP); recall = TP / (TP + FN).
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

The corpus neighbors (b) were inspected during design: 20 pairs of distinct Spanish prompts at cosine >= 0.90, mostly false hits (the first version of this paragraph said 22, a count that included the English subset; see the data-acquisition amendment below). These 20 pairs are part of the (b) set (cosine >= 0.85) and were seen non-blind. One of them is the near-identical MBPP pair (`es:code-0113` vs `es:code-0138`, cosine 1.0). The neighbors are therefore descriptive only and do not enter the verdict.

The same pairs are corpus originals, so in (c) they also appear as leave-one-out false hits by rule (including `es:code-0113` vs `es:code-0138`, which is semantically a correct hit). The author saw them before fixing this criterion, which makes a fail of (c) at 0.90 likely and known in advance; the criterion was kept because a cache that serves a different question's answer at 0.90 is exactly what it must reject.

## Sensitivity model

`nomic-embed-text` v1.5 is an English model. `nomic-embed-text-v2-moe` (multilingual) is measured as sensitivity only and does not enter the verdict.

## How the verdict is computed

Computed by `make cache-eval`, which writes the verdict to `benchmarks/cache/v1/report.json` (key `preregistration`).

## Amendment (data acquisition, 2026-10-22, before any precision was computed)

Written after the evaluation data were built (`make cache-data`, commit `feat(cache-eval): PAWS-X and corpus-neighbor pairs with cosines`) and before any precision, recall or verdict was computed. Three facts about the data differ from what the sections above first said; they are corrected here and in the definitions above.

1. **Source of (a).** The official archive `https://storage.googleapis.com/paws/pawsx/x-final.tar.gz` (the URL in the dataset README) answered HTTP 403 to every anonymous request on 2026-10-22, so the archive and its SHA-256 are not available. The `es` test split (2000 rows) was taken from the Hugging Face dataset `google-research-datasets/paws-x` (same publisher, revision `4cd8187c404bda33cb1f62b49b001115862acf37`) and checked row for row against that dataset's parquet file `es/test-00000-of-00001.parquet`, SHA-256 `5ba872e113a79c783616e59d3d28ec0e922b6db745d797e5eb95010a32928bee` (equal to the Hugging Face object id). Byte identity with `x-final/es/test_2k.tsv` could not be verified. All hashes are in `benchmarks/cache/v1/pawsx/LICENSE.md`.
2. **Size of (a).** (a) has **1999** valid pairs, not 2000: one row is the `NS` placeholder (id 5815, `sentence1` = `NS`, label 0) that the dataset README tells users to remove. Wherever the definitions above stated the size of (a), it is 1999.
3. **Declared prior inspection, corrected.** At cosine >= 0.90 there are **20** pairs of distinct Spanish prompts among the 1000 corpus prompts (22 when the 250-prompt English subset is counted too; the two extra pairs are `en:code-0021` vs `en:code-0046` at 0.946 and `en:summarisation-0050` vs `es:summarisation-0050` at 0.906). The (b) set at cosine >= 0.85 has **265** Spanish pairs. The 20 pairs were seen non-blind, including the near-identical MBPP pair (`es:code-0113` vs `es:code-0138`, cosine 1.0). The leave-one-out disclosure above stands as written: it refers to the Spanish pairs.

None of these changes touches the criterion (precision >= 0.95 on both (a) and (c)), the threshold (t = 0.90), the grid (0.80-0.99, step 0.01), the eligibility rule (>= 20 hits in each of (a) and (c)) or the verdict rule. The one removed row has label 0, so it could only have been a true negative or a false positive in (a).

## Amendment (paraphrase validity, 2026-10-22, before any hit, precision or recall was computed)

The first generation of the paraphrases put the instruction and the prompt in one user message, and `qwen2.5:7b` answered instead of rewriting in some cases: 27 of 200 paraphrases were under 30 % of the original's length (only lengths were inspected; no cosine, hit, precision or recall was looked at). Paraphrases are regenerated with the instruction as the system message and the prompt as the user message. The rule below is fixed before the regeneration, without seeing its outputs.

- A paraphrase is **valid** when its length is between 0.5 and 2.0 times the original's, in characters (both bounds included). Invalid paraphrases are dropped and counted, with their reason.
- (c) uses only valid paraphrases: recall = correct hits / valid paraphrases. Wherever the definitions above say 200 paraphrases for (c), the count is the number of valid paraphrases. The 1000 originals leave-one-out are unchanged.
- The 40-item human sample is drawn from valid paraphrases.
- If fewer than 150 paraphrases are valid, the report says so.

None of this touches the criterion (precision >= 0.95 on both (a) and (c)), the threshold (t = 0.90), the grid (0.80-0.99, step 0.01), the eligibility rule (>= 20 hits in each of (a) and (c)) or the verdict rule.
