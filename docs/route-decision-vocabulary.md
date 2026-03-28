# Route decision vocabulary

S01 replaced the earlier char-count heuristic with an explicit routing signal model. This document is the stable vocabulary reference for operator understanding today and for S02/S03 simulation replay against persisted ledger entries.

## Signal reference

| Signal key | Type | Source | Plain-language meaning |
| --- | --- | --- | --- |
| `token_count` | int | `ceil(len(prompt) / 4)` | Estimated token count of the request prompt |
| `complexity_tier` | `"low" | "medium" | "high"` | Token-count thresholds: `<500`, `500–2000`, `>2000` | Routing complexity band |
| `keyword_match` | bool | Complexity-hint keyword scan | Whether the prompt contains a complexity-hint keyword |
| `model_constraint` | bool | `policy.allowed_premium_models` | Whether the tenant policy restricts available premium models |
| `budget_proximity` | float \| null | Computed spend ratio when `soft_budget_usd` is set | Fraction of advisory soft budget already consumed (`null` if no soft budget is configured) |

## Score

The route score is a normalised float in the `0.0–1.0` range, computed as `min(token_count / 500, 1.0) + 0.1 if model_constraint`, then capped to `1.0`. It is an audit artifact for simulation replay and operator inspection, not a hard routing threshold.

## Reason code reference

| Reason code | Signals populated | Plain-language meaning |
| --- | --- | --- |
| `token_complexity` | All heuristic signals populated | Route driven by token-count complexity tiering |
| `policy_budget_advisory` | `budget_proximity` set | Local route preferred because advisory soft budget is near its limit |
| `policy_model_constraint` | `model_constraint=true` | Available premium models restricted by policy allowlist |
| `hard_budget_downgrade` | Existing route signals preserved from the baseline decision | Cumulative hard budget was exhausted, so compatible auto-routed traffic was downgraded to local instead of premium |
| `explicit_local_model` | Signals empty (override path) | Caller explicitly requested a local model by name |
| `explicit_premium_model` | Signals empty (override path) | Caller explicitly requested a non-local model |
| `policy_local_only` | Signals empty (override path) | Routing mode is `local_only` |
| `policy_premium_only` | Signals empty (override path) | Routing mode is `premium_only` |

## Policy outcome vocabulary

These values are operator-facing explanation strings carried through headers, simulation diffs, and the usage ledger. They stay within decisioning scope: they explain why routing changed, but they do not create a separate analytics or billing subsystem.

| Policy outcome fragment / shape | Meaning for operators |
| --- | --- |
| `default` | No policy override or advisory signal changed the request outcome |
| `routing_mode=premium_only` / `routing_mode=local_only` | The tenant default routing mode forced the request path |
| `cache=disabled` | Cache participation was disabled by policy |
| `fallback=disabled` | Premium fallback after local failure was disabled by policy |
| `soft_budget=exceeded` | Advisory soft budget was exceeded; request still ran, but operator-visible metadata was attached |
| `hard_budget=exceeded(limit_usd=…,spent_usd=…,enforcement=…)` | Hard cumulative tenant budget was exhausted at decision time, including the configured enforcement mode |
| `budget_action=downgraded_to_local` | Hard-budget enforcement kept the request allowed by routing compatible auto traffic to local |
| `denied=Request exceeds the tenant premium spend guardrail.` | Per-request premium cost guardrail denied the request |
| `denied=Tenant hard budget limit reached; premium routing is blocked (spent_usd=…, limit_usd=…).` | Hard cumulative budget blocked premium routing; explicit premium or non-downgradable traffic was denied |

Signal keys, reason codes, and policy outcome fragments in this document are stable from S01 forward; S02 simulation replay and S03 operator surfaces depend on these names for consistent explanations.
