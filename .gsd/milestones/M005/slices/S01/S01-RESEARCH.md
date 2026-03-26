# S01: Adaptive Routing Model — Research

**Researched:** 2026-03-26
**Domain:** Routing signal architecture, ledger schema migration, observability console extension
**Confidence:** HIGH — all findings are from direct codebase inspection

---

<user_constraints>
## User Constraints (from S01-CONTEXT.md)

### Locked Decisions

- Primary new signals: token estimate (replaces char count) + policy-context signals (budget proximity, model constraints from `TenantPolicy`)
- Policy fields (`soft_budget_usd`, `max_premium_cost_per_request`, `allowed_premium_models`) are inputs to the decision model
- Signal model is fixed (not operator-configurable) — operator configurability deferred to S04
- Signal count: 3-4 total (token estimate, complexity tier, policy context, model preference)
- `RouteDecision` enriched with `signals: dict[str, Any]` and `score: float` fields
- Reason codes are structured with signal metadata payload
- Usage ledger gets a `route_signals` JSON column
- Existing `X-Nebula-Route` header extended with reason + top signal summary (no new header)
- Route decision details exposed via Observability request detail drawer — "Route Decision" section
- Signal display uses plain-language labels, not raw JSON
- S01 includes route-decision vocabulary and signal reference in `docs/`
- Test strategy: unit tests for signal scoring logic + integration test proving full request path uses new signals

### Claude's Discretion

- Exact token estimation approach (heuristic vs. tiktoken-style) — keep simple and fast, avoid heavy tokenizer dependency
- Complexity tier thresholds and exact scoring formula — defensible but tunable internally
- Specific doc filename and structure for route-decision vocabulary reference
- Console component placement within Observability drawer

### Deferred Ideas (OUT OF SCOPE)

- Operator-configurable signal weights — deferred to S04
- Semantic embedding as routing signal — too complex for S01
- Historical outcome signals (past latency/cost per route) — S02 produces this data
- Dedicated "Routing" console page — S01 extends Observability drawer only
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| R039 | Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone. | All six seams identified: router_service, policy_service, governance_store, db/models, chat_service, and the console ledger-request-detail drawer. Each seam has a concrete, minimal change that threads signal data end to end. |
</phase_requirements>

---

## Summary

S01 is a seam-threading exercise: routing signal data must flow from `RouterService.choose_target_with_reason()` all the way to the ledger, the response headers, and the Observability drawer without breaking the existing frozen dataclass contract or the admin API shape. The codebase is small and well-structured — there are exactly six extension points, each with a clear, minimal change required.

The current router is a single 52-line file (`router_service.py`) that makes all decisions via `len(prompt)` and a keyword list. The `PolicyService` already computes `soft_budget_exceeded` and `projected_premium_cost` and passes them through `PolicyResolution`, but these values are never fed back into the routing decision. The ledger schema has `route_reason` (Text) but no `route_signals` column — one additive migration is needed. The console `UsageLedgerRecord` TypeScript type and the `LedgerRequestDetail` component are both narrow and easily extended.

Token estimation already exists in `PolicyService._estimate_text_tokens()` (`ceil(len(content) / 4)`) — this is the chars/4 heuristic, which is adequate for complexity tiering and avoids a `tiktoken` dependency. The new router should reuse the same estimation approach; the planner does not need to introduce any new dependency.

**Primary recommendation:** Extend `RouteDecision` with `signals` and `score`, add `route_signals` JSON column to the ledger, thread signal data through the three existing seams (router → policy → chat → ledger/headers), and extend the console drawer. All changes are additive and backward-compatible with existing test infrastructure.

---

## Current Architecture Map

### Request Flow (traced end to end)

```
POST /v1/chat/completions
  └── chat.py: create_chat_completion()
        └── ChatService.create_completion_with_metadata()
              ├── ChatService._resolve_policy()
              │     └── PolicyService.resolve()
              │           └── RouterService.choose_target_with_reason()  ← SIGNAL COMPUTATION POINT
              │                 returns RouteDecision(target, reason)     ← ADD signals, score
              ├── ChatService._record_usage()
              │     └── GovernanceStore.record_usage(UsageLedgerRecord)  ← ADD route_signals
              └── chat.py: _nebula_headers(metadata)                     ← ADD signal summary to header
```

### PolicyService Already Computes Policy Context

`PolicyService.resolve()` (lines 40-110) already:
1. Calls `router_service.choose_target_with_reason()` and gets a `RouteDecision`
2. Computes `soft_budget_exceeded` from `store.tenant_spend_total()`
3. Computes `projected_premium_cost` using `_estimate_request_cost()`
4. Checks `allowed_premium_models` against the policy

The policy context signals (`budget_proximity`, `model_constraints`) are already computed — they just are not fed back into the routing decision or stored as structured signal data. The missing link is: pass policy context into `choose_target_with_reason()` and let it produce a richer `RouteDecision`.

**Critical seam:** `PolicyService.resolve()` calls `router_service.choose_target_with_reason(prompt, request, routing_mode=policy.routing_mode_default)` but does not pass the policy's `soft_budget_usd`, `max_premium_cost_per_request`, or `allowed_premium_models`. Those need to be passed as a new parameter so the router can fold them into its signal payload.

---

## Standard Stack

No new external dependencies are needed. All required capability is already present.

### Existing Relevant Dependencies

| Component | Location | What It Provides |
|-----------|----------|------------------|
| `policy_service._estimate_text_tokens()` | `src/nebula/services/policy_service.py:206` | `ceil(len(content) / 4)` — adequate token estimate heuristic |
| `TenantPolicy` fields | `src/nebula/models/governance.py:20-27` | `soft_budget_usd`, `max_premium_cost_per_request`, `allowed_premium_models` — all signal inputs |
| `RouteDecision` dataclass | `src/nebula/services/router_service.py:11-13` | Frozen dataclass to extend |
| `UsageLedgerModel` | `src/nebula/db/models.py:144-164` | SQLAlchemy model to add `route_signals` JSON column |
| `UsageLedgerRecord` Pydantic model | `src/nebula/models/governance.py:88-106` | Pydantic model to add `route_signals` field |
| Alembic migrations | `migrations/versions/` | Pattern: idempotent `if column not in columns` guard, `sa.JSON()` column type |

**No new pip install needed.** The `dict[str, Any]` type for signals is stdlib. SQLAlchemy `JSON` column type is already imported in `db/models.py` (line 6).

---

## Architecture Patterns

### The Six Extension Seams

#### Seam 1: `RouteDecision` dataclass — `router_service.py`

**Current:**
```python
@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str
```

**Required change:** Add two fields. Frozen dataclasses require all fields at construction.

```python
from typing import Any

@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str
    signals: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
```

`default_factory=dict` keeps every existing `RouteDecision(target=..., reason=...)` call valid without modification. The `field()` import is `from dataclasses import dataclass, field`.

**Frozen dataclass + mutable default:** `field(default_factory=dict)` is the correct pattern — not `signals: dict[str, Any] = {}` which would raise a `ValueError` for a mutable default on a frozen dataclass.

#### Seam 2: `RouterService.choose_target_with_reason()` — signal computation

**Current signature:**
```python
async def choose_target_with_reason(
    self,
    prompt: str,
    request: ChatCompletionRequest,
    routing_mode: RoutingMode = "auto",
) -> RouteDecision:
```

**Required change:** Accept an optional `policy` parameter so the router can incorporate policy context signals. Return `RouteDecision` with populated `signals` and `score`.

```python
async def choose_target_with_reason(
    self,
    prompt: str,
    request: ChatCompletionRequest,
    routing_mode: RoutingMode = "auto",
    policy: TenantPolicy | None = None,
) -> RouteDecision:
```

The existing call in `PolicyService.resolve()` at line 49 passes `routing_mode=policy.routing_mode_default` — this call site needs updating to also pass `policy=policy`.

#### Seam 3: `PolicyService.resolve()` — pass policy to router

**Current call (line 49):**
```python
route_decision = await router_service.choose_target_with_reason(
    prompt,
    request,
    routing_mode=policy.routing_mode_default,
)
```

**Required change:** Add `policy=policy` to this call.

```python
route_decision = await router_service.choose_target_with_reason(
    prompt,
    request,
    routing_mode=policy.routing_mode_default,
    policy=policy,
)
```

#### Seam 4: `UsageLedgerRecord` + `UsageLedgerModel` + migration

**Current `UsageLedgerRecord` (governance.py:88-106):** No `route_signals` field.

**Required changes:**
1. Add `route_signals: dict[str, Any] | None = None` to `UsageLedgerRecord` (Pydantic model)
2. Add `route_signals_json: dict | None = mapped_column(JSON, nullable=True)` to `UsageLedgerModel` (SQLAlchemy model)
3. Update `GovernanceStore.record_usage()` to pass `route_signals` to the model
4. Update `GovernanceStore._usage_from_model()` to read `route_signals_json`
5. Add Alembic migration: `ADD COLUMN route_signals JSON NULL` on `usage_ledger`

**Migration pattern to follow** (from `20260315_0001`):
```python
# Idempotent guard — existing migration style
inspector = sa.inspect(bind)
columns = {col["name"] for col in inspector.get_columns("usage_ledger")}
if "route_signals" not in columns:
    op.add_column("usage_ledger", sa.Column("route_signals", sa.JSON(), nullable=True))
```

**Where `route_signals` is populated in `ChatService`:**
`ChatService._record_usage()` (line 832) constructs `UsageLedgerRecord`. Currently it takes `metadata: CompletionMetadata` which carries `route_reason`. The `route_signals` payload needs to be carried from `RouteDecision` through `PolicyResolution` → `CompletionMetadata` → `_record_usage()`.

Two options: (a) add `route_signals` to `CompletionMetadata`, or (b) extract it from the `PolicyResolution.route_decision.signals` directly in `_record_usage`. Option (b) is simpler — `PolicyResolution` already carries `route_decision`, and `metadata` has everything else. However, `_record_usage` does not currently receive `policy_resolution` — it receives `metadata` which is derived from it. The cleanest path: add `route_signals: dict[str, Any] | None = None` to `CompletionMetadata` and populate it from `route_decision.signals` in `ChatService._metadata()`.

#### Seam 5: `_nebula_headers()` — extend `X-Nebula-Route-Reason` header

**Current** (`api/routes/chat.py:51-61`):
```python
def _nebula_headers(metadata) -> dict[str, str]:
    return {
        ...
        "X-Nebula-Route-Reason": metadata.route_reason,
        ...
    }
```

The existing `X-Nebula-Route-Reason` header carries the raw reason string. The decision is to extend this header — not add a new one. Options: serialize top signal as `reason:signal_key=value`, or add a separate `X-Nebula-Route-Score` header. Based on CONTEXT.md ("existing `X-Nebula-Route` header extended with reason + top signal summary — keeps header count stable"), the cleanest approach is to add `X-Nebula-Route-Score` as a companion float header (one header, the score) and keep `X-Nebula-Route-Reason` as the structured reason code. This stays within "header count stable" because it replaces nothing.

**Alternatively**, `CompletionMetadata` grows a `route_score: float = 0.0` field and `_nebula_headers` serializes it.

#### Seam 6: Console `LedgerRequestDetail` + `UsageLedgerRecord` TypeScript type

**Current TypeScript type** (`console/src/lib/admin-api.ts:110-128`):
```typescript
export type UsageLedgerRecord = {
  // ... existing fields
  route_reason: string | null;
  policy_outcome: string | null;
  // NO route_signals field
};
```

**Required changes:**
1. Add `route_signals: Record<string, unknown> | null` to `UsageLedgerRecord` TypeScript type
2. Extend `LedgerRequestDetail` component to render a "Route Decision" section when `route_signals` is present
3. The backend admin API route that serializes `UsageLedgerRecord` to JSON must also include `route_signals`

**Admin API serialization:** Check `src/nebula/api/routes/admin.py` — it uses `UsageLedgerRecord` Pydantic model which auto-serializes. Adding the field to the Pydantic model is sufficient.

**Console component pattern** (from `ledger-request-detail.tsx`):
- Existing drawer uses a `<dl>` grid of `<DetailRow>` elements
- "Route Decision" section should be a new `<section>` below the existing `<dl>`, rendered conditionally when `entry.route_signals !== null`
- Plain-language labels: `DetailRow label="Token count"` not `DetailRow label="token_count"`
- Existing test style (from `ledger-request-detail.test.tsx`): `renderWithProviders`, `screen.getByText()`, `screen.queryByText()` for negative assertions

---

## Token Estimation Approach

