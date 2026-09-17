# Benchmark results kept for the thesis

`artifacts/benchmarks/` is gitignored: every `make benchmark` writes there and
the directory is disposable. The runs below are the ones cited in docs or in
the thesis, so they are copied here and versioned. Never edit a report in
place; re-run and add a new folder.

| Run | Why it is kept | Headline |
|---|---|---|
| `20260314T193127Z` | Golden v1.0 run referenced by `docs/evaluation.md` and `tests/golden/` | 14/14 scenarios passed |
| `20260819T225557Z` | Thesis anchor, run 1 of 3 (same 14 scenarios, healthy dependencies) | 41.2 % premium spend avoided |
| `20260819T225703Z` | Thesis anchor, run 2 of 3 | 38.2 % premium spend avoided |
| `20260819T225713Z` | Thesis anchor, run 3 of 3 | 40.0 % premium spend avoided |
| `20260903T143128Z` | Example of a degraded run carrying the **NOT COMPARABLE** banner (Qdrant down) | not comparable |

The three August runs measure the two-rule heuristic router against a
premium-only baseline. They stop being comparable once the learned router
lands (phase 3); they stay here as the "before" picture.
