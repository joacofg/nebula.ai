---
task: T01
title: Enrich RouteDecision and RouterService with signal model
wave: 1
depends_on: []
files_modified:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
requirements:
  - R039
autonomous: true
---

# T01: Enrich RouteDecision and RouterService with signal model

## Goal

Add `signals: dict[str, Any]` and `score: float` to `RouteDecision`, implement token-estimate-based complexity tiering and policy-context signals in `RouterService.choose_target_with_reason()`, and wire the policy object through `PolicyService.resolve()`.

## Must-Haves

- `RouteDecision` has `signals` and `score` fields with defaults so all existing construction sites are valid unchanged
- `choose_target_with_reason()` accepts `policy: TenantPolicy | None = None` parameter
- Every non-override routing path populates `signals` with `token_count`, `complexity_tier`, `budget_proximity`, `model_constraint` keys
- Every non-override routing path populates `score` as a 0.0–1.0 float
- Reason code `"token_complexity"` replaces `"simple_prompt"` and `"prompt_length"` in the heuristic path
- `PolicyService.resolve()` passes `policy=policy` to `choose_target_with_reason()`

## Tasks

<task id="1">
<title>Extend RouteDecision dataclass and rewrite heuristic routing logic</title>
<read_first>
- src/nebula/services/router_service.py — full file; understand all existing RouteDecision construction sites and the heuristic branching logic before modifying
- src/nebula/models/governance.py — TenantPolicy fields: routing_mode_default, allowed_premium_models, soft_budget_usd, max_premium_cost_per_request
- src/nebula/core/config.py — Settings.router_complexity_chars (used in current char-count threshold)
</read_first>
<action>
Rewrite `src/nebula/services/router_service.py` as follows.

**Imports to add:**
```python
from dataclasses import dataclass, field
from math import ceil
from typing import Any, Literal

from nebula.models.governance import TenantPolicy  # add to existing import line
```

**Updated RouteDecision:**
```python
@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str
    signals: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
```

**Module-level helper (add before RouterService class):**
```python
def _estimate_token_count(text: str) -> int:
    """Chars/4 heuristic — same formula as PolicyService._estimate_text_tokens()."""
    return max(1, ceil(len(text) / 4))
```

**Updated RouterService.choose_target_with_reason() signature:**
```python
async def choose_target_with_reason(
    self,
    prompt: str,
    request: ChatCompletionRequest,
    routing_mode: RoutingMode = "auto",
    policy: TenantPolicy | None = None,
) -> RouteDecision:
```

**Override paths (before heuristics):** Explicit model and routing-mode override paths remain. Return them with empty signals and score=0.0 (default), since they are not heuristic decisions:
```python
if requested_model and request.model == self.settings.local_model:
    return RouteDecision(target="local", reason="explicit_local_model")
if requested_model:
    return RouteDecision(target="premium", reason="explicit_premium_model")
if routing_mode == "local_only":
    return RouteDecision(target="local", reason="policy_local_only")
if routing_mode == "premium_only":
    return RouteDecision(target="premium", reason="policy_premium_only")
```

