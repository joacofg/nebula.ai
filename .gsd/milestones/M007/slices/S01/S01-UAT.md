# S01: Define page roles and evidence boundaries — UAT

**Milestone:** M007
**Written:** 2026-04-03T02:00:04.231Z

# S01 UAT — Define page roles and evidence boundaries

## Preconditions
- Console dependencies are installed and `npm --prefix console run test` can execute Vitest.
- Worktree includes the M007/S01 console changes.
- Use the focused verification command when confirming this slice: `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.

## Test Case 1 — Observability leads with selected-request investigation
1. Run the focused verification command above.
   - Expected: all 5 Vitest files pass.
2. Open `console/src/app/(console)/observability/page.tsx` and inspect the top-level sections after filters.
   - Expected: the first major evidence section after `LedgerFilters` is the selected-request section headed `Inspect one persisted ledger row before reading tenant context`.
3. Confirm the next major sections are supporting context and dependency health, in that order.
   - Expected: `Grounded follow-up guidance for the selected request` appears before `Dependency health context`, with no dashboard framing.
4. Review the Observability tests.
   - Expected: `page.test.tsx` and `observability-page.test.tsx` assert heading order, require selected-request-first phrasing, and reject `dashboard` drift.

## Test Case 2 — Request detail remains the authoritative persisted evidence record
1. Review `console/src/components/ledger/ledger-request-detail.tsx`.
   - Expected: the lead paragraph says the persisted ledger record is the authoritative evidence row for the request ID.
2. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
   - Expected: tests pass.
3. Inspect the test cases for calibrated, degraded, rollout-disabled, and unscored routing states.
   - Expected: each state renders as explicit request-level evidence, not as missing data or analytics framing.
4. Inspect the budget and calibration sections.
   - Expected: they render as supporting evidence panels and do not replace the persisted request fields as the lead surface.

## Test Case 3 — Policy preview stays preview-before-save and does not drift into analytics/editor blend
1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
   - Expected: both files pass.
2. Inspect `console/src/components/policy/policy-form.tsx` preview section.
   - Expected: it is headed `Preview before save`, includes the badge `Save remains explicit`, and says replay does not persist the policy.
3. Review changed-request preview assertions in `policy-page.test.tsx`.
   - Expected: tests confirm parity rows render for changed requests and explicitly reject `dashboard`, `routing studio`, and `analytics product` wording.
4. Review the zero-result and error preview states.
   - Expected: preview still reads as non-saving decision support in both cases.

## Test Case 4 — Edge case: rollout-disabled parity rows remain renderable when route score is absent
1. Inspect `formatRouteScore` in `console/src/components/policy/policy-form.tsx`.
   - Expected: it returns `null` for both `null` and `undefined` route scores.
2. Run the focused policy tests again.
   - Expected: the preview no longer crashes on rollout-disabled/null-mode changed-request rows.
3. Check the changed-request parity expectations in `policy-page.test.tsx`.
   - Expected: one sample renders `routing parity: degraded (degraded, score 0.28) → rollout disabled` without requiring a numeric simulated route score.

## Edge Cases
- Thin/stale/gated calibration summaries must remain valid supporting context on Observability and request detail without inventing a separate analytics flow.
- Request detail must continue to render neutral empty state text when no ledger row is selected.
- Policy preview error and zero-row states must keep explicit preview-before-save semantics and must not imply that the draft has been applied.
