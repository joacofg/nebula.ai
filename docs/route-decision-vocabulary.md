# Route decision vocabulary

S01 replaces the earlier char-count heuristic with an explicit routing signal model. This document is the stable vocabulary reference for operator understanding today and for S02 simulation replay against persisted ledger entries.

## Signal reference

| Signal key | Type | Source | Plain-language meaning |
| --- | --- | --- | --- |
| `token_count` | int | `ceil(len(prompt) / 4)` | Estimated token count of the request prompt |
| `complexity_tier` | `"low" | "medium" | "high"` | Token-count thresholds: `<500`, `500–2000`, `>2000` | Routing complexity band |
| `keyword_match` | bool | Complexity-hint keyword scan | Whether the prompt contains a complexity-hint keyword |
| `model_constraint` | bool | `policy.allowed_premium_models` | Whether the tenant policy restricts available premium models |
| `budget_proximity` | float \| null | Computed spend ratio when `soft_budget_usd` is set | Fraction of soft budget already consumed (`null` if no budget is configured) |

## Score

The route score is a normalised float in the `0.0–1.0` range, computed as `min(token_count / 500, 1.0) + 0.1 if model_constraint`, then capped to `1.0`. It is an audit artifact for simulation replay and operator inspection, not a hard routing threshold.

## Reason code reference

| Reason code | Signals populated | Plain-language meaning |
| --- | --- | --- |
| `token_complexity` | All heuristic signals populated | Route driven by token-count complexity tiering |
| `policy_budget_advisory` | `budget_proximity` set | Local route preferred because soft budget is near its limit |
| `policy_model_constraint` | `model_constraint=true` | Available premium models restricted by policy allowlist |
| `explicit_local_model` | Signals empty (override path) | Caller explicitly requested a local model by name |
| `explicit_premium_model` | Signals empty (override path) | Caller explicitly requested a non-local model |
| `policy_local_only` | Signals empty (override path) | Routing mode is `local_only` |
| `policy_premium_only` | Signals empty (override path) | Routing mode is `premium_only` |

Signal keys and reason codes in this document are stable from S01 forward; S02 simulation depends on these names for ledger replay.
