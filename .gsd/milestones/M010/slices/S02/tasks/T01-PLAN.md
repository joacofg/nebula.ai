---
estimated_steps: 1
estimated_files: 4
skills_used: []
---

# T01: Add serving-critical governance outage proof

Why: S02 must first prove the strongest fail-closed invariant from S01: if the governance store is unavailable at request time, Nebula must not pretend serving succeeded, and health truth must agree. Do: extend `tests/test_phase10_outage_safety.py` using the existing `configured_outage_client()` harness to inject a deterministic governance-store failure before request completion, preferably by swapping in a failing governance or policy seam already exercised by the real app. Keep the proof end-to-end: send `/v1/chat/completions`, assert the response is a bounded non-200 failure, then assert `/health/ready` returns `503` with overall `not_ready` and `/health/dependencies` reports `governance_store` as serving-critical `not_ready` with `fail_closed` semantics and a stable reason/detail. If the current app code does not propagate this truthfully, make the smallest backend fix in the existing runtime path rather than adding a new resilience surface. Done when one deterministic test locks all three layers: request failure semantics, readiness `503`, and dependency payload truth for the same outage.

## Inputs

- `tests/test_phase10_outage_safety.py`
- `tests/support.py`
- `src/nebula/services/chat_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/runtime_health_service.py`
- `src/nebula/main.py`
- `tests/test_health.py`

## Expected Output

- `tests/test_phase10_outage_safety.py`

## Verification

.venv/bin/pytest tests/test_phase10_outage_safety.py -q

## Observability Impact

Confirms serving-critical outage evidence stays aligned across request failure semantics and the existing readiness/dependencies endpoints.
