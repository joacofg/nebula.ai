---
task: T03
title: Observability drawer extension and route-decision vocabulary doc
wave: 2
depends_on:
  - T01
  - T02
files_modified:
  - console/src/lib/admin-api.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - docs/route-decision-vocabulary.md
requirements:
  - R039
autonomous: true
---

# T03: Observability drawer extension and route-decision vocabulary doc

**Slice:** S01 — Adaptive routing model
**Milestone:** M005

## Goal

Surface the `route_signals` payload recorded by T02 in the Observability request-detail drawer using plain-language labels, extend the TypeScript type contract, and write `docs/route-decision-vocabulary.md` so S02 simulation can reference a stable decision model.

## Context

T01 added `signals` and `score` to `RouteDecision`. T02 persisted them in `usage_ledger.route_signals` and exposed them through the admin API via `UsageLedgerRecord.route_signals`. T03 closes the operator visibility loop: extending the TypeScript type, rendering a "Route Decision" section in the drawer, and documenting the vocabulary.

**Signal keys to display (from T01 output):**

| Key | Plain-language label |
|-----|----------------------|
| `token_count` | Token count |
| `complexity_tier` | Complexity tier |
| `keyword_match` | Keyword match |
| `model_constraint` | Model constraint |
| `budget_proximity` | Budget proximity |

**Reason codes to document (from T01 output):**

| Code | Meaning |
|------|---------|
| `token_complexity` | Route chosen based on estimated token count and complexity tier |
| `policy_budget_advisory` | Local route preferred because soft budget threshold is near |
| `policy_model_constraint` | Routing constrained by `allowed_premium_models` policy field |
| `explicit_local_model` | Caller explicitly requested a local model |
| `explicit_premium_model` | Caller explicitly requested a non-local model |
| `policy_local_only` | Routing mode is `local_only` |
| `policy_premium_only` | Routing mode is `premium_only` |

## Must-Haves

- `route_signals: Record<string, unknown> | null` added to `UsageLedgerRecord` TypeScript type in `admin-api.ts`
- `LedgerRequestDetail` conditionally renders a "Route Decision" `<section>` when `entry.route_signals !== null`
- Section uses existing `<DetailRow>` component with plain-language labels (not raw JSON key names)
- Section is absent (not rendered) when `entry.route_signals` is null or undefined
- Vitest test covers both the positive (section present with labels) and negative (section absent when null) cases
- `docs/route-decision-vocabulary.md` exists and documents all signal keys and reason codes
- TypeScript compiles without type errors after the change

## Tasks

<task id="1">
<title>Extend UsageLedgerRecord TypeScript type and update LedgerRequestDetail drawer</title>
<read_first>
- console/src/lib/admin-api.ts — full file; find UsageLedgerRecord type (lines 110-128 approx); note existing fields and import patterns
- console/src/components/ledger/ledger-request-detail.tsx — full file; understand the existing <dl>/<DetailRow> pattern, the component props interface, and how existing sections are conditionally rendered
- console/src/components/ledger/ledger-request-detail.test.tsx — full file; understand renderWithProviders helper, fixture shape, and existing assertion style (screen.getByText / screen.queryByText)
</read_first>
<action>
**Step 1 — Extend `UsageLedgerRecord` in `console/src/lib/admin-api.ts`:**

Find the `UsageLedgerRecord` type (currently ends at `policy_outcome: string | null`). Add one field after it:

```typescript
route_signals: Record<string, unknown> | null;
```

No other type changes are needed. The existing admin API route auto-serializes `UsageLedgerRecord` from the Python Pydantic model; adding this field here is sufficient.

**Step 2 — Add "Route Decision" section to `console/src/components/ledger/ledger-request-detail.tsx`:**

Below the existing `<dl>` grid (which contains the existing route/policy/provider detail rows), add a new `<section>` rendered conditionally:

```tsx
{entry.route_signals && (
  <section className="mt-4">
    <h4 className="text-sm font-semibold text-foreground mb-2">Route Decision</h4>
    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
      {entry.route_signals.token_count !== undefined && (
        <DetailRow label="Token count" value={String(entry.route_signals.token_count)} />
      )}
      {entry.route_signals.complexity_tier !== undefined && (
        <DetailRow label="Complexity tier" value={String(entry.route_signals.complexity_tier)} />
      )}
      {entry.route_signals.keyword_match !== undefined && (
        <DetailRow
          label="Keyword match"
          value={entry.route_signals.keyword_match ? "yes" : "no"}
        />
      )}
      {entry.route_signals.model_constraint !== undefined && (
        <DetailRow
          label="Model constraint"
          value={entry.route_signals.model_constraint ? "yes" : "no"}
        />
      )}
      {entry.route_signals.budget_proximity !== null &&
        entry.route_signals.budget_proximity !== undefined && (
          <DetailRow
            label="Budget proximity"
            value={`${Math.round(Number(entry.route_signals.budget_proximity) * 100)}%`}
          />
        )}
    </dl>
  </section>
)}
```

Use whatever className/styling conventions match the existing component. Check if `DetailRow` is imported at the top of the file — if it is a local sub-component rather than an import, follow the existing usage pattern exactly.

Do NOT add a new page or route. This is a new section inside the existing drawer only.

**Step 3 — Update the test fixture and add test cases in `console/src/components/ledger/ledger-request-detail.test.tsx`:**

The existing test fixture (`mockEntry` or similar) has a `UsageLedgerRecord`-shaped object. Add `route_signals: null` to the existing fixture (so existing tests pass without change).

Add two new `it` / `test` blocks:

