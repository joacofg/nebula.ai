# S03: Rework Observability around a primary investigation flow — UAT

**Milestone:** M007
**Written:** 2026-04-03T02:37:40.383Z

# S03: Rework Observability around a primary investigation flow — UAT

**Milestone:** M007
**Written:** 2026-04-01

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice is a bounded console-composition change with hierarchy and selector semantics locked by focused Vitest coverage. The decisive proof is the rendered page structure, selected-request affordances, and anti-drift assertions rather than a live backend behavior change.

## Preconditions

- `console/node_modules` is installed so Vitest can run.
- The worktree includes the S03 Observability page and ledger-table changes.
- The tester can run focused console tests from the repo root.

## Smoke Test

Run:

`npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx src/components/ledger/ledger-table.test.tsx`

**Expected:** All 5 test files pass, confirming that Observability still renders one authoritative request-detail investigation flow with supporting follow-up context and strengthened request-selection cues.

## Test Cases

### 1. Selected request leads the page investigation

1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`.
2. Inspect the assertions in the passing suite or review the rendered test output if debugging.
3. **Expected:** The page shows the selected-request section before follow-up context, `LedgerRequestDetail` remains the authoritative persisted evidence seam, and recommendations/calibration/cache/dependency cards are asserted as supporting context rather than peer dashboard panels.

### 2. Request detail stays authoritative while follow-up points to policy preview

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`.
2. Confirm the request-detail component still renders persisted route/provider/fallback/policy evidence for the selected request ID.
3. **Expected:** Request detail remains the primary persisted record, while page-level assertions confirm follow-up copy points operators toward policy preview as the next comparison surface instead of replacing the selected request evidence.

### 3. Ledger table acts as a bounded request selector

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx src/app/'(console)'/observability/page.test.tsx`.
2. Inspect the selected-row and unselected-row assertions.
3. **Expected:** The chosen row exposes `aria-selected`, the request button exposes a pressed state plus `Current investigation`, unselected rows retain a lighter `Select request` cue, and the table is still treated as the selector for the primary detail view rather than a second analysis surface.

### 4. Dependency health remains supporting runtime context

1. Run `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`.
2. Confirm dependency health is rendered within the supporting follow-up column.
3. **Expected:** Dependency health stays visible as runtime context for the same selected-request investigation and does not outrank the persisted ledger row or turn into a separate dashboard authority.

## Edge Cases

### Duplicate request IDs and labels appear across bounded cards

1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/observability-page.test.tsx`.
2. Review the scoped assertions around repeated request IDs or shared labels.
3. **Expected:** Tests pass by using scoped assertions or count-based expectations rather than assuming global uniqueness, proving the page can intentionally repeat identifiers across selector/detail/supporting contexts without false regressions.

### No row is expanded into a second detail surface

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx`.
2. Review the selected and unselected row copy.
3. **Expected:** The selected row strengthens recognition of the current investigation but still only promotes the request into the main detail panel below; it does not render a second independent investigation summary inside the table.

## Failure Signals

- Observability tests fail because supporting cards render before the selected request section.
- Request-detail tests fail because the authoritative persisted-evidence wording or routing fields drift.
- Ledger-table tests fail because `aria-selected`, pressed-button state, or `Current investigation` cues disappear.
- Page tests start asserting dashboard, analytics, or routing-studio language, indicating identity drift.

## Requirements Proved By This UAT

- R049 — The operator-surface refinement stays bounded and request-led rather than widening Nebula into an analytics-style dashboard or broader product sprawl.

## Not Proven By This UAT

- This UAT does not prove the full policy-preview comparison-and-decision flow planned for S04.
- This UAT does not exercise live backend/admin API changes; it verifies the assembled console hierarchy and selector semantics in focused component/page tests.

## Notes for Tester

If a test fails because the same request ID or label appears in more than one card, treat that as a scoping problem in the test before assuming the page regressed. Duplicate identifiers are expected in this request-led design as long as the selected request remains primary and supporting cards stay clearly subordinate.
