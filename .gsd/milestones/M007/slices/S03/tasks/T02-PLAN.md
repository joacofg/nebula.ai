---
estimated_steps: 15
estimated_files: 5
skills_used: []
---

# T02: Tighten request-selection affordances without widening the surface

If the page restructure alone still leaves request selection too passive, strengthen `console/src/components/ledger/ledger-table.tsx` so the chosen request is easier to recognize as the lead investigation object. Keep the table bounded: improve selection affordance, request recognition, and integration with the page flow without turning it into a new explorer or analytics surface.

Steps:
1. Update `console/src/components/ledger/ledger-table.tsx` to make selected-request state more legible through bounded row affordances, labels, or structural hints that reinforce investigation-first behavior.
2. Extend `console/src/components/ledger/ledger-table.test.tsx` to assert the improved selection cues and preserve existing row discoverability/anti-drift expectations.
3. If the stronger table affordance changes page integration, update `console/src/app/(console)/observability/page.tsx` and its focused tests so page-level assertions continue to describe one request-led investigation flow.

Must-haves:
- The selected row is easier to recognize as the current investigation target.
- The table remains a bounded selector for the primary request, not a new dashboard/explorer surface.
- Focused table and page tests prove the affordance without weakening request-detail authority or supporting-card hierarchy.

Verification:
- `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`

Observability Impact:
- Signals added/changed: selected-row cues in the request list make the current investigation target obvious before opening request detail.
- How a future agent inspects this: inspect `console/src/components/ledger/ledger-table.tsx` and rerun the focused table plus Observability page tests.
- Failure state exposed: weak or regressed selection cues fail in focused table/page tests rather than relying on manual visual interpretation.

## Inputs

- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`

## Expected Output

- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`

## Verification

npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx

## Observability Impact

Selected-request affordance becomes a durable inspection cue on the page.