```typescript
it("renders Route Decision section when route_signals is present", () => {
  const entryWithSignals = {
    ...mockEntry,
    route_signals: {
      token_count: 842,
      complexity_tier: "medium",
      keyword_match: false,
      model_constraint: false,
      budget_proximity: null,
    },
  };
  renderWithProviders(<LedgerRequestDetail entry={entryWithSignals} />);
  expect(screen.getByText("Route Decision")).toBeInTheDocument();
  expect(screen.getByText("Token count")).toBeInTheDocument();
  expect(screen.getByText("842")).toBeInTheDocument();
  expect(screen.getByText("Complexity tier")).toBeInTheDocument();
  expect(screen.getByText("medium")).toBeInTheDocument();
});

it("does not render Route Decision section when route_signals is null", () => {
  renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, route_signals: null }} />);
  expect(screen.queryByText("Route Decision")).not.toBeInTheDocument();
});
```

Adapt to the actual renderWithProviders call signature and component props as seen in the existing test file.
</action>
<acceptance_criteria>
- `grep -n "route_signals" console/src/lib/admin-api.ts` — returns a line containing `Record<string, unknown> | null`
- `grep -n "Route Decision" console/src/components/ledger/ledger-request-detail.tsx` — returns at least 1 match
- `grep -n "Token count" console/src/components/ledger/ledger-request-detail.tsx` — returns at least 1 match
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` exits 0
- `npm --prefix console run build 2>&1 | grep -i "error"` returns no TypeScript errors
</acceptance_criteria>
</task>

<task id="2">
<title>Write docs/route-decision-vocabulary.md</title>
<read_first>
- src/nebula/services/router_service.py — confirm the final reason codes and signal keys after T01 execution
- docs/ — list any existing docs to understand naming conventions and style
</read_first>
<action>
Create `docs/route-decision-vocabulary.md`. The document should be concise (no more than 100 lines) and cover:

1. **Purpose paragraph** — explain that S01 replaced the char-count heuristic with an explicit signal model, and that this doc is the stable vocabulary reference for S02 simulation and operator understanding.

2. **Signal reference table** with columns: Signal key, Type, Source, Plain-language meaning.
   - `token_count`: int, `ceil(len(prompt) / 4)`, "Estimated token count of the request prompt"
   - `complexity_tier`: "low" | "medium" | "high", threshold on token_count (<500, 500–2000, >2000), "Routing complexity band"
   - `keyword_match`: bool, keyword hint scan, "Whether the prompt contains a complexity-hint keyword"
   - `model_constraint`: bool, `policy.allowed_premium_models`, "Whether the tenant policy restricts available premium models"
   - `budget_proximity`: float | null, computed ratio if soft_budget_usd is set, "Fraction of soft budget already consumed (null if no budget is configured)"

3. **Score** — brief paragraph: score is a normalised float (0.0–1.0) computed as `min(token_count / 500, 1.0) + 0.1 if model_constraint`. It is an audit artifact for simulation replay, not a hard routing threshold.

4. **Reason code reference table** with columns: Reason code, Signals populated, Plain-language meaning.
   - `token_complexity` — all heuristic signals populated, "Route driven by token-count complexity tiering"
   - `policy_budget_advisory` — `budget_proximity` set, "Local route preferred because soft budget is near its limit"
   - `policy_model_constraint` — `model_constraint=true`, "Available premium models restricted by policy allowlist"
   - `explicit_local_model` — signals empty (override path), "Caller explicitly requested a local model by name"
   - `explicit_premium_model` — signals empty (override path), "Caller explicitly requested a non-local model"
   - `policy_local_only` — signals empty (override path), "Routing mode is local_only"
   - `policy_premium_only` — signals empty (override path), "Routing mode is premium_only"

5. **Stability note** — one sentence: "Signal keys and reason codes in this document are stable from S01 forward; S02 simulation depends on these names for ledger replay."
</action>
<acceptance_criteria>
- `test -f docs/route-decision-vocabulary.md` exits 0
- `grep -n "token_complexity" docs/route-decision-vocabulary.md` returns at least 1 match
- `grep -n "budget_proximity" docs/route-decision-vocabulary.md` returns at least 1 match
- `grep -n "complexity_tier" docs/route-decision-vocabulary.md` returns at least 1 match
- File is under 120 lines: `wc -l docs/route-decision-vocabulary.md | awk '{print $1}' | xargs -I{} test {} -le 120`
</acceptance_criteria>
</task>

## Verification

```bash
npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx
test -f docs/route-decision-vocabulary.md
```

Both commands exit 0.

## Inputs

- `console/src/lib/admin-api.ts` — TypeScript type to extend
- `console/src/components/ledger/ledger-request-detail.tsx` — drawer component to extend
- `console/src/components/ledger/ledger-request-detail.test.tsx` — test file to extend
- T01 output: `src/nebula/services/router_service.py` — confirms final signal keys and reason codes
- T02 output: `src/nebula/models/governance.py` `UsageLedgerRecord` — confirms `route_signals` field name

## Expected Output

- `console/src/lib/admin-api.ts` — `route_signals` field added to TypeScript type
- `console/src/components/ledger/ledger-request-detail.tsx` — "Route Decision" section with plain-language labels
- `console/src/components/ledger/ledger-request-detail.test.tsx` — two new test cases (positive and negative)
- `docs/route-decision-vocabulary.md` — new vocabulary reference doc

## Observability Impact

- Signals changed: Vitest failures now surface if the "Route Decision" section renders incorrectly, uses wrong labels, or renders when it should not.
- Inspection surfaces: `console/src/components/ledger/ledger-request-detail.tsx` for the section structure; `docs/route-decision-vocabulary.md` for the stable vocabulary.
- Failure visibility: exact `getByText` assertion failures on label strings; TypeScript compile errors on type mismatches.
