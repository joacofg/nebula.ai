# Ground truth — fase 2

## Corpus

| lang | code | factual_qa | multistep_reasoning | open_writing | summarisation |
|---|---|---|---|---|---|
| es | 200 | 200 | 200 | 200 | 200 |
| en | 50 | 50 | 50 | 50 | 50 |

Translator `mistralai/mistral-medium-3.1`: 10 rejected by the number/code check; human review 0/40 wrong.

## Capture

| lang | role | ok | failed | truncated |
|---|---|---|---|---|
| es | qwen7b | 1000 | 0 | 7 |
| es | llama3b | 1000 | 0 | 2 |
| es | haiku | 1000 | 0 | 20 |
| es | gpt41 | 1000 | 0 | 2 |
| en | qwen7b | 250 | 0 | 0 |
| en | llama3b | 250 | 0 | 0 |
| en | haiku | 250 | 0 | 1 |
| en | gpt41 | 250 | 0 | 2 |

Pairs skipped: {'es': {'reference_unusable': 0, 'candidate_failed': 0}, 'en': {'reference_unusable': 0, 'candidate_failed': 0}}

## Judges

Rule selection on 22 EN pilot pairs graded by `human-3` (20 substitutable / 2 not; pairs the pilot chose because two earlier judges disagreed on them):

| rule | kappa |
|---|---|
| R1_unanimous | -0.015 |
| R2_majority | 0.327 |
| R3_ordinal_mean | 0.645 |

**Chosen: `R3_ordinal_mean`.**

Spanish hold-out (50 pairs, complete): kappa 0.308 [-0.070, 0.638] — **judge-limited**
Excluding code pairs (post hoc, rater low-confidence): 40 pairs, kappa 0.437 [0.000, 0.778]
Targeted rejections (not random, no code): human agrees with 20/25 ensemble rejections (80.0%, Wilson [0.609, 0.911]); decoys substitutable 9/10

Position flip rate: `deepseek/deepseek-chat-v3-0324` 8.1%, `google/gemini-2.5-flash` 12.5%
Inter-judge kappa: 0.617

## Tiers

### tiers.jsonl (coverage 100.0%)

| lang | task | local | economy | frontier | unlabelled |
|---|---|---|---|---|---|
| en | code | 36 | 10 | 4 | 0 |
| en | factual_qa | 41 | 4 | 5 | 0 |
| en | multistep_reasoning | 44 | 4 | 2 | 0 |
| en | open_writing | 32 | 5 | 13 | 0 |
| en | summarisation | 48 | 1 | 1 | 0 |
| es | code | 145 | 37 | 18 | 0 |
| es | factual_qa | 139 | 44 | 17 | 0 |
| es | multistep_reasoning | 171 | 24 | 5 | 0 |
| es | open_writing | 107 | 55 | 38 | 0 |
| es | summarisation | 180 | 14 | 6 | 0 |

### tiers.llama3b.jsonl (coverage 100.0%)

| lang | task | local | economy | frontier | unlabelled |
|---|---|---|---|---|---|
| en | code | 27 | 18 | 5 | 0 |
| en | factual_qa | 40 | 5 | 5 | 0 |
| en | multistep_reasoning | 38 | 10 | 2 | 0 |
| en | open_writing | 28 | 11 | 11 | 0 |
| en | summarisation | 44 | 5 | 1 | 0 |
| es | code | 102 | 69 | 29 | 0 |
| es | factual_qa | 115 | 65 | 20 | 0 |
| es | multistep_reasoning | 139 | 56 | 5 | 0 |
| es | open_writing | 91 | 67 | 42 | 0 |
| es | summarisation | 168 | 24 | 8 | 0 |

### tiers.R1_unanimous.jsonl (coverage 100.0%)

| lang | task | local | economy | frontier | unlabelled |
|---|---|---|---|---|---|
| en | code | 29 | 11 | 10 | 0 |
| en | factual_qa | 29 | 11 | 10 | 0 |
| en | multistep_reasoning | 43 | 5 | 2 | 0 |
| en | open_writing | 23 | 6 | 21 | 0 |
| en | summarisation | 39 | 5 | 6 | 0 |
| es | code | 105 | 36 | 59 | 0 |
| es | factual_qa | 100 | 57 | 43 | 0 |
| es | multistep_reasoning | 167 | 24 | 9 | 0 |
| es | open_writing | 55 | 59 | 86 | 0 |
| es | summarisation | 124 | 39 | 37 | 0 |

### tiers.R2_majority.jsonl (coverage 100.0%)

| lang | task | local | economy | frontier | unlabelled |
|---|---|---|---|---|---|
| en | code | 33 | 9 | 8 | 0 |
| en | factual_qa | 37 | 4 | 9 | 0 |
| en | multistep_reasoning | 44 | 4 | 2 | 0 |
| en | open_writing | 25 | 6 | 19 | 0 |
| en | summarisation | 43 | 4 | 3 | 0 |
| es | code | 130 | 35 | 35 | 0 |
| es | factual_qa | 119 | 54 | 27 | 0 |
| es | multistep_reasoning | 170 | 24 | 6 | 0 |
| es | open_writing | 80 | 59 | 61 | 0 |
| es | summarisation | 162 | 24 | 14 | 0 |

### tiers.R3_ordinal_mean.jsonl (coverage 100.0%)

| lang | task | local | economy | frontier | unlabelled |
|---|---|---|---|---|---|
| en | code | 36 | 10 | 4 | 0 |
| en | factual_qa | 41 | 4 | 5 | 0 |
| en | multistep_reasoning | 44 | 4 | 2 | 0 |
| en | open_writing | 32 | 5 | 13 | 0 |
| en | summarisation | 48 | 1 | 1 | 0 |
| es | code | 145 | 37 | 18 | 0 |
| es | factual_qa | 139 | 44 | 17 | 0 |
| es | multistep_reasoning | 171 | 24 | 5 | 0 |
| es | open_writing | 107 | 55 | 38 | 0 |
| es | summarisation | 180 | 14 | 6 | 0 |

## Spend

Total USD 9.84: translate 0.43, capture 5.40, judge 4.02
