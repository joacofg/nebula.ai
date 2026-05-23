---
estimated_steps: 3
estimated_files: 4
skills_used: []
---

# T02: Wire RuntimeHealthService aggregation semantics and lock the contract with failure-path tests

Why: the shared payload shape is only useful if the runtime aggregator and tests prove how serving-critical vs optional dependencies affect readiness and operator truth. This is the contract later outage and recovery slices will rely on.

Do: Update `RuntimeHealthService` to aggregate overall readiness from the typed dependency contract rather than only raw `required` / `status`, while preserving the current endpoint behavior in `src/nebula/main.py` (`200` for ready or degraded, `503` for not_ready). Keep `/health/ready` and `/health/dependencies` on the same runtime truth seam. Extend `tests/test_health.py` with explicit contract assertions for a serving-critical failure, serving-optional degradation, and a recovery-oriented payload shape. Add or adjust backend request-path tests only where needed to confirm the new contract does not drift from existing fail-closed metadata behavior already asserted in `tests/test_response_headers.py`.

Done when: runtime aggregation uses the typed contract consistently, health endpoints return stable structured payloads with truthful status codes, and tests fail if dependency class/effect/recovery semantics regress.

## Inputs

- `src/nebula/models/resilience.py`
- `src/nebula/services/runtime_health_service.py`
- `src/nebula/main.py`
- `tests/test_health.py`
- `tests/test_response_headers.py`

## Expected Output

- `src/nebula/services/runtime_health_service.py`
- `src/nebula/main.py`
- `tests/test_health.py`
- `tests/test_response_headers.py`

## Verification

pytest tests/test_health.py tests/test_response_headers.py -q

## Observability Impact

Locks the readiness contract to explicit degraded/fail-closed semantics and ensures future agents can inspect dependency class, reason, and recovery fields through the existing health endpoints.
