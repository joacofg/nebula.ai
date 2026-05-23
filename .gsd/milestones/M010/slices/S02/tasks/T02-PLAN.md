---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T02: Add serving-optional semantic cache outage proof and slice verification

Why: S02 also needs the complementary continuity proof: an optional dependency outage must degrade truthfully without blocking healthy serving. Do: extend `tests/test_phase10_outage_safety.py` and, only if required, shared test support to force semantic-cache or Qdrant unavailability while local completions still succeed through the existing stubs. Assert chat completions still return `200` with truthful route metadata, `/health/ready` remains non-503 with overall `ready` or `degraded`, and `/health/dependencies` reports `semantic_cache` as serving-optional degraded continuity-limited with the expected reason/detail. Reuse the S01 typed payload contract instead of inventing new fields. Then run the focused outage plus health verification suite to prove both outage classes coexist with the established readiness contract. Done when the optional-outage request proof passes, the health payload is truthful, and the focused regression suite is green.

## Inputs

- `tests/test_phase10_outage_safety.py`
- `tests/support.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/services/runtime_health_service.py`
- `tests/test_health.py`

## Expected Output

- `tests/test_phase10_outage_safety.py`
- `tests/support.py`

## Verification

.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q

## Observability Impact

Locks the existing semantic-cache degraded payload as the operator-visible explanation for continuity-limited serving during Qdrant outages.
