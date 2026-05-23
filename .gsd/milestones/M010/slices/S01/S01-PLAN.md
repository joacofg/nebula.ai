# S01: Dependency failure contract

**Goal:** Establish a stable typed resilience contract for dependency health and serving consequences so Nebula can distinguish serving-critical, serving-optional, and metadata-only failures, expose truthful degraded or fail-closed readiness semantics on existing runtime surfaces, and carry recovery-state fields needed by later outage and operator-proof slices.
**Demo:** After this: Nebula has a stable typed resilience contract proving how serving-critical, serving-optional, and metadata-only dependency failures degrade, fail closed, and recover at the runtime truth layer.

## Must-Haves

- Backend defines one shared additive resilience contract that preserves existing `status` / `required` / `detail` compatibility while adding typed dependency class, serving effect, reason code, and recovery-state metadata.
- `/health/ready` and `/health/dependencies` expose the typed contract consistently and keep current HTTP readiness semantics truthful: required serving-critical failures return `503`, optional failures can report degraded without false not-ready.
- Focused backend tests exercise at least one serving-critical failure, one serving-optional degradation, and one recovery-oriented payload shape so later slices can build outage proofs on a locked contract.
- The slice does not widen scope into new operator dashboards or hosted-contract changes; it only strengthens backend runtime truth and tests.

## Proof Level

- This slice proves: contract

## Integration Closure

This slice closes the backend truth-model seam by wiring the shared resilience vocabulary through RuntimeHealthService and the dependency producers already surfaced by FastAPI health endpoints. Later slices still need to exercise real outage paths, map this truth onto operator surfaces, and prove end-to-end recovery, but they should not need to redefine dependency classes or serving effects.

## Verification

- Existing health endpoints remain the primary inspection surfaces. This slice should make failure diagnosis more machine-readable by adding stable class/effect/reason metadata and recovery-state fields, while preserving redaction boundaries and avoiding raw dependency internals or hosted-plane sprawl.

## Tasks

- [x] **T01: Add shared resilience contract types and migrate dependency health payloads** `est:75m`
  Why: S01 needs one authoritative backend vocabulary before outage proofs or UI wording can be trusted. Today dependency producers return ad hoc dictionaries with only `status`, `required`, and `detail`, which is too coarse for the milestone’s serving-critical, serving-optional, and metadata-only outage classes.
  - Files: `src/nebula/models/resilience.py`, `src/nebula/services/governance_store.py`, `src/nebula/services/semantic_cache_service.py`, `src/nebula/services/premium_provider_health_service.py`, `src/nebula/services/embeddings_service.py`, `src/nebula/services/retention_lifecycle_service.py`, `tests/support.py`
  - Verify: pytest tests/test_health.py -q

- [x] **T02: Wire RuntimeHealthService aggregation semantics and lock the contract with failure-path tests** `est:60m`
  Why: the shared payload shape is only useful if the runtime aggregator and tests prove how serving-critical vs optional dependencies affect readiness and operator truth. This is the contract later outage and recovery slices will rely on.
  - Files: `src/nebula/services/runtime_health_service.py`, `src/nebula/main.py`, `tests/test_health.py`, `tests/test_response_headers.py`
  - Verify: pytest tests/test_health.py tests/test_response_headers.py -q

## Files Likely Touched

- src/nebula/models/resilience.py
- src/nebula/services/governance_store.py
- src/nebula/services/semantic_cache_service.py
- src/nebula/services/premium_provider_health_service.py
- src/nebula/services/embeddings_service.py
- src/nebula/services/retention_lifecycle_service.py
- tests/support.py
- src/nebula/services/runtime_health_service.py
- src/nebula/main.py
- tests/test_health.py
- tests/test_response_headers.py
