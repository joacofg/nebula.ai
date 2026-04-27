# S03: S03 — UAT

**Milestone:** M009
**Written:** 2026-04-27T21:12:03.030Z

# S03: S03 — UAT

**Milestone:** M009
**Written:** 2026-04-27

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice changes replay semantics, typed API contracts, and request-first preview compatibility without requiring live provider traffic. Focused backend and console tests fully exercise the observable operator contract and the non-mutating replay boundary.

## Preconditions

- Python virtualenv dependencies are installed and `./.venv/bin/pytest` is available.
- Console dependencies are installed and Vitest can run under `console/`.
- The repository includes seeded replay fixtures used by `tests/test_service_flows.py` and `tests/test_governance_api.py`.
- No live providers or external credentials are required because the replay flow must remain metadata-only and side-effect free.

## Smoke Test

Run `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)"` and confirm the focused simulation test passes, proving the public replay endpoint still returns parity/degraded diagnostics without mutating tenant policy.

## Test Cases

### 1. Shared outcome-grounded replay semantics are reused across the simulation window

1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"`.
2. Inspect the passing focused tests covering replay evaluation and calibration summary reuse.
3. **Expected:** The suite passes and proves `PolicySimulationService.simulate()` computes one tenant-window `calibration_summary`, injects it into replayed `PolicyService.evaluate()` calls, and emits shared `outcome_evidence=sufficient` or `outcome_evidence=degraded` diagnostics instead of replay-only scoring behavior.

### 2. Admin replay proves unchanged-policy parity and changed-policy drift separately

1. Run `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)"`.
2. Confirm the unchanged-policy portion of the test asserts parity for route target, route reason, route mode, and route score against runtime for calibrated rows.
3. Confirm the changed-policy portion still asserts replay drift when the candidate policy differs.
4. **Expected:** The API-level simulation test passes, proving replay credibility for same-policy rows while still preserving changed-policy what-if behavior.

### 3. Console preview stays stable when degraded evidence is returned more often

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`.
2. Confirm the degraded calibration evidence preview case executes successfully.
3. **Expected:** The policy preview remains request-first and resilient when `calibration_summary.state` is `degraded`, with no replay-only UI branch required.

## Edge Cases

### Missing persisted route signals during replay

1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and degraded"`.
2. **Expected:** Replay still returns honest degraded route mode and policy outcome diagnostics rather than pretending fully grounded certainty when historical request signals are incomplete.

## Failure Signals

- Focused replay tests fail on route score/mode mismatches between runtime and unchanged-policy simulation.
- `calibration_summary` differs across replayed rows within one simulation request.
- Simulation mutates the saved tenant policy or triggers provider execution side effects.
- Console tests fail because `CalibrationEvidenceSummary.state` rejects `degraded` or the policy preview crashes/hides replay clues.

## Not Proven By This UAT

- Live `POST /v1/chat/completions` routing improvement against real provider behavior; that belongs to the integrated S05 proof.
- Request-detail and Observability UI explanation of grounded/thin/stale/degraded states; that is the scope of S04.
- Production operational telemetry beyond the test surfaces; this slice is bounded to replay semantics, typed contracts, and non-mutating operator proof.

## Notes for Tester

Replay is expected to remain metadata-only and bounded by persisted request evidence. If a future regression appears, compare unchanged-policy replay outputs against live persisted request diagnostics first; parity failures are more trustworthy than changed-policy drift checks for detecting semantic divergence.
