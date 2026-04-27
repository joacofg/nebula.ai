# S05: S05 — UAT

**Milestone:** M009
**Written:** 2026-04-27T21:48:43.449Z

# S05: S05 — UAT

**Milestone:** M009
**Written:** 2026-04-27

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S05 is a close-out slice that assembles proof across already-shipped runtime, admin, and console seams. The required confidence comes from rerunning the focused backend and console verification seams plus reviewing the integrated proof document rather than introducing a new manual operator workflow.

## Preconditions

- The repository is on the S05 completion state.
- Python virtualenv dependencies are installed in `./.venv`.
- Console test dependencies are installed under `console/`.
- The integrated proof document `docs/m009-integrated-proof.md` is present.

## Smoke Test

Open `docs/m009-integrated-proof.md` and confirm it walks the reader through the same four seams in order: public `POST /v1/chat/completions`, correlated `GET /v1/admin/usage/ledger?request_id=...`, unchanged-policy `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, and selected-request-first Observability/request detail for both a happy path and a degraded path.

## Test Cases

### 1. Happy-path proof chain stays intact

1. Run `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or policy_denied"`.
2. Run `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"`.
3. Run `./.venv/bin/pytest tests/test_governance_api.py -k "returns_summary_and_preserves_saved_policy or supports_unchanged_and_empty_windows"`.
4. **Expected:** The selected tests pass, proving a happy-path request can expose outcome-grounded headers, persist correlated route signals and outcome evidence in the ledger, and replay with unchanged-policy route parity on the existing simulation seam.

### 2. Degraded operator inspection stays request-first

1. Run `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'`.
2. Run `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`.
3. Run `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'`.
4. **Expected:** All selected console tests pass, proving degraded routing inspection keeps the selected request row authoritative while tenant calibration context remains supporting only on existing Observability surfaces.

## Edge Cases

### Missing persisted route signals during replay

1. Run `./.venv/bin/pytest tests/test_governance_api.py -k "supports_unchanged_and_empty_windows"`.
2. **Expected:** The replay result remains honest about degraded evidence by leaving parity fields unset when persisted route signals are incomplete rather than fabricating replay-only diagnostics.

## Failure Signals

- Any selected pytest or Vitest suite fails.
- `docs/m009-integrated-proof.md` no longer references the public request, ledger lookup, simulation replay, and selected-request-first inspection seams in order.
- Console assertions start promoting calibration context over the selected request row.
- Governance replay assertions start requiring fabricated parity metadata when persisted route signals are missing.

## Not Proven By This UAT

- It does not benchmark whether routing quality improved quantitatively in production traffic; it proves the end-to-end evidence chain and anti-drift seams only.
- It does not exercise a browser-driven live operator walkthrough; confidence comes from focused backend and component/page verification on the existing shipped seams.

## Notes for Tester

This slice intentionally closes the milestone without adding a new orchestration API, dashboard, or replay-only vocabulary. If a future change needs new proof coverage, extend the existing runtime, ledger, simulation, or request-detail seams instead of inventing a separate close-out surface.