`PolicyService._estimate_text_tokens()` (line 206) already implements `ceil(len(content) / 4)` — a chars/4 heuristic. This is exactly what S01 should reuse for the token count signal. It is already available and tested implicitly through `estimate_usage()` and `_estimate_request_cost()`.

**Why no tiktoken:** `tiktoken` is not in `pyproject.toml`. Adding it would require a Rust-compiled wheel, adds ~5MB, and the extra precision does not meaningfully improve routing decisions given that signal thresholds are configurable heuristics anyway. The chars/4 approximation is a defensible estimate for complexity tiering.

**What the router should call:** The router does not have access to `PolicyService`, but the chars/4 formula is trivial enough to inline or extract to a shared utility function. The planner should decide: inline `ceil(len(prompt) / 4)` in `RouterService`, or extract `estimate_token_count(text: str) -> int` as a small module-level function.

---

## Signal Model Design

### Recommended Signal Structure

Based on CONTEXT.md decisions and the code analysis, the 3-4 signals and their sources:

| Signal | Source | Type | Reason Code Contribution |
|--------|--------|------|--------------------------|
| `token_count` | `ceil(len(prompt) / 4)` | int | `token_complexity` |
| `complexity_tier` | threshold on token_count | `"low"/"medium"/"high"` | drives local vs. premium decision |
| `budget_proximity` | `(spend / soft_budget_usd)` ratio, or `None` if no budget set | float or None | `policy_budget_advisory` |
| `model_constraint` | whether `allowed_premium_models` restricts routing | bool | `policy_model_constraint` |

### Scoring Formula (defensible starting point)

Score drives the routing outcome probability, not a hard threshold. A simple linear formula:

```
score = token_score + policy_penalty
```

Where:
- `token_score = token_count / token_threshold` (normalized; > 1.0 suggests premium)
- `policy_penalty = 0.2 if soft_budget_proximity > 0.8 else 0.0`

The score is stored but does not override the routing logic — the decision still follows the explicit reason-code path. Score is an audit artifact for S02 simulation replay.

### Reason Code Vocabulary

Existing reason codes in `router_service.py`:
- `"explicit_local_model"` — model explicitly requested as local
- `"explicit_premium_model"` — model explicitly requested as non-default, non-local
- `"policy_local_only"` — routing mode is `local_only`
- `"policy_premium_only"` — routing mode is `premium_only`
- `"simple_prompt"` — char count below threshold, no complexity hints
- `"complexity_hint"` — keyword match
- `"prompt_length"` — char count above threshold

**New codes for S01:**
- `"token_complexity"` — token estimate above threshold (replaces `"prompt_length"` and `"simple_prompt"`)
- `"policy_budget_advisory"` — soft budget exceeded, prefer local
- `"policy_model_constraint"` — allowed_premium_models restricts available routes

Existing codes for explicit model and policy mode overrides do not need changing — they fire before heuristics and do not benefit from signal scoring.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Token estimation | tiktoken integration, BPE tokenizer | Inline `ceil(len(text) / 4)` — already in `policy_service.py:206` |
| JSON column in SQLAlchemy | Custom serialization | `sa.JSON()` — already imported in `db/models.py:6` |
| Signal serialization | Custom encoder | `dict[str, Any]` + Pydantic's built-in JSON serialization |
| Alembic migration guard | Table-drop-recreate | Idempotent `if column not in columns` pattern from existing migrations |

---

## Common Pitfalls

### Pitfall 1: Frozen dataclass + mutable default
**What goes wrong:** `RouteDecision` is `@dataclass(frozen=True)`. Adding `signals: dict[str, Any] = {}` raises `ValueError: mutable default is not allowed for field`.
**How to avoid:** Use `field(default_factory=dict)` from `dataclasses`. Every existing call site `RouteDecision(target=..., reason=...)` remains valid.

### Pitfall 2: `PolicyService` computes budget proximity AFTER calling router
**What goes wrong:** `PolicyService.resolve()` calls `router_service.choose_target_with_reason()` first (line 49), then computes `soft_budget_exceeded` (line 62). If the router needs budget proximity as a signal input, it must receive that context via a parameter — it cannot read it from the store itself.
**How to avoid:** The router receives `policy: TenantPolicy | None`. The `PolicyService` computes `tenant_spend_total` and passes the current spend alongside the policy budget limit as a pre-computed value, or passes the raw policy and the router does a lightweight ratio with `store` not available. Cleanest: pass `budget_spend_ratio: float | None` computed in `PolicyService` before calling the router. Or: reorder — compute spend first, pass into router.

### Pitfall 3: `CompletionMetadata` is not frozen, but `RouteDecision` is
**What goes wrong:** `CompletionMetadata` is `@dataclass(slots=True)` without `frozen=True` (line 42 of `chat_service.py`). Adding fields is safe here. But `RouteDecision` is frozen — all changes to it must use `field(default_factory=...)`.

### Pitfall 4: Admin API admin route needs `route_signals` in its response serialization
**What goes wrong:** The Pydantic `UsageLedgerRecord` model auto-serializes all fields. But if the column name in the SQLAlchemy model is `route_signals_json` (following the existing pattern for JSON columns: `metadata_json`, `allowed_premium_models_json`) and the Pydantic field is `route_signals`, the `_usage_from_model()` mapper must explicitly map `row.route_signals_json` → `route_signals`.
**How to avoid:** Check `GovernanceStore._usage_from_model()` — all other JSON columns (e.g., `metadata_json`) are already remapped. Follow the same explicit mapping pattern.

### Pitfall 5: Console TypeScript type must add `route_signals` before the component can use it
**What goes wrong:** `LedgerRequestDetail` receives `entry: UsageLedgerRecord`. If `route_signals` is not in the TypeScript type, TypeScript won't compile the property access.
**How to avoid:** Update `admin-api.ts` UsageLedgerRecord type first, then update the component. Update the test fixture to include `route_signals` so the test covers the new section rendering.

### Pitfall 6: Existing reason codes `"simple_prompt"` and `"prompt_length"` should be preserved or explicitly superseded
**What goes wrong:** If S01 replaces all reason codes wholesale, existing tests in `test_response_headers.py` and `test_service_flows.py` will break on reason assertions.
**How to avoid:** Map old char-count paths to new token-count equivalents. `"prompt_length"` → `"token_complexity"` is a clean rename; `"simple_prompt"` → `"token_complexity"` with a low score. Explicitly update any test that asserts on reason codes.

---

## Integration Points (Precise)

### Backend seam map

| File | Line(s) | Change |
|------|---------|--------|
| `src/nebula/services/router_service.py` | 11-13 | Add `signals: dict[str, Any]`, `score: float` to `RouteDecision` |
| `src/nebula/services/router_service.py` | 24-46 | Add `policy` param; compute token estimate, policy signals; populate `signals` and `score` on every return path |
| `src/nebula/services/policy_service.py` | 49-53 | Pass `policy=policy` to `choose_target_with_reason()` call; optionally pre-compute spend ratio |
| `src/nebula/services/chat_service.py` | 42-51 | Add `route_signals: dict[str, Any] | None` to `CompletionMetadata` |
| `src/nebula/services/chat_service.py` | 875-895 | Populate `route_signals=route_decision.signals` in `_metadata()` |
| `src/nebula/services/chat_service.py` | 832-873 | Pass `route_signals=metadata.route_signals` to `UsageLedgerRecord(...)` in `_record_usage()` |
| `src/nebula/models/governance.py` | 88-106 | Add `route_signals: dict[str, Any] | None = None` to `UsageLedgerRecord` |
| `src/nebula/db/models.py` | 144-164 | Add `route_signals_json: dict | None = mapped_column(JSON, nullable=True)` to `UsageLedgerModel` |
| `src/nebula/services/governance_store.py` | 272-296 | Pass `route_signals_json=record.route_signals` in `record_usage()` |
| `src/nebula/services/governance_store.py` | 393+ | Map `row.route_signals_json` → `route_signals` in `_usage_from_model()` |
| `src/nebula/api/routes/chat.py` | 51-61 | Add `X-Nebula-Route-Score: str(metadata.route_score)` to `_nebula_headers()` |
| `migrations/versions/` | new file | `ADD COLUMN route_signals JSON NULL` on `usage_ledger` |

### Console seam map

| File | Change |
|------|--------|
| `console/src/lib/admin-api.ts` | Add `route_signals: Record<string, unknown> \| null` to `UsageLedgerRecord` type |
| `console/src/components/ledger/ledger-request-detail.tsx` | Add conditional "Route Decision" section rendering `route_signals` with plain-language labels |
| `console/src/components/ledger/ledger-request-detail.test.tsx` | Add test case asserting "Route Decision" section renders with correct labels |

---

## Code Examples

### RouteDecision extension (frozen dataclass with mutable default)
```python
# Source: dataclasses stdlib docs + existing router_service.py pattern
from dataclasses import dataclass, field
from typing import Any, Literal

RouteTarget = Literal["local", "premium"]

@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str
    signals: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
```

### Token estimate signal computation (no new dependency)
```python
# Inline in RouterService — same formula as PolicyService._estimate_text_tokens()
from math import ceil

token_count = ceil(len(prompt) / 4)
token_threshold = self.settings.router_complexity_chars // 4  # reuse existing config
complexity_tier = (
    "high" if token_count > token_threshold * 1.5
    else "medium" if token_count > token_threshold
    else "low"
)
```

### Alembic migration pattern (from existing migrations)
```python
# Follow 20260315_0001 idempotent style
def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("usage_ledger")}
    if "route_signals" not in columns:
        op.add_column(
            "usage_ledger",
            sa.Column("route_signals", sa.JSON(), nullable=True),
        )

def downgrade() -> None:
    op.drop_column("usage_ledger", "route_signals")
```

### Console "Route Decision" section (extend LedgerRequestDetail)
```tsx
// Source: existing ledger-request-detail.tsx pattern
{entry.route_signals !== null && entry.route_signals !== undefined && (
  <div>
    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
      Route Decision
    </div>
    <dl className="mt-3 grid gap-3 sm:grid-cols-2">
      {entry.route_signals.token_count !== undefined && (
        <DetailRow
          label="Token count"
          value={`${entry.route_signals.token_count} (threshold: ${entry.route_signals.threshold ?? "N/A"})`}
        />
      )}
      {entry.route_signals.complexity_tier !== undefined && (
        <DetailRow label="Complexity tier" value={String(entry.route_signals.complexity_tier)} />
      )}
      {entry.route_signals.budget_proximity !== undefined && entry.route_signals.budget_proximity !== null && (
        <DetailRow
          label="Budget proximity"
          value={`${Math.round(Number(entry.route_signals.budget_proximity) * 100)}% of soft limit`}
        />
      )}
    </dl>
  </div>
)}
```

---

## State of the Art

| Old Approach | New Approach | What Changes |
|--------------|--------------|--------------|
| `len(prompt) < router_complexity_chars` threshold | `ceil(len(prompt)/4)` token estimate with tier classification | Same config setting reused; unit: tokens not chars |
| `reason: str` (single opaque string) | `reason: str` + `signals: dict[str, Any]` + `score: float` | Reason code is still the routing decision; signals are the audit record |
| `route_reason TEXT` in ledger | `route_reason TEXT` + `route_signals JSON` in ledger | Additive — existing queries unaffected |
| No signal visibility in Observability | "Route Decision" section in request detail drawer | Extends existing component, no new page |

**The current heuristic this replaces:**
```python
# Current router_service.py lines 40-46
complexity_hints = ("analyze", "reason", "contract", "debug", "architecture", "design")
contains_complexity_hint = any(hint in prompt.lower() for hint in complexity_hints)
if len(prompt) < self.settings.router_complexity_chars and not contains_complexity_hint:
    return RouteDecision(target="local", reason="simple_prompt")
if contains_complexity_hint:
    return RouteDecision(target="premium", reason="complexity_hint")
return RouteDecision(target="premium", reason="prompt_length")
```

The new heuristic replaces the three `len(prompt)` branches. The keyword-hint branch (`complexity_hint`) is a valid signal and should be preserved as one input within the signal model rather than eliminated. The policy-override branches (`explicit_local_model`, `explicit_premium_model`, `policy_local_only`, `policy_premium_only`) are unaffected — they short-circuit before heuristics and still fire first.

---

## Open Questions

