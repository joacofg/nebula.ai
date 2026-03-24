---
estimated_steps: 4
estimated_files: 5
skills_used:
  - test
---

# T02: Expose embeddings request explanation fields in the ledger detail surface

**Slice:** S04 — Durable evidence correlation
**Milestone:** M003

## Description

Once an operator can find an embeddings row, the selected detail view must show enough durable metadata to explain what happened for that same request. This task should stay strictly inside already-persisted usage-ledger fields and make the request-detail card more explicit about identity, route, model, and outcome. The UI should help an operator correlate the request from S03 without introducing any new persistence, payload capture, or embeddings-specific backend schema.

## Steps

1. Read `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-table.tsx`, and `console/src/lib/admin-api.ts` to identify which persisted `UsageLedgerRecord` fields are already available but not shown.
2. Expand the request-detail card to render the persisted explanation fields most relevant to embeddings correlation: request id, timestamp, tenant, route target, terminal status, requested model, response model, provider, route reason, policy outcome, and the existing fallback/cache/token metadata.
3. Keep the row-selection/table behavior coherent for the richer detail view, adjusting `console/src/components/ledger/ledger-table.tsx` only if needed to preserve clear selection and embeddings-row discoverability.
4. Add or extend focused component coverage in `console/src/components/ledger/ledger-request-detail.test.tsx` and `console/src/components/ledger/ledger-table.test.tsx` so the visible explanation contract is locked and raw payload fields remain absent.

## Must-Haves

- [ ] `console/src/components/ledger/ledger-request-detail.tsx` renders the persisted identity, route, model, and outcome fields needed to explain an embeddings request from the usage-ledger row alone.
- [ ] Component tests lock the detail/table contract and do not introduce any display of raw `input` text or embedding vectors.

## Verification

- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`
- `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx`
- `! rg -n 'input|embedding\"|embeddings\"' console/src/components/ledger/ledger-request-detail.tsx console/src/components/ledger/ledger-request-detail.test.tsx console/src/lib/admin-api.ts -S`

## Observability Impact

- Signals added/changed: the request-detail surface now exposes durable identity/context fields needed to explain embeddings outcomes from the existing ledger row.
- How a future agent inspects this: select a row in Observability or run the focused component tests to see which persisted metadata is intentionally presented to operators.
- Failure state exposed: regressions where the detail card hides route/model/outcome context or starts surfacing redacted payload data become explicit test failures.

## Inputs

- `console/src/components/ledger/ledger-request-detail.tsx` — current narrow detail card that omits key persisted identity/context fields.
- `console/src/components/ledger/ledger-table.tsx` — current row inventory and selection surface feeding the detail pane.
- `console/src/components/ledger/ledger-table.test.tsx` — existing selection coverage to preserve while the detail contract expands.
- `console/src/lib/admin-api.ts` — source of truth for the existing `UsageLedgerRecord` shape.
- `console/src/app/(console)/observability/page.tsx` — page composition for table + request-detail selection behavior.

## Expected Output

- `console/src/components/ledger/ledger-request-detail.tsx` — richer metadata-only request explanation card.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — new focused coverage for embeddings-relevant request detail fields.
- `console/src/components/ledger/ledger-table.tsx` — preserved or minimally improved row selection/display to support the detail flow.
- `console/src/components/ledger/ledger-table.test.tsx` — updated regression coverage for row selection/display.
- `console/src/lib/admin-api.ts` — preserved shared ledger record shape used by the UI and tests.
