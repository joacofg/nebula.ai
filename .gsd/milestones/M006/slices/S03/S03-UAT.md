# S03: Runtime / simulation parity — UAT

**Milestone:** M006
**Written:** 2026-04-02T03:57:24.612Z

# S03 UAT — Runtime / simulation parity

## Preconditions
- Python virtualenv dependencies are installed and `./.venv/bin/pytest` is available.
- Console dependencies are installed and `npm --prefix console run test` works.
- The assembled worktree includes the S03 backend and console changes.
- Admin policy simulation continues to use the existing `POST /v1/admin/tenants/{tenant_id}/policy/simulate` contract and the policy page preview surface.

## Test Case 1 — Service-level replay exposes calibrated parity fields
1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x`.
2. Confirm the simulation-focused service tests pass.
3. Inspect the selected cases conceptually: changed-request samples must include baseline and simulated route target, route reason, route mode, calibrated/degraded booleans, and route score.

**Expected outcome**
- The suite passes.
- Calibrated replay samples show non-null route mode and route score when backed by calibrated runtime evidence.
- Policy-forced and calibrated-routing-disabled replay cases keep `route_mode`, calibrated/degraded flags, and route score null instead of inventing synthetic values.

## Test Case 2 — Admin simulation parity matches live runtime evidence for a calibrated request
1. Run `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x`.
2. Confirm the calibrated runtime request test creates a real chat-completions response, captures `X-Request-ID` plus `X-Nebula-*` headers, reads the correlated usage-ledger row, and then replays through the admin simulation endpoint.
3. Verify the changed-request sample for the runtime request matches the live header and ledger semantics for route target, route reason, route mode, calibrated/degraded flags, and route score.

**Expected outcome**
- The suite passes.
- Baseline replay fields equal the live runtime headers and persisted ledger fields for the same request.
- Replay preserves null route semantics when the simulated policy forces a policy-only route instead of a calibrated token-complexity decision.

## Test Case 3 — Degraded replay evidence remains explicit when persisted route signals are thin
1. Use the same focused governance simulation test run from Test Case 2.
2. Inspect the degraded runtime/replay scenario covered there.
3. Verify the degraded row is treated as eligible degraded evidence, not as calibrated evidence and not as rollout-disabled evidence.

**Expected outcome**
- The replay window reports degraded evidence through the calibration summary and changed-request semantics.
- Runtime and persisted ledger intentionally lack a route mode for the thin-signals row.
- Replay classification still distinguishes this from rollout-disabled gating and explicit override rows.

## Test Case 4 — Rollout-disabled gating renders as intentional null mode in preview
1. Run `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`.
2. Confirm the policy preview tests pass.
3. Verify the changed-request preview includes a routing parity line for both a calibrated→degraded case and a degraded→rollout-disabled case.

**Expected outcome**
- The suite passes.
- The preview renders `routing parity: calibrated (calibrated, score 0.74) → degraded (degraded, score 0.31)` for the calibrated/degraded sample.
- The preview renders `routing parity: degraded (degraded, score 0.28) → rollout disabled` for the gated sample.
- The preview remains inside the existing changed-request card and does not introduce a separate routing dashboard.

## Test Case 5 — Preview remains bounded and save semantics stay explicit
1. In the same console test run, verify the preview interaction path on the policy page.
2. Trigger Preview impact with an edited draft policy.
3. Confirm the preview response renders a changed-request sample and the page still states that the preview did not save the policy.

**Expected outcome**
- Preview invokes simulation without calling the save mutation.
- The page shows `Save remains explicit` and `This preview did not save the policy.`
- Routing parity is presented as compact supporting evidence rather than expanded analytics.

## Edge Cases
- Inverted simulation windows still fail with `from_timestamp must be less than or equal to to_timestamp.`
- Empty replay windows still produce a zero-result preview state rather than stale changed-request content.
- Explicit premium/local overrides and policy-forced routes remain unscored and null-mode in parity output.
- Calibrated-routing-disabled rows render as `rollout disabled`, not as missing data or degraded routing.
