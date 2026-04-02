# S03: Runtime / simulation parity

**Goal:** Extend policy simulation replay so the existing admin simulation contract and policy preview surface report the same calibrated-versus-degraded routing semantics that live runtime already emits for the same tenant traffic class, including explicit gated/null-mode behavior when calibrated routing is disabled.
**Demo:** After this: After this: policy simulation replay reports the same calibrated routing and degraded-mode semantics as live runtime for the same tenant traffic class.

## Tasks
- [x] **T01: Extended simulation changed-request samples with route parity fields and null-safe gated semantics aligned to runtime routing signals.** — Add the smallest backend contract needed for S03: extend `PolicySimulationChangedRequest` and the simulation service so replay changed-request samples carry the same calibrated/degraded/gated semantics that runtime already persists in `route_signals` and headers. Keep the vocabulary aligned to S01/S02 and preserve explicit null mode when calibrated routing is gated.

Steps:
1. Update the typed governance models in `src/nebula/models/governance.py` to add baseline/simulated parity fields for route mode, calibrated/degraded booleans, and route score on `PolicySimulationChangedRequest`, keeping gated rows explicit as null mode rather than synthesizing fake route signals.
2. Wire `src/nebula/services/policy_simulation_service.py` to derive baseline parity values from persisted ledger `route_signals` and simulated parity values from `PolicyEvaluation.route_decision`, including unchanged route targets that still count as changed because policy outcome or projected cost changed.
3. Mirror the contract in `console/src/lib/admin-api.ts` so the console uses the same field names and nullability as the backend response.
4. Add or update focused service-level assertions in `tests/test_service_flows.py` for the changed-request payload shape so later tasks can rely on the parity fields instead of re-deriving them in the UI.
  - Estimate: 1h
  - Files: src/nebula/models/governance.py, src/nebula/services/policy_simulation_service.py, console/src/lib/admin-api.ts, tests/test_service_flows.py
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x
- [x] **T02: Added runtime-to-replay parity tests that lock calibrated, degraded, and gated simulation semantics against live headers and usage-ledger evidence.** — Lock the S03 requirement at the backend boundary with focused parity tests. Use real runtime requests plus replay over the same tenant traffic class so parity is proven from shipped behavior, not assumed from shared architecture.

Steps:
1. Extend `tests/test_governance_api.py` to assert that simulation changed-request entries expose the same route reason, route mode, calibrated/degraded flags, and route score semantics as the live request that produced the ledger row.
2. Cover three concrete scenarios: a calibrated live request that stays calibrated in replay, a degraded replay case where missing or partial persisted signals produce `route_mode="degraded"`, and a calibrated-routing-disabled gate where runtime and replay both expose `calibrated_routing_disabled` with null route mode.
3. Reuse the existing oldest-first replay ordering and current admin endpoint; do not add a new endpoint or widen persistence.
4. Keep assertions aligned to the current contract by pairing runtime headers and ledger rows with simulation response fields rather than asserting on copy alone.
  - Estimate: 1h
  - Files: tests/test_governance_api.py, tests/test_service_flows.py, src/nebula/services/policy_simulation_service.py
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x
- [ ] **T03: Render compact routing parity cues in the existing policy preview** — Expose the new parity fields in the existing policy preview UI without widening it into a routing dashboard. Executors should keep the rendering compact and operator-readable so S03 stays bounded and S04 can build richer inspection later.

Steps:
1. Update `console/src/components/policy/policy-form.tsx` to render a concise parity line in each changed-request card using the new baseline/simulated route mode, calibrated/degraded markers, and route score fields when present.
2. Preserve explicit gated semantics: when route mode is null because calibrated routing is disabled, render the absence as an intentional gated state tied to the existing `calibrated_routing_disabled` reason rather than as missing data.
3. Keep the existing changed-request sample compact and reuse the established route vocabulary; do not add new sections, charts, or analytics framing.
4. Extend `console/src/components/policy/policy-page.test.tsx` to lock the parity rendering so future slices cannot regress the bounded preview contract.
  - Estimate: 45m
  - Files: console/src/components/policy/policy-form.tsx, console/src/components/policy/policy-page.test.tsx, console/src/lib/admin-api.ts
  - Verify: npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx
