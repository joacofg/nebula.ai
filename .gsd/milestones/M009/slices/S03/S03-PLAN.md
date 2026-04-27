# S03: Replay parity for outcome-grounded routing

**Goal:** Make admin policy simulation replay consume the same tenant-scoped outcome-evidence summary and additive routing semantics as live runtime, while preserving honest degraded replay behavior and bounded request-first operator proof.
**Demo:** After this: `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replays the same outcome-grounded semantics as runtime, including honest degraded behavior when evidence is incomplete.

## Must-Haves

- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replays the same outcome-grounded route scoring semantics as runtime for the same tenant traffic class rather than falling back to heuristic-only replay.
- Replay uses the shared `GovernanceStore.summarize_calibration_evidence()` tenant-window summary once per simulation window and returns that same bounded summary contract in `calibration_summary`.
- Changed-request replay output stays honest when persisted signals are incomplete by surfacing degraded parity via existing route-mode and policy-outcome fields instead of pretending fully grounded certainty.
- Console/admin typing remains additive and request-first; no new dashboard surface or replay-only evidence vocabulary is introduced.

## Proof Level

- This slice proves: This slice proves: integration
- Real runtime required: no
- Human/UAT required: no

## Integration Closure

- Upstream surfaces consumed: `src/nebula/services/governance_store.py` summarization seam, `src/nebula/services/router_service.py` additive scoring/replay route-mode contract, and S02-persisted `UsageLedgerRecord.route_signals` / `policy_outcome` request evidence.
- New wiring introduced in this slice: admin simulation now injects tenant-window outcome evidence into shared `PolicyService.evaluate()` so replay and runtime traverse the same backend scoring path.
- What remains before the milestone is truly usable end-to-end: S04 still needs to explain grounded/thin/stale/degraded request evidence on request-first operator surfaces, and S05 still needs the integrated live-request → replay → operator proof.

## Verification

- Runtime signals: `simulated_policy_outcome`, `simulated_route_mode`, `simulated_route_score`, and `calibration_summary` remain the canonical replay diagnostics.
- Inspection surfaces: `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, backend pytest coverage in `tests/test_service_flows.py` and `tests/test_governance_api.py`, and the existing policy preview in `console/src/components/policy/policy-form.tsx`.
- Failure visibility: parity drift localizes through changed-request samples, degraded replay flags, and tenant-window evidence counts/reasons without needing provider calls or ledger mutation.
- Redaction constraints: replay remains metadata-only; no raw prompts, responses, or credentials are added to admin payloads.

## Tasks

- [x] **T01: Wire tenant-window outcome evidence into replay evaluation** `est:1h`
  Add the replay propagation seam that keeps runtime and simulation on one routing contract.

Steps:
1. Extend `PolicyService.evaluate()` so replay callers can supply an explicit calibration/outcome evidence summary override instead of forcing replay to skip evidence lookup whenever `replay_context` is present.
2. In `PolicySimulationService.simulate()`, compute the tenant-window `calibration_summary` once for the requested replay window before the row loop, pass that same summary into every replayed `PolicyService.evaluate()` call, and return the exact same summary object in the response payload.
3. Preserve current bounded replay behavior: still use `before_timestamp` for spend-window guardrails, keep synthetic prompt reconstruction only as a fallback for missing persisted signals, and do not add a replay-only scoring branch or duplicate evidence classification outside `GovernanceStore.summarize_calibration_evidence()`.
4. Update or add focused backend service tests that prove replay now carries `outcome_evidence=...` vocabulary in `simulated_policy_outcome`, that a low-complexity replay can change for the same evidence-driven reason as live runtime, and that missing replay signals still produce degraded route mode honestly under the shared evidence summary.
  - Files: `src/nebula/services/policy_service.py`, `src/nebula/services/policy_simulation_service.py`, `tests/test_service_flows.py`
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"

- [x] **T02: Prove admin replay parity and repair console type drift** `est:1h`
  Close the public replay boundary and keep the request-first console contract aligned with the backend semantics.

Steps:
1. Extend admin API coverage so `POST /v1/admin/tenants/{tenant_id}/policy/simulate` proves replay uses the same outcome-grounded semantics as runtime for the same tenant traffic class, including changed-request route score/mode parity and honest degraded behavior when persisted route signals are incomplete.
2. Keep the simulation non-mutating and bounded by asserting saved tenant policy is unchanged, no provider execution side effects are introduced, and the returned tenant-window `calibration_summary` matches the replay window semantics.
3. Update `console/src/lib/admin-api.ts` so `CalibrationEvidenceSummary.state` includes `"degraded"`, then adjust policy-form tests only as needed to keep the request-first preview resilient when degraded replay evidence becomes visible more often.
4. Verify the backend API contract and the console type/test seam separately so future regressions localize quickly to either replay semantics or UI typing/rendering drift.
  - Files: `tests/test_governance_api.py`, `src/nebula/api/routes/admin.py`, `console/src/lib/admin-api.ts`, `console/src/components/policy/policy-form.test.tsx`
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)" && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx

## Files Likely Touched

- src/nebula/services/policy_service.py
- src/nebula/services/policy_simulation_service.py
- tests/test_service_flows.py
- tests/test_governance_api.py
- src/nebula/api/routes/admin.py
- console/src/lib/admin-api.ts
- console/src/components/policy/policy-form.test.tsx
