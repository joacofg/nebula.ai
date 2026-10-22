# Pre-registration: semantic cache measurement

Date: 2026-10-22. Fixed before computing any precision. The commit of this file precedes every commit that computes a precision, a recall or a verdict.

Design: `docs/superpowers/specs/2026-10-22-semantic-cache-measurement-design.md` (Part B).

## Criterion

The cache is *safe at a threshold t* when precision >= **0.95** on both:

- (a) PAWS-X `es` test, and
- (c) the paraphrase replay,

with the production embedding (`nomic-embed-text`, no prefix). The verdict is reported at the default **t = 0.90**.

## If it fails at 0.90

Report it as a result. Recommend the smallest t on the grid 0.80-0.99 (step 0.01) where both precisions are >= 0.95, and report recall there. The criterion does not move.

## Declared beforehand

The corpus neighbors (b) were inspected during design: 22 pairs of distinct Spanish prompts at cosine >= 0.90, mostly false hits, and one near-identical MBPP pair. They are therefore descriptive only and do not enter the verdict.

## Sensitivity model

`nomic-embed-text` v1.5 is an English model. `nomic-embed-text-v2-moe` (multilingual) is measured as sensitivity only and does not enter the verdict.

## How the verdict is computed

The verdict is computed by `make cache-eval` from `benchmarks/cache/v1/report.json`, using only the production embedding.
