# S02: Runtime outage behavior proof

**Goal:** Exercise one serving-critical outage and one serving-optional outage end to end so Nebula proves truthful fail-closed versus degraded-serving runtime behavior, plus matching readiness/dependency evidence, on existing backend surfaces.
**Demo:** After this: at least one serving-critical outage and one serving-optional outage are exercised end to end, proving truthful request behavior, safe degraded or fail-closed behavior, and correct runtime/admin evidence.

## Must-Haves

- Focused outage tests prove a deterministic governance-store failure causes chat completions to fail closed and `/health/ready` to return `503` while `/health/dependencies` reports serving-critical `not_ready` / `fail_closed` truth.
- Focused outage tests prove a deterministic semantic-cache or Qdrant outage preserves successful chat serving while `/health/ready` stays non-503 and `/health/dependencies` reports serving-optional degraded continuity-limited truth.
- Verification covers both runtime request behavior and the operator-consumable health surfaces already established in S01 without adding new resilience APIs or dashboard scope.

## Proof Level

- This slice proves: integration

## Integration Closure

Consumes the S01 typed resilience contract from `src/nebula/models/resilience.py` and existing runtime health aggregation in `src/nebula/services/runtime_health_service.py`. This slice closes the gap between contract-only health tests and real outage-path request behavior by wiring deterministic outage fixtures through the existing FastAPI app/test harness in `tests/test_phase10_outage_safety.py`. Remaining milestone work is operator-surface presentation and recovery proof in S03 and S04, not additional runtime outage abstractions.

## Verification

- Verifies that existing `/health/ready` and `/health/dependencies` payloads remain the authoritative inspection surfaces during serving-critical and serving-optional outages, including typed dependency class, lifecycle, serving effect, and reason-code evidence aligned with request outcomes.

## Tasks

- [x] **T01: Add serving-critical governance outage proof** `est:1.5h`
  Why: S02 must first prove the strongest fail-closed invariant from S01: if the governance store is unavailable at request time, Nebula must not pretend serving succeeded, and health truth must agree. Do: extend `tests/test_phase10_outage_safety.py` using the existing `configured_outage_client()` harness to inject a deterministic governance-store failure before request completion, preferably by swapping in a failing governance or policy seam already exercised by the real app. Keep the proof end-to-end: send `/v1/chat/completions`, assert the response is a bounded non-200 failure, then assert `/health/ready` returns `503` with overall `not_ready` and `/health/dependencies` reports `governance_store` as serving-critical `not_ready` with `fail_closed` semantics and a stable reason/detail. If the current app code does not propagate this truthfully, make the smallest backend fix in the existing runtime path rather than adding a new resilience surface. Done when one deterministic test locks all three layers: request failure semantics, readiness `503`, and dependency payload truth for the same outage.
  - Files: `tests/test_phase10_outage_safety.py`, `src/nebula/services/chat_service.py`, `src/nebula/services/governance_store.py`, `src/nebula/services/runtime_health_service.py`
  - Verify: .venv/bin/pytest tests/test_phase10_outage_safety.py -q

- [x] **T02: Add serving-optional semantic cache outage proof and slice verification** `est:1.5h`
  Why: S02 also needs the complementary continuity proof: an optional dependency outage must degrade truthfully without blocking healthy serving. Do: extend `tests/test_phase10_outage_safety.py` and, only if required, shared test support to force semantic-cache or Qdrant unavailability while local completions still succeed through the existing stubs. Assert chat completions still return `200` with truthful route metadata, `/health/ready` remains non-503 with overall `ready` or `degraded`, and `/health/dependencies` reports `semantic_cache` as serving-optional degraded continuity-limited with the expected reason/detail. Reuse the S01 typed payload contract instead of inventing new fields. Then run the focused outage plus health verification suite to prove both outage classes coexist with the established readiness contract. Done when the optional-outage request proof passes, the health payload is truthful, and the focused regression suite is green.
  - Files: `tests/test_phase10_outage_safety.py`, `tests/support.py`, `src/nebula/services/semantic_cache_service.py`, `src/nebula/services/runtime_health_service.py`, `tests/test_health.py`
  - Verify: .venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q

## Files Likely Touched

- tests/test_phase10_outage_safety.py
- src/nebula/services/chat_service.py
- src/nebula/services/governance_store.py
- src/nebula/services/runtime_health_service.py
- tests/support.py
- src/nebula/services/semantic_cache_service.py
- tests/test_health.py
