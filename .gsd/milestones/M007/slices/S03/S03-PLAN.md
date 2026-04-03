# S03: Rework Observability around a primary investigation flow

**Goal:** Rework Observability so one selected request reads as the clear primary investigation flow, with request detail staying authoritative and every supporting card visibly subordinate to that investigation and its implied next step.
**Demo:** After this: After this: an operator can open Observability and immediately understand one selected request as the lead investigation object, with all other cards clearly supporting that investigation.

## Tasks
- [x] **T01: Reworked Observability into a selected-request-first investigation flow with explicit policy-preview follow-up sections and hierarchy-locking tests.** — Rework `console/src/app/(console)/observability/page.tsx` so the selected request is the page’s obvious lead object and the rest of the page reads as follow-up context for that investigation. Keep the existing data sources, preserve `LedgerRequestDetail` as the authoritative persisted evidence seam, and tighten the page-level structure so the next action is legible through layout and section sequencing rather than copy alone.

Steps:
1. Recompose the top-level Observability page layout in `console/src/app/(console)/observability/page.tsx` around one investigation-first flow that leads with selected-request inspection, keeps request detail authoritative, and regroups supporting cards as follow-up context for the same request.
2. Update `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` to assert DOM order, scoped supporting-card hierarchy, explicit policy-preview follow-up cues, and negative guards against dashboard/routing-studio/analytics drift.
3. Keep `console/src/components/ledger/ledger-request-detail.tsx` stable unless the new flow exposes a small wording mismatch; if touched, preserve its authoritative persisted-record contract and keep focused coverage aligned.

Must-haves:
- The selected request remains the lead investigation object and `LedgerRequestDetail` still reads as the authoritative persisted evidence row.
- Recommendations, calibration, cache, and dependency sections are explicitly subordinate follow-up context for the selected request.
- The page structure makes the next operator action legible and keeps policy preview as the follow-up comparison surface.
- Focused page tests lock hierarchy and anti-drift boundaries with scoped assertions rather than copy-only snapshots.

Verification:
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`
- `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx`

Observability Impact:
- Signals added/changed: the selected-request-first UI hierarchy and its policy-preview follow-up cues become the primary inspection signal on the page.
- How a future agent inspects this: read `console/src/app/(console)/observability/page.tsx` and rerun the focused Observability Vitest files.
- Failure state exposed: hierarchy drift, duplicate-label scoping mistakes, or dashboard-language regressions fail in focused page tests instead of surfacing only as subjective UI review.
  - Estimate: 75m
  - Files: console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/components/ledger/ledger-request-detail.tsx, console/src/components/ledger/ledger-request-detail.test.tsx
  - Verify: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx
- [ ] **T02: Tighten request-selection affordances without widening the surface** — If the page restructure alone still leaves request selection too passive, strengthen `console/src/components/ledger/ledger-table.tsx` so the chosen request is easier to recognize as the lead investigation object. Keep the table bounded: improve selection affordance, request recognition, and integration with the page flow without turning it into a new explorer or analytics surface.

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
  - Estimate: 45m
  - Files: console/src/components/ledger/ledger-table.tsx, console/src/components/ledger/ledger-table.test.tsx, console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx
  - Verify: npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx
