# Policy guardrails

Nebula exposes two budget-oriented policy surfaces for operators:

- **Hard cumulative budget controls** change live routing behavior once tenant premium spend reaches a configured limit.
- **Soft budget advisory controls** add explanation metadata for operators but do not block or reroute requests.

This document stays inside the existing decisioning control-plane scope. It explains how routing decisions appear in policy preview, request detail, and simulation surfaces; it does **not** introduce a billing, chargeback, or analytics subsystem.

## Hard cumulative budget controls

### Fields

- `hard_budget_limit_usd`
  - Cumulative premium spend threshold for the tenant.
  - When unset, no hard-budget enforcement runs.
- `hard_budget_enforcement`
  - `downgrade`: compatible auto-routed traffic is downgraded to local after the limit is exhausted.
  - `deny`: premium traffic is denied once the limit is exhausted.

### Runtime behavior

When `hard_budget_limit_usd` is reached or exceeded:

1. Nebula calculates the tenant's cumulative premium spend at decision time.
2. If the request is compatible with local downgrade, Nebula may route it to local with reason code `hard_budget_downgrade`.
3. If the request explicitly requires premium routing, or downgrade is not allowed, Nebula denies premium routing with a stable operator-readable explanation.

### Operator-visible explanation vocabulary

Hard-budget outcomes show up in request detail, simulation diffs, and response headers through these stable fragments:

- `hard_budget=exceeded(limit_usd=…,spent_usd=…,enforcement=…)`
- `budget_action=downgraded_to_local`
- `denied=Tenant hard budget limit reached; premium routing is blocked (spent_usd=…, limit_usd=…).`

These strings explain **why** routing changed; they are not a separate financial reporting interface.

## Soft budget advisory control

### Field

- `soft_budget_usd`
  - Advisory threshold only.
  - When cumulative spend crosses this value, Nebula adds policy outcome metadata for operator visibility.

### Runtime behavior

Soft budget exceedance does **not**:

- deny a request
- downgrade a request
- force local routing on its own

Instead, it marks the request with `soft_budget=exceeded` so operators can see that the advisory threshold was crossed.

## Where operators inspect these outcomes

### Policy page

The Policy page separates controls into:

- **Runtime-enforced controls** for routing mode, allowlists, per-request spend limits, and hard cumulative budget behavior.
- **Soft budget advisory** for the non-blocking budget signal.

This keeps hard guardrails visibly distinct from advisory spend metadata.

### Preview before save

Policy preview replays recent ledger-backed traffic without saving the draft policy. Operators can inspect:

- changed routes
- newly denied requests
- changed policy outcomes
- premium cost delta for the replay window

This gives operators a controlled explanation loop before they commit a policy change.

### Usage ledger request detail

The request-detail drawer keeps the raw `policy_outcome` field for audit continuity, then adds labeled budget evidence when relevant:

- summary of the budget outcome
- hard budget limit and spent amount at decision time
- enforcement mode
- downgrade action or denial reason
- soft-budget advisory status when applicable

This keeps operators out of raw JSON spelunking while preserving the original persisted value.

## Scope boundary

R044 scope discipline for this slice is:

- explain routing and guardrail outcomes already produced by Nebula
- preserve stable vocabulary across runtime, simulation, and operator UI
- avoid adding billing dashboards, spend forecasting, or new external control-plane responsibilities

If future work needs billing or cross-tenant financial analytics, that should be planned as a separate milestone instead of expanding these decisioning surfaces implicitly.