1. **Budget proximity computation timing**
   - What we know: `PolicyService.resolve()` currently computes `soft_budget_exceeded` at line 62, after calling the router at line 49.
   - What's unclear: Should `PolicyService` pre-compute `spend_ratio` and pass it to the router, or should the router receive the raw `TenantPolicy` and let `PolicyService` tell it the current spend as a separate parameter?
   - Recommendation: Add `current_spend_usd: float | None = None` parameter to `choose_target_with_reason()`. `PolicyService` computes `tenant_spend_total()` before calling the router, passes it in. This avoids giving the router a DB dependency.

2. **Keyword hints — preserve or absorb into signal model?**
   - What we know: The six complexity keywords (`analyze`, `reason`, `contract`, `debug`, `architecture`, `design`) are in the current heuristic.
   - What's unclear: Should they become a signal (`has_complexity_keywords: bool`) or be dropped in favor of token count alone?
   - Recommendation: Preserve as `keyword_match: bool` signal. It is a valid independent signal and removing it would change routing behavior for existing users without evidence it is harmful.

3. **`route_signals` in denied requests**
   - What we know: When policy denies a request, `chat_service.py` records usage at line 804-821 using a hardcoded `UsageLedgerRecord(...)` without metadata from `PolicyResolution.route_decision`.
   - What's unclear: Should denied requests also carry `route_signals`?
   - Recommendation: Yes — the router ran before denial, so the `route_decision.signals` are valid. Extract the signals from the `HTTPException` headers path or from the `PolicyResolution` object. This is a small addition to the denial-recording path.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest with pytest-asyncio (auto mode) |
| Config file | `pyproject.toml` (pytest section) |
| Quick run command | `pytest tests/test_router_signals.py -x` (new file) |
| Full suite command | `make test` |
| Console quick run | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R039 | `RouteDecision` carries `signals` dict and `score` float | unit | `pytest tests/test_router_signals.py::test_route_decision_carries_signals -x` | Wave 0 |
| R039 | Token count signal is computed from prompt length | unit | `pytest tests/test_router_signals.py::test_token_count_signal_from_prompt -x` | Wave 0 |
| R039 | Policy context signals populated when policy has soft budget | unit | `pytest tests/test_router_signals.py::test_budget_proximity_signal -x` | Wave 0 |
| R039 | Model constraint signal populated when allowed_premium_models is set | unit | `pytest tests/test_router_signals.py::test_model_constraint_signal -x` | Wave 0 |
| R039 | Score reflects complexity tier (low/medium/high) | unit | `pytest tests/test_router_signals.py::test_score_by_complexity_tier -x` | Wave 0 |
| R039 | Full path: signals recorded in ledger for a real request | integration | `pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger -x` | Wave 0 |
| R039 | `X-Nebula-Route-Score` header present in response | integration | `pytest tests/test_router_signals.py::test_route_score_header -x` | Wave 0 |
| R039 | Console drawer renders "Route Decision" section with token count label | console unit | `npm --prefix console run test -- --run ledger-request-detail.test.tsx` | Wave 0 |

### Unit Test Patterns to Follow

**Pattern for RouterService unit tests** (from `test_service_flows.py`):
```python
# Direct RouterService instantiation — no app needed
from nebula.core.config import Settings
from nebula.services.router_service import RouterService, RouteDecision
from nebula.models.openai import ChatCompletionRequest
from nebula.models.governance import TenantPolicy

def make_settings(**overrides) -> Settings:
    # Use minimal Settings; router_complexity_chars controls threshold
    ...

async def test_token_count_signal_from_prompt():
    service = RouterService(settings=make_settings())
    request = ChatCompletionRequest(model="nebula-auto", messages=[...])
    decision = await service.choose_target_with_reason("short prompt", request)
    assert "token_count" in decision.signals
    assert isinstance(decision.signals["token_count"], int)
    assert decision.score >= 0.0
```

**Pattern for integration test** (from `test_governance_api.py` / `test_response_headers.py`):
```python
def test_route_signals_persisted_in_ledger() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=auth_headers(),
                json={"model": "nebula-auto", "messages": [{"role": "user", "content": "short"}]},
            )
            ledger = client.get("/v1/admin/usage/ledger", headers=admin_headers())
            record = ledger.json()[0]
            assert record["route_signals"] is not None
            assert "token_count" in record["route_signals"]
```

### Migration Verification

The `configured_app()` helper in `tests/support.py` runs `alembic upgrade head` before each test run (line 129-134). Adding the new migration to `migrations/versions/` is sufficient — it will be applied automatically in test runs. Verify:
- `route_signals` column present after `alembic upgrade head`
- Downgrade removes the column cleanly
- Old rows without `route_signals` still deserialize correctly (nullable column, `None` default in Pydantic model)

### Observability Console Assertions

The vitest test for `LedgerRequestDetail` (`ledger-request-detail.test.tsx`) follows this pattern:

```tsx
// New test case to add
it("renders Route Decision section when route_signals present", () => {
  renderWithProviders(
    <LedgerRequestDetail
      entry={{
        ...baseEntry,
        route_signals: {
          token_count: 842,
          threshold: 500,
          complexity_tier: "medium",
          budget_proximity: 0.72,
          keyword_match: false,
        },
      }}
    />,
  );

  expect(screen.getByText("Route Decision")).toBeInTheDocument();
  expect(screen.getByText("Token count")).toBeInTheDocument();
  expect(screen.getByText(/842/)).toBeInTheDocument();
  expect(screen.getByText("Complexity tier")).toBeInTheDocument();
  expect(screen.getByText("medium")).toBeInTheDocument();
  expect(screen.getByText("Budget proximity")).toBeInTheDocument();
});

it("does not render Route Decision section when route_signals is null", () => {
  renderWithProviders(<LedgerRequestDetail entry={{ ...baseEntry, route_signals: null }} />);
  expect(screen.queryByText("Route Decision")).not.toBeInTheDocument();
});
```

### Sampling Rate
- **Per task commit:** `pytest tests/test_router_signals.py -x && npm --prefix console run test -- --run ledger-request-detail.test.tsx`
- **Per wave merge:** `make test && make console-test`
- **Phase gate:** Full suite green before close-out

### Wave 0 Gaps

- [ ] `tests/test_router_signals.py` — all signal unit tests + integration test (new file, does not yet exist)
- [ ] Console `ledger-request-detail.test.tsx` — new test cases for "Route Decision" section (extend existing file)
- [ ] `migrations/versions/YYYYMMDD_0006_route_signals.py` — new migration file

*(Existing test infrastructure: `configured_app()`, `StubProvider`, `FakeCacheService`, `auth_headers()`, `admin_headers()`, `renderWithProviders` — all available, no new framework setup required.)*

---

## Sources

### Primary (HIGH confidence)

All findings are from direct codebase inspection:

- `src/nebula/services/router_service.py` — current `RouteDecision` and `RouterService` implementation
- `src/nebula/services/policy_service.py` — `PolicyService.resolve()` call chain, `_estimate_text_tokens()` heuristic
- `src/nebula/services/chat_service.py` — `CompletionMetadata`, `_record_usage()`, `_metadata()` full flow
- `src/nebula/api/routes/chat.py` — `_nebula_headers()` header construction
- `src/nebula/models/governance.py` — `TenantPolicy`, `UsageLedgerRecord` Pydantic models
- `src/nebula/db/models.py` — `UsageLedgerModel` SQLAlchemy model
- `src/nebula/services/governance_store.py` — `record_usage()`, `_usage_from_model()` mapping
- `migrations/versions/20260315_0001_governance_baseline.py` — migration pattern (idempotent guards)
- `console/src/components/ledger/ledger-request-detail.tsx` — drawer component structure
- `console/src/lib/admin-api.ts` — `UsageLedgerRecord` TypeScript type
- `console/src/components/ledger/ledger-request-detail.test.tsx` — console test patterns
- `tests/support.py` — test helper patterns (`configured_app`, `StubProvider`, etc.)

### Secondary (MEDIUM confidence)

- Python `dataclasses` stdlib documentation — frozen dataclass `field(default_factory=...)` behavior
- SQLAlchemy docs — `JSON` column type, nullable column behavior with existing rows

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, all capability is already present in the codebase
- Architecture: HIGH — all six seams identified from direct code reading, exact line numbers provided
- Migration pattern: HIGH — follows idempotent pattern from existing migration exactly
- Token estimation: HIGH — formula already exists in `policy_service.py:206`, reuse confirmed
- Console extension: HIGH — component structure fully read, test pattern established
- Signal scoring formula: MEDIUM — thresholds are heuristic; the specific formula is Claude's discretion per CONTEXT.md

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable codebase, no fast-moving external dependencies)
