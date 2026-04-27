# S01: S01 — UAT

**Milestone:** M009
**Written:** 2026-04-27T15:01:47.686Z

# UAT — S01 Outcome evidence contract

## Preconditions
- Project dependencies are installed and the Python virtualenv exists at `./.venv`.
- The backend test suite can run locally from the repository root.
- The repository includes the S01 changes to governance summary models, GovernanceStore summarization, and replay/admin test coverage.

## Test Case 1 — Contract vocabulary remains stable through existing `calibration_summary` seam
1. Run `./.venv/bin/pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation"`.
   - Expected: The targeted governance/admin tests pass.
2. Review the passing assertions in the policy simulation/admin coverage.
   - Expected: Payloads still use the field name `calibration_summary` rather than a new API surface.
   - Expected: The exposed summary state vocabulary includes `sufficient`, `thin`, `stale`, and `degraded` as the shared outcome-evidence contract.
3. Confirm compatibility expectations in the tests/models.
   - Expected: Existing consumers can continue reading `calibration_summary` while downstream slices interpret its richer state semantics.

## Test Case 2 — Deterministic tenant/window-scoped summary derivation
1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "governance_store_calibration_summary or calibration_summary"`.
   - Expected: The targeted service-flow tests pass.
2. Inspect the covered scenarios exercised by the test names/assertions.
   - Expected: Evidence outside the requested time window is excluded from the summary.
   - Expected: Evidence from other tenants does not affect the current tenant summary.
   - Expected: The bounded read path still classifies eligible, excluded, gated, and degraded rows deterministically.

## Test Case 3 — State precedence is honest when evidence is thin, stale, degraded, or sufficient
1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or outcome or governance_store_calibration_summary"`.
   - Expected: The targeted summary-state tests pass.
2. Verify the scenarios represented by the assertions.
   - Expected: No evidence or below-threshold evidence yields `thin`.
   - Expected: Sufficient non-degraded but old evidence yields `stale`.
   - Expected: Sufficient fresh evidence with trustworthy rows yields `sufficient`.
   - Expected: When sufficient recent evidence includes eligible degraded rows, the summary state yields `degraded` instead of incorrectly reporting `sufficient` or `stale`.

## Test Case 4 — Governance-suppressed and replay-degraded rows stay visible to replay/admin consumers
1. Run `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation"`.
   - Expected: Policy simulation tests pass.
2. Confirm the degraded/suppressed-row assertions described by the tests.
   - Expected: A persisted row with suppressed `route_signals` is surfaced as degraded evidence with reason `missing_route_signals` rather than being silently treated as thin or sufficient.
   - Expected: Replay-degraded rows remain distinguishable with `degraded_replay_signals`.
   - Expected: Replay samples for suppressed rows keep route-mode parity fields null instead of fabricating calibrated metadata.

## Edge Cases
- Thin-before-sufficient precedence: if degraded rows exist but sufficient eligible evidence has not been reached, the summary should remain `thin` rather than prematurely reporting `degraded`.
- Fresh-but-untrustworthy evidence: if the evidence window is recent enough but eligible degraded rows are present after sufficiency is met, the summary must report `degraded` rather than a freshness-only state.
- Compatibility edge: existing admin/replay consumers should not need a renamed field to access the richer contract; `calibration_summary` must remain the payload seam.
- Scope safety: explicit-premium or override rows that are intentionally excluded from calibration evidence must remain excluded rather than inflating eligible evidence counts.
