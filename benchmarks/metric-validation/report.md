# Metric validation — pilot study

Reference rater: `llm-judge`. Raters: `llm-gemini-2.5-flash (auxiliary)`, `llm-judge (auxiliary)`.

**Human-to-human agreement: PENDING.** Rigour point 3 of the Phase 1 plan asks for two human evaluators. This run has 0. The LLM rater below is an auxiliary rater: it followed the same rubric on the same blinded pairs, and its agreement with the human rater is evidence that the rubric can be applied consistently — it is not the inter-rater agreement the plan requires, and it must not be reported as such.

Withdrawn passes, kept in the repository as evidence and excluded from every number below: `human-1`, `human-2`.

## Task prefix sweep

Which `nomic-embed-text` task prefix best separates the grades. Decided after labelling, on the labels, so the choice cannot be read off the stratification.

### natural pairs — the pairs the metric is used on

| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |
|---|---|---|---|---|---|---|
| `search_query` | 105 | 0.639 | [0.525, 0.750] | 2000/0 | 0.282 | — |
| `clustering` | 105 | 0.626 | [0.510, 0.741] | 2000/0 | 0.254 | — |
| `search_document` | 105 | 0.600 | [0.482, 0.717] | 2000/0 | 0.187 | — |
| `none` | 105 | 0.593 | [0.473, 0.713] | 2000/0 | 0.192 | — |

### all pairs, including planted negatives

| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |
|---|---|---|---|---|---|---|
| `search_query` | 130 | 0.797 | [0.717, 0.870] | 2000/0 | 0.608 | — |
| `clustering` | 130 | 0.790 | [0.705, 0.865] | 2000/0 | 0.591 | — |
| `search_document` | 130 | 0.776 | [0.690, 0.854] | 2000/0 | 0.558 | — |
| `none` | 130 | 0.772 | [0.682, 0.851] | 2000/0 | 0.560 | — |

An AUC over all pairs is **inflated** by the planted `cross_prompt` negatives: telling an answer to a different question from an answer to this one is easy, and every prefix does it. The natural-pairs table above is the one that says whether the cosine resolves quality among responses that all actually answered the prompt.


**Chosen prefix: `search_query`**, on local_vs_premium, premium_vs_premium.

## Where the metric sits — noise floor

**Noise floor.** `premium_vs_premium` is two different premium models answering the same prompt: the ceiling the cosine can reach when both answers are good. A `local_vs_premium` median has no interpretable scale without it. If the two medians coincide, the cosine is not resolving quality in that range — it is saturating, and a high similarity says only that both sides answered the question asked.

Cosine at the chosen prefix (`search_query`).

| pair kind | pairs | min | median | max |
|---|---|---|---|---|
| `local_vs_premium` | 80 | 0.827 | 0.938 | 0.986 |
| `premium_vs_premium` | 25 | 0.852 | 0.935 | 0.994 |
| `cross_prompt` | 25 | 0.494 | 0.555 | 0.629 |

## Separation by similarity band

`cross_prompt` pairs are planted negatives: a premium answer to a *different* prompt of the same task type. They anchor the low band so AUC is measurable, but they are not traffic Nebula would ever route. The `local_vs_premium only` table below is the honest one.

### all pairs

| band | pairs | substitutable | rate |
|---|---|---|---|
| 0.00-0.50 | 2 | 0 | 0.00 |
| 0.50-0.65 | 23 | 0 | 0.00 |
| 0.80-0.90 | 24 | 12 | 0.50 |
| 0.90-1.00 | 81 | 61 | 0.75 |

### local_vs_premium only

| band | pairs | substitutable | rate |
|---|---|---|---|
| 0.80-0.90 | 21 | 11 | 0.52 |
| 0.90-1.00 | 59 | 42 | 0.71 |

## Inter-rater agreement

| rater | rater | shared pairs | Cohen κ (binary) | quadratic-weighted κ | 95% CI | note |
|---|---|---|---|---|---|---|
| llm-gemini-2.5-flash (auxiliary) | llm-judge (auxiliary) | 130 | 0.651 | 0.770 | [0.674, 0.848] | — |

Krippendorff's ordinal α across all raters: 0.733.
