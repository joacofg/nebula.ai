# Metric validation — pilot study

Reference rater: `human-2`. Raters: `human-2`, `llm-gemini-2.5-flash (auxiliary)`, `llm-judge (auxiliary)`.

**Human-to-human agreement: PENDING.** Rigour point 3 of the Phase 1 plan asks for two human evaluators. This run has 1. The LLM rater below is an auxiliary rater: it followed the same rubric on the same blinded pairs, and its agreement with the human rater is evidence that the rubric can be applied consistently — it is not the inter-rater agreement the plan requires, and it must not be reported as such.

Withdrawn passes, kept in the repository as evidence and excluded from every number below: `human-1`.

## Task prefix sweep

Which `nomic-embed-text` task prefix best separates the grades. Decided after labelling, on the labels, so the choice cannot be read off the stratification.

### natural pairs — the pairs the metric is used on

| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |
|---|---|---|---|---|---|---|
| `search_query` | 33 | 0.532 | [0.188, 0.875] | 1767/233 | 0.147 | — |
| `none` | 33 | 0.468 | [0.125, 0.812] | 1767/233 | 0.143 | — |
| `clustering` | 33 | 0.468 | [0.125, 0.812] | 1767/233 | 0.133 | — |
| `search_document` | 33 | 0.403 | [0.097, 0.719] | 1767/233 | 0.004 | — |

### all pairs, including planted negatives

| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |
|---|---|---|---|---|---|---|
| `search_query` | 41 | 0.906 | [0.729, 1.000] | 2000/0 | 0.658 | — |
| `none` | 41 | 0.894 | [0.703, 1.000] | 2000/0 | 0.656 | — |
| `clustering` | 41 | 0.894 | [0.705, 1.000] | 2000/0 | 0.653 | — |
| `search_document` | 41 | 0.881 | [0.678, 1.000] | 2000/0 | 0.610 | — |

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
| 0.00-0.50 | 1 | 0 | 0.00 |
| 0.50-0.65 | 7 | 0 | 0.00 |
| 0.80-0.90 | 11 | 10 | 0.91 |
| 0.90-1.00 | 22 | 21 | 0.95 |

### local_vs_premium only

| band | pairs | substitutable | rate |
|---|---|---|---|
| 0.80-0.90 | 10 | 9 | 0.90 |
| 0.90-1.00 | 16 | 15 | 0.94 |

## Inter-rater agreement

| rater | rater | shared pairs | Cohen κ (binary) | quadratic-weighted κ | 95% CI | note |
|---|---|---|---|---|---|---|
| human-2 | llm-gemini-2.5-flash (auxiliary) | 41 | 0.544 | 0.585 | [0.367, 0.756] | — |
| human-2 | llm-judge (auxiliary) | 41 | 0.436 | 0.560 | [0.343, 0.745] | — |
| llm-gemini-2.5-flash (auxiliary) | llm-judge (auxiliary) | 130 | 0.651 | 0.770 | [0.674, 0.848] | — |

Krippendorff's ordinal α across all raters: 0.638.