**Signal computation block (replaces the keyword/char-count block):**
```python
# --- Signal computation ---
token_count = _estimate_token_count(prompt)
# Complexity tier thresholds: <500 = low, 500-2000 = medium, >2000 = high
if token_count < 500:
    complexity_tier = "low"
elif token_count <= 2000:
    complexity_tier = "medium"
else:
    complexity_tier = "high"

# Policy context signals
budget_proximity: float | None = None
if policy is not None and policy.soft_budget_usd and policy.soft_budget_usd > 0:
    # budget_proximity is passed in pre-computed only if a caller provides current_spend;
    # for now compute as a signal flag — the ratio requires current_spend which is not
    # available here. Store None and let callers who have spend data override if needed.
    pass  # budget_proximity stays None unless policy_service passes spend context

model_constraint = bool(policy is not None and policy.allowed_premium_models)

signals: dict[str, Any] = {
    "token_count": token_count,
    "complexity_tier": complexity_tier,
    "budget_proximity": budget_proximity,
    "model_constraint": model_constraint,
}

# --- Scoring ---
# token_score: normalized against 500-token threshold; capped at 1.0 for display
token_score = min(token_count / 500, 1.0)
# policy adjustment: model constraint adds 0.1
policy_bonus = 0.1 if model_constraint else 0.0
score = round(min(token_score + policy_bonus, 1.0), 4)

# --- Keyword hint check ---
complexity_hints = ("analyze", "reason", "contract", "debug", "architecture", "design")
keyword_match = any(hint in prompt.lower() for hint in complexity_hints)
signals["keyword_match"] = keyword_match

# --- Routing decision ---
if complexity_tier == "low" and not keyword_match:
    return RouteDecision(target="local", reason="token_complexity", signals=signals, score=score)
return RouteDecision(target="premium", reason="token_complexity", signals=signals, score=score)
```

Remove the old `choose_target` alias or keep it unchanged — it delegates to `choose_target_with_reason` and is not affected.
</action>
<acceptance_criteria>
- `grep -n "signals: dict\[str, Any\]" src/nebula/services/router_service.py` — returns a line containing `signals: dict[str, Any] = field(default_factory=dict)`
- `grep -n "score: float" src/nebula/services/router_service.py` — returns a line containing `score: float = 0.0`
- `grep -n "def _estimate_token_count" src/nebula/services/router_service.py` — returns a line defining the helper
- `grep -n "policy: TenantPolicy" src/nebula/services/router_service.py` — returns a line in the method signature
- `grep -n '"prompt_length"\|"simple_prompt"' src/nebula/services/router_service.py` — returns no matches (old reason codes removed)
- `grep -n '"token_complexity"' src/nebula/services/router_service.py` — returns at least 2 matches (both return sites)
- `grep -n "complexity_tier" src/nebula/services/router_service.py` — returns matches for low/medium/high tier logic
- `pytest tests/test_chat_completions.py -x` exits 0 (existing tests unbroken)
</acceptance_criteria>
</task>

<task id="2">
<title>Update PolicyService to pass policy into choose_target_with_reason</title>
<read_first>
- src/nebula/services/policy_service.py — full file; focus on PolicyService.resolve() lines 40-110 and the existing call to choose_target_with_reason at line 49
</read_first>
<action>
In `src/nebula/services/policy_service.py`, update `PolicyService.resolve()` at line 49:

**Before:**
```python
route_decision = await router_service.choose_target_with_reason(
    prompt,
    request,
    routing_mode=policy.routing_mode_default,
)
```

**After:**
```python
route_decision = await router_service.choose_target_with_reason(
    prompt,
    request,
    routing_mode=policy.routing_mode_default,
    policy=policy,
)
```

No other changes are needed in policy_service.py for T01. The `soft_budget_exceeded` computation that already exists (lines 61-63) will be used in T02 to populate `budget_proximity` in the ledger signals. Do not move or change that logic now.
</action>
<acceptance_criteria>
- `grep -n "policy=policy" src/nebula/services/policy_service.py` — returns exactly 1 match inside `resolve()`
- `pytest tests/test_chat_completions.py tests/test_admin.py tests/test_governance.py -x` exits 0
</acceptance_criteria>
</task>

## Verification

```
pytest tests/test_chat_completions.py tests/test_admin.py tests/test_governance.py -x
```

All existing tests pass. The `RouteDecision` dataclass is backward-compatible (default fields).

## Success Criteria

- `RouteDecision` has `signals` and `score` fields with safe defaults
- All existing `RouteDecision(target=..., reason=...)` call sites still work without modification
- `choose_target_with_reason()` accepts optional `policy` and returns populated signals for all heuristic paths
- Reason codes `"simple_prompt"` and `"prompt_length"` are gone; `"token_complexity"` is used for all heuristic routing
- `PolicyService.resolve()` passes `policy=policy` to the router
- Full test suite green
