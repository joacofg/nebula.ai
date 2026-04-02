# S04: Operator inspection surfaces — UAT

**Milestone:** M006
**Written:** 2026-04-02T04:16:31.158Z

# S04: Operator inspection surfaces — UAT

**Milestone:** M006
**Written:** 2026-04-01

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice changes bounded console rendering and request-inspection framing on top of persisted admin data contracts already established in S01–S03. Focused console tests against those contracts are the strongest proof in this worktree.

## Preconditions

- `console/node_modules` is installed so Vitest can run.
- The M006 S01–S03 contracts already exist in the worktree: persisted `route_signals` may carry calibrated/degraded state and additive score components, and the recommendations payload includes `calibration_summary`.
- Run from the repository root: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx`

## Smoke Test

Run the focused Vitest command above and confirm all three test files pass with 20/20 tests green.

## Test Cases

### 1. Request detail shows calibrated routing inspection with additive score breakdown

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
2. Confirm the case `renders calibrated routing inspection with additive score components` passes.
3. Inspect the expectations in that case and verify the request detail renders `Routing inspection`, `Routing state`, `Route mode`, `Route score`, and additive score fields such as `Token score`, `Keyword bonus`, `Policy bonus`, or `Budget penalty` when present.
4. **Expected:** The selected persisted ledger row exposes calibrated request-level routing evidence directly from `route_signals`, and the tests pass without requiring any new API or analytics surface.

### 2. Request detail keeps degraded, rollout-disabled, and unscored rows explicit

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
2. Confirm the cases for degraded routing, rollout-disabled rows, and unscored partial-signal rows all pass.
3. Verify the assertions explicitly expect `degraded`, `rollout disabled`, and `unscored` text in bounded request detail rendering rather than treating null-mode rows as missing data.
4. **Expected:** Operators can distinguish degraded replay fallback, rollout-disabled gating, and unscored rows directly in request detail.

### 3. Observability presents selected request evidence first and supporting context second

1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx`.
2. Confirm the page renders headings and copy equivalent to `Selected request evidence first` and `Inspect one persisted ledger row before reading tenant context`.
3. Verify the tests assert that calibration readiness, grounded recommendations, cache posture, and dependency health are described as supporting runtime context for the same routed request investigation.
4. **Expected:** Observability is framed around the selected persisted ledger row, with surrounding cards positioned as support rather than replacement evidence.

### 4. Duplicate-label-safe rendering stays bounded to the right card

1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`.
2. Verify the tests intentionally scope queries for labels like `Eligible calibrated rows` and `Rollout-disabled rows` to the relevant card or section.
3. Confirm duplicate request IDs or duplicate routing labels do not fail the suite so long as the section-scoped assertions still pass.
4. **Expected:** The UI may repeat the same evidence labels across the tenant summary and request detail, but tests only fail if the wrong bounded section loses its contract.

## Edge Cases

### Rollout-disabled row with null route mode

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
2. Check the rollout-disabled case where calibrated routing was intentionally disabled for the request.
3. **Expected:** The UI renders `rollout disabled` explicitly and does not collapse the row into generic missing routing data.

### Partial route_signals without calibrated score path

1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
2. Check the unscored case where some route_signals exist but no calibrated score participated.
3. **Expected:** The UI renders `unscored` explicitly and preserves the request-level explanation rather than implying an analytics or fetch failure.

## Failure Signals

- The focused Vitest suite fails in any of the three target files.
- Request detail no longer renders `Routing inspection` for rows with persisted `route_signals`.
- Observability copy implies calibration summary, recommendations, cache, or dependency cards replace or overrule the selected persisted ledger row.
- Tests start failing because labels like `Eligible calibrated rows` or request IDs are assumed to be unique across the full page.

## Requirements Proved By This UAT

- R039 — The operator console can now expose calibrated-versus-heuristic routing state and supporting evidence through existing request-detail and Observability surfaces, strengthening the interpretable outcome-aware routing story without introducing a separate analytics product.

## Not Proven By This UAT

- End-to-end runtime generation of the underlying calibrated/degraded route_signals or calibration summaries; those behaviors were assembled in S01–S03.
- Full integrated M006 proof across live routing, replay parity, degraded fallback, and operator inspection together; that remains S05 work.
- TypeScript semantic diagnostics in this worktree; no active language server was available during slice close-out.

## Notes for Tester

If a future change adds new supporting cards or repeats existing labels again, keep the request-detail row authoritative and update tests with section-scoped queries rather than enforcing whole-page uniqueness. This slice intentionally treats bounded duplication as part of the UI contract.
