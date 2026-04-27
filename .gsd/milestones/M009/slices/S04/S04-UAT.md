# S04: S04 — UAT

**Milestone:** M009
**Written:** 2026-04-27T21:28:42.838Z

# UAT — S04 Request-first operator evidence

## Preconditions

1. Console dependencies are installed and the console test environment is runnable.
2. Outcome-grounded routing fixtures are available through the existing mocked Observability/request-detail tests.
3. The selected request UI continues to consume persisted `route_signals` and optional tenant `calibration_summary` rather than any new dashboard-only data source.

## Test Case 1 — Selected request explains grounded routing from persisted request evidence

1. Run `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'`.
2. Inspect the grounded request-detail assertions in the passing suite.
3. Confirm the selected request explanation uses grounded/operator wording derived from persisted `route_signals`.
4. Confirm supporting tenant evidence is presented as additional context, not as the authoritative explanation.

**Expected outcome:** The suite passes and the selected request wording clearly explains a grounded routing decision while keeping the selected usage-ledger row authoritative.

## Test Case 2 — Thin, stale, and degraded supporting evidence remain visible but subordinate

1. In the same request-detail suite run, verify the thin, stale, and degraded supporting-summary cases are covered.
2. Confirm each case renders explicit operator wording tied to `calibration_summary` rather than falling back to generic copy.
3. Confirm the selected request investigation remains the primary explanation even when supporting tenant evidence is thin, stale, or degraded.

**Expected outcome:** Thin/stale/degraded supporting evidence states render clearly, but none of them displace or overrule the selected-request evidence.

## Test Case 3 — Rollout-disabled and unscored requests stay distinguishable on request detail

1. In the request-detail test run, verify assertions covering rollout-disabled and unscored request states.
2. Confirm the UI does not mislabel these cases as grounded or degraded.
3. Confirm operators can still understand why the selected request lacks grounded scoring without the component crashing or hiding the row.

**Expected outcome:** Rollout-disabled and unscored requests render as distinct request states with safe fallback wording.

## Test Case 4 — Observability page keeps selected request first

1. Run `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`.
2. Verify the focused page-level assertions covering top-level composition.
3. Confirm the selected request section appears before calibration, cache, or dependency follow-up cards.

**Expected outcome:** The selected request remains the first and authoritative inspection surface on the Observability page.

## Test Case 5 — Broader observability regression suite uses current governed ledger fixtures

1. Run `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'`.
2. Confirm the repaired fixture includes current `UsageLedgerRecord` governed metadata suppression fields and route evidence.
3. Confirm request detail renders without crashing when governed metadata suppression is present or optional fields are omitted.
4. Confirm supporting grounded/thin/stale/rollout-disabled states render without overriding selected-request evidence.

**Expected outcome:** The broader observability suite passes with current fixture shapes and proves safe request-detail rendering plus request-first hierarchy.

## Edge Cases

### Edge Case A — Missing `metadata_fields_suppressed`

1. Exercise the incomplete-fixture coverage in `ledger-request-detail.test.tsx`.
2. Confirm request detail still renders rather than throwing.

**Expected outcome:** Missing suppression arrays are tolerated safely.

### Edge Case B — Missing or partial `calibration_summary`

1. Exercise request-detail/page coverage where supporting tenant evidence is absent or partial.
2. Confirm supporting calibration sections become optional and selected-request wording still stands on persisted request evidence.

**Expected outcome:** The request remains investigable from the selected row alone, with no crash and no invented UI-only evidence state.

### Edge Case C — Legacy page fixtures drifting behind contract

1. Exercise the broader observability page suite after fixture repair.
2. Confirm governed metadata fields and route evidence stay aligned with the shared `UsageLedgerRecord` contract.

**Expected outcome:** Contract drift is caught by failing tests instead of silently weakening the operator evidence surface.
