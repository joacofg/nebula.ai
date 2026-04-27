# Route decision vocabulary

S01 replaces the duplicated heuristic branches with a shared calibrated routing contract. This document is the stable vocabulary reference for operator understanding today and for later simulation replay against persisted ledger entries.

## Signal reference

Stable replay-critical keys remain unchanged: `token_count`, `keyword_match`, and `complexity_tier`. New keys are additive and exist to make calibrated-versus-degraded behavior and score construction explicit in runtime evidence.

| Signal key | Type | Source | Plain-language meaning |
| --- | --- | --- | --- |
| `token_count` | int | `ceil(len(prompt) / 4)` or replay context | Estimated token count used by routing |
| `complexity_tier` | `"low" | "medium" | "high"` | Token-count thresholds: `<500`, `500–2000`, `>2000` | Routing complexity band |
| `keyword_match` | bool | Complexity-hint keyword scan or replay context | Whether the request includes a complexity-hint keyword |
| `model_constraint` | bool | `policy.allowed_premium_models` | Whether tenant policy restricts available premium models |
| `budget_proximity` | float \| null | Reserved advisory spend ratio signal | Fraction of advisory soft budget consumed (`null` in the current shipped contract) |
| `route_mode` | `"calibrated" | "degraded"` | Router decision path | Whether routing used the full calibrated signal set or had to reconstruct missing replay inputs |
| `calibrated_routing` | bool | Derived from `route_mode` | Convenience flag for fully calibrated routing |
| `degraded_routing` | bool | Derived from `route_mode` | Convenience flag for replay decisions that had to infer missing signals |
| `replay` | bool | Live vs replay path | Whether the decision was computed during simulation replay |
| `score_components.token_score` | float | `min(token_count / 500, 1.0)` | Additive base contribution from token volume |
| `score_components.keyword_bonus` | float | `0.2` when `keyword_match`, else `0.0` | Additive complexity bump for hint keywords |
| `score_components.policy_bonus` | float | `0.1` when `model_constraint`, else `0.0` | Additive bump showing policy-constrained premium selection context |
| `score_components.outcome_bonus` | float | Outcome-grounded additive factor when recent request evidence favors the same route | Shared pointer-first explanation term for positive outcome evidence; see `outcome_evidence` |
| `score_components.evidence_penalty` | float | Outcome-grounded subtractive factor when recent request evidence weakens confidence in the same route | Shared pointer-first explanation term for degraded or cautionary evidence pressure; see `outcome_evidence` |
| `score_components.budget_penalty` | float | Reserved for future advisory spend shaping | Additive budget penalty (`0.0` in the current shipped contract) |
| `score_components.total_score` | float | Clamped sum of additive components | Final route score exposed in runtime evidence and headers |

## Score

The route score is a normalized float in the `0.0–1.0` range. The shipped calibrated formula is:

- `token_score = min(token_count / 500, 1.0)`
- `keyword_bonus = 0.2 if keyword_match else 0.0`
- `policy_bonus = 0.1 if model_constraint else 0.0`
- `budget_penalty = 0.0`
- `total_score = clamp(token_score + keyword_bonus + policy_bonus - budget_penalty, 0.0, 1.0)`

`X-Nebula-Route-Score` and persisted `route_score` both expose `total_score`. The named components exist so later slices can reason about the additive explanation without reverse-engineering the implementation.

For M009's pointer-first close-out proof, `outcome_bonus`, `evidence_penalty`, and `outcome_evidence` are shared discoverability terms rather than a second scoring spec: runtime headers, persisted ledger rows, replay output, and request detail should all point back to these names instead of redefining them inline.

## Route mode semantics

| Route mode | Meaning |
| --- | --- |
| `calibrated` | The router had the full calibrated signal set for this decision. Live requests always use this mode. Replay requests use it when persisted `token_count`, `keyword_match`, and `complexity_tier` are all present. |
| `degraded` | Replay was missing one or more persisted calibrated inputs, so the router reconstructed the missing value from the synthetic replay prompt or token count. The stable replay-critical subset is still preserved when present. |

Explicit model overrides and policy-forced routing remain override paths with empty `signals`; they do not emit `route_mode` or score breakdown fields because calibrated scoring did not participate in the decision.

## Reason code reference

| Reason code | Signals populated | Plain-language meaning |
| --- | --- | --- |
| `token_complexity` | Calibrated or degraded routing signals populated | Route driven by the shared calibrated complexity contract |
| `policy_budget_advisory` | `budget_proximity` set | Local route preferred because advisory soft budget is near its limit |
| `policy_model_constraint` | `model_constraint=true` | Available premium models restricted by policy allowlist |
| `hard_budget_downgrade` | Existing route signals preserved from the baseline decision | Cumulative hard budget was exhausted, so compatible auto-routed traffic was downgraded to local instead of premium |
| `explicit_local_model` | Signals empty (override path) | Caller explicitly requested a local model by name |
| `explicit_premium_model` | Signals empty (override path) | Caller explicitly requested a non-local model |
| `policy_local_only` | Signals empty (override path) | Routing mode is `local_only` |
| `policy_premium_only` | Signals empty (override path) | Routing mode is `premium_only` |

## Policy outcome vocabulary

`outcome_evidence` is the shared pointer-first umbrella term for the bounded request evidence that informs route explanation across runtime headers, persisted ledger rows, replay output, and selected request detail. It is intentionally discoverability-oriented: later docs may point here instead of restating field-by-field outcome-grounded semantics inline.

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

Signal keys, route modes, reason codes, and policy outcome fragments in this document are stable from S01 forward; downstream replay and operator surfaces depend on these names for consistent explanations.
