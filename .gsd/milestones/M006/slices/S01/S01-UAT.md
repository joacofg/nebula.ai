# S01: Calibrated routing core — UAT

**Milestone:** M006
**Written:** 2026-04-02T03:09:02.837Z

# S01: Calibrated routing core — UAT

**Milestone:** M006
**Written:** 2026-04-02

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: This slice changed runtime routing behavior, governance persistence, and the existing policy editor. The shipped proof is strongest when it combines artifact-backed backend/console tests with concrete operator steps that trace one request from public response headers into persisted usage evidence.

## Preconditions

- Python virtualenv dependencies are installed and `./.venv/bin/pytest` works.
- Console dependencies are installed and `npm --prefix console run test` works.
- Database migrations are applied with `./.venv/bin/alembic upgrade head`.
- A local operator session can load the Policy page, or the tester can use the focused console tests as the UI proof surface.
- The default tenant exists with a writable policy and at least one allowed premium model.

## Smoke Test

1. Run `./.venv/bin/pytest tests/test_router_signals.py -x`.
2. **Expected:** All focused router tests pass, proving the shared calibrated scoring contract and route-signal vocabulary are assembled before checking admin/runtime surfaces.

## Test Cases

### 1. Calibrated token-complexity routing emits interpretable runtime evidence

1. Run `./.venv/bin/pytest tests/test_router_signals.py -x`.
2. Inspect the passing cases for calibrated live routing, replay reconstruction, and degraded replay behavior.
3. **Expected:** Token-complexity routes emit additive route signals including `route_mode`, calibrated/degraded markers, and `score_components`, while explicit override routes keep `route_signals` empty and `route_score` at `0.0`.

### 2. Policy and runtime preserve calibrated metadata through headers and persisted evidence

1. Run `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py tests/test_response_headers.py -k "simulation or runtime_policy or response_headers or denied or fallback or hard_budget" -x`.
2. Focus on the response-header test covering denied explicit routes and fallback-blocked provider failures.
3. **Expected:** Successful, denied, and fallback-blocked requests expose coherent `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Route-Score`, and conditional `X-Nebula-Route-Mode` headers, and the request identified by `X-Request-ID` matches a usage-ledger row with the same route reason and calibrated route-signal payload.

### 3. The bounded tenant rollout valve persists and affects runtime/simulation consistently

1. Run `./.venv/bin/alembic upgrade head && ./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation or route_reason" -x`.
2. Confirm the focused governance tests cover policy options, policy read/write payloads, and simulation behavior when `calibrated_routing_enabled` is disabled.
3. **Expected:** Admin policy APIs expose `calibrated_routing_enabled` as a runtime-enforced field, persistence accepts and returns the field, and runtime/simulation both surface `route_reason=calibrated_routing_disabled` plus empty route signals when the rollout valve disables token-complexity routing.

### 4. Operators can toggle the rollout valve from the existing policy editor without widening the UI

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Confirm the form submits a payload with `calibrated_routing_enabled` populated and the page keeps the control inside the runtime-enforced policy surface.
3. **Expected:** The policy editor shows a single "Calibrated routing enabled" checkbox, preview/save flows serialize it correctly, and no broader calibration analytics or tuning UI appears in this slice.

## Edge Cases

### Policy-denied explicit override still exposes route evidence

1. Execute the focused backend command from Test Case 2.
2. Inspect the assertion path for an explicit premium model denied by policy.
3. **Expected:** The denial response still exposes `X-Nebula-Route-Score: 0.0000`, omits `X-Nebula-Route-Mode`, and includes meaningful `X-Nebula-Policy-Outcome` text rather than dropping route evidence entirely.

### Local provider failure with premium fallback disabled preserves the original calibrated score

1. Execute the focused backend command from Test Case 2.
2. Inspect the fallback-blocked assertion path.
3. **Expected:** The 502 response shows `X-Nebula-Route-Reason=local_provider_error_fallback_blocked`, keeps the calibrated `X-Nebula-Route-Score`/`X-Nebula-Route-Mode` from the original route decision, and the matching usage-ledger row carries the same calibrated `route_signals` payload.

### Calibrated routing disabled does not affect explicit or policy-forced routes

1. Execute the governance command from Test Case 3.
2. Inspect the disabled-rollout coverage.
3. **Expected:** Only token-complexity auto routing is gated to local; explicit premium/local overrides and policy-forced routes retain their existing reasons and do not emit synthetic calibrated signals.

## Failure Signals

- `tests/test_router_signals.py` fails on `route_mode`, `score_components`, or degraded replay assertions.
- Response headers for denied or fallback-blocked requests lose `X-Nebula-Route-Score` or disagree with the matching usage-ledger row.
- Policy APIs omit `calibrated_routing_enabled`, or simulation/runtime disagree on `calibrated_routing_disabled` semantics.
- The console policy form submits `calibrated_routing_enabled: undefined` or hides the rollout valve outside the runtime-enforced controls section.

## Requirements Proved By This UAT

- R039 — Proves Nebula now has an interpretable calibrated routing core with explicit decision signals, additive score breakdown, propagated runtime evidence, and bounded tenant rollout control, while also showing that full validation still depends on later ledger-backed calibration and parity slices.

## Not Proven By This UAT

- This UAT does not prove tenant-scoped calibration summaries derived from historical ledger evidence; that is S02 work.
- This UAT does not prove full replay/runtime parity across operator inspection surfaces or integrated milestone proof; those are S03-S05 concerns.
- This UAT does not validate that R039 is complete; it validates the calibrated routing core only.

## Notes for Tester

Use the stronger backend command as the authoritative runtime proof for this slice, not only the literal T02 task-plan command, because the original argument ordering under-selected the touched response-header file. When checking calibrated scores in focused tests, treat the prompt fixture text as authoritative: token-based score components legitimately change when the test prompt changes.
