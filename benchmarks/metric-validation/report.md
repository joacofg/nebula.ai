# Metric validation — pilot study

Reference rater: `human-3`. Raters: `human-3`, `llm-gemini-2.5-flash (auxiliary)`, `llm-judge (auxiliary)`.

**Human-to-human agreement: PENDING.** Rigour point 3 of the Phase 1 plan asks for two human evaluators. This run has 1. The LLM rater below is an auxiliary rater: it followed the same rubric on the same blinded pairs, and its agreement with the human rater is evidence that the rubric can be applied consistently — it is not the inter-rater agreement the plan requires, and it must not be reported as such.

Withdrawn passes, kept in the repository as evidence and excluded from every number below: `human-1`, `human-2`.

## Task prefix sweep

Which `nomic-embed-text` task prefix best separates the grades. Decided after labelling, on the labels, so the choice cannot be read off the stratification.

### natural pairs — the pairs the metric is used on

| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |
|---|---|---|---|---|---|---|
| `search_document` | 22 | 0.250 | [0.000, 0.561] | 1727/273 | 0.106 | — |
| `none` | 22 | 0.225 | [0.000, 0.500] | 1727/273 | 0.087 | — |
| `search_query` | 22 | 0.225 | [0.048, 0.450] | 1727/273 | 0.071 | — |
| `clustering` | 22 | 0.225 | [0.000, 0.500] | 1727/273 | 0.058 | — |

### all pairs, including planted negatives

| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |
|---|---|---|---|---|---|---|
| `search_document` | 22 | 0.250 | [0.000, 0.561] | 1727/273 | 0.106 | — |
| `none` | 22 | 0.225 | [0.000, 0.500] | 1727/273 | 0.087 | — |
| `search_query` | 22 | 0.225 | [0.048, 0.450] | 1727/273 | 0.071 | — |
| `clustering` | 22 | 0.225 | [0.000, 0.500] | 1727/273 | 0.058 | — |

An AUC over all pairs is **inflated** by the planted `cross_prompt` negatives: telling an answer to a different question from an answer to this one is easy, and every prefix does it. The natural-pairs table above is the one that says whether the cosine resolves quality among responses that all actually answered the prompt.


**Chosen prefix: `search_document`**, on local_vs_premium, premium_vs_premium.

## Where the metric sits — noise floor

**Noise floor.** `premium_vs_premium` is two different premium models answering the same prompt: the ceiling the cosine can reach when both answers are good. A `local_vs_premium` median has no interpretable scale without it. If the two medians coincide, the cosine is not resolving quality in that range — it is saturating, and a high similarity says only that both sides answered the question asked.

Cosine at the chosen prefix (`search_document`).

| pair kind | pairs | min | median | max |
|---|---|---|---|---|
| `local_vs_premium` | 80 | 0.838 | 0.944 | 0.993 |
| `premium_vs_premium` | 25 | 0.849 | 0.939 | 0.985 |
| `cross_prompt` | 25 | 0.506 | 0.564 | 0.636 |

## Separation by similarity band

`cross_prompt` pairs are planted negatives: a premium answer to a *different* prompt of the same task type. They anchor the low band so AUC is measurable, but they are not traffic Nebula would ever route. The `local_vs_premium only` table below is the honest one.

### all pairs

| band | pairs | substitutable | rate |
|---|---|---|---|
| 0.80-0.90 | 5 | 5 | 1.00 |
| 0.90-1.00 | 17 | 15 | 0.88 |

### local_vs_premium only

| band | pairs | substitutable | rate |
|---|---|---|---|
| 0.80-0.90 | 4 | 4 | 1.00 |
| 0.90-1.00 | 15 | 13 | 0.87 |

## Inter-rater agreement

| rater | rater | shared pairs | Cohen κ (binary) | quadratic-weighted κ | 95% CI | note |
|---|---|---|---|---|---|---|
| human-3 | llm-gemini-2.5-flash (auxiliary) | 22 | 0.094 | 0.359 | [-0.032, 0.684] | — |
| human-3 | llm-judge (auxiliary) | 22 | -0.051 | -0.199 | [-0.544, 0.033] | — |
| llm-gemini-2.5-flash (auxiliary) | llm-judge (auxiliary) | 130 | 0.651 | 0.770 | [0.674, 0.848] | — |

Krippendorff's ordinal α across all raters: 0.685.
