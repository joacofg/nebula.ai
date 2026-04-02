# S02: Ledger-backed calibration evidence — UAT

**Milestone:** M006
**Written:** 2026-04-02T03:39:43.378Z

# S02 UAT — Ledger-backed calibration evidence

## Preconditions
- Backend test environment is available with `./.venv/bin/pytest` runnable from the repo root.
- Console test environment is available with `npm --prefix console run test` runnable from the repo root.
- The worktree includes the M006/S01 calibrated routing contract and tenant `calibrated_routing_enabled` policy field.

## Test Case 1 — Backend derives sufficient tenant calibration evidence from existing ledger metadata
1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x`.
   - Expected: The selected tests pass.
2. Confirm the passing cases cover a tenant summary where recent eligible calibrated rows meet the sufficiency threshold.
   - Expected: The summary state is `sufficient`, with eligible row counts, latest eligible timestamp, and reason text derived from usage-ledger metadata only.
3. Confirm the same passing set includes degraded evidence rows.
   - Expected: Degraded counts/reasons stay visible without widening persistence or inventing replay-only fields.

## Test Case 2 — Override and policy-forced traffic do not poison calibration sufficiency
1. Inspect the passing `tests/test_service_flows.py -k "calibration_summary or simulation" -x` cases covering excluded traffic.
   - Expected: Explicit overrides and policy-forced routing are excluded from sufficiency counts.
2. Verify gated traffic is still visible.
   - Expected: `calibrated_routing_disabled` rows are reported distinctly as gated/rollout-disabled evidence rather than disappearing into missing-data classification.

## Test Case 3 — Stale versus thin versus rollout-disabled semantics stay distinct in replay
1. Run `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x`.
   - Expected: The selected simulation API coverage passes.
2. Confirm replay responses include the shared `calibration_summary` contract.
   - Expected: Simulation reports the same `sufficient`, `thin`, `stale`, and rollout-disabled semantics as the governance summary contract instead of a replay-only vocabulary.
3. Confirm replay ordering remains deterministic.
   - Expected: The replay path still uses oldest-first deterministic sampling while adding calibration evidence state to the response.

## Test Case 4 — Request detail keeps persisted request proof primary while adding calibration context
1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
   - Expected: The focused request-detail suite passes.
2. Confirm the request-detail cases render calibration messaging for `sufficient`, `thin`, `stale`, and rollout-disabled states.
   - Expected: The selected ledger row remains the primary proof surface and calibration text appears as compact supporting context.
3. Confirm absent-summary coverage passes.
   - Expected: Request detail handles missing calibration summaries gracefully without inventing empty placeholders or analytics framing.

## Test Case 5 — Observability shows bounded tenant replay-readiness context, not a new analytics destination
1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/observability-page.test.tsx`.
   - Expected: The focused Observability suite passes.
2. Confirm the integrated page copy still frames Observability as persisted request evidence first.
   - Expected: The page references public `X-Request-ID` / `X-Nebula-*` correlation and describes calibration evidence as supporting tenant-scoped context.
3. Confirm sufficient, thin, stale, and rollout-disabled calibration states render in the tenant summary card.
   - Expected: The card shows state reason, eligible rows, sufficiency threshold, latest eligible row, and rollout-disabled rows where applicable.
4. Confirm recommendation and cache sections remain bounded.
   - Expected: The page does not describe itself as analytics or black-box optimization, and calibration evidence appears beside existing recommendation/cache/runtime context rather than replacing the ledger proof flow.

## Edge Cases
- Thin evidence: eligible rows exist but remain below the sufficiency threshold; the UI and replay surfaces should show `thin`, not `stale`.
- Stale evidence: eligible evidence exists but the newest eligible row is outside the freshness window; the UI and replay surfaces should show `stale`.
- Rollout-disabled evidence: recent rows exist but calibrated routing is disabled; the summary should surface rollout-disabled row counts/reasons distinctly from missing data.
- Duplicate UI labels: the same calibration labels may appear in both Observability summary and request detail; focused UI tests should scope assertions to the intended panel rather than assuming page-wide uniqueness.
