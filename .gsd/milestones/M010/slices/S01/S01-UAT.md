# S01: S01 — UAT

**Milestone:** M010
**Written:** 2026-05-23T19:49:22.714Z

# UAT — S01 Dependency failure contract

## UAT Type
Backend contract and runtime-surface verification.

## Preconditions
1. Repository checkout is at the S01 implementation state.
2. Python virtualenv dependencies are installed in `.venv`.
3. The operator is in `/Users/joaquinfernandezdegamboa/Proj/nebula`.

## Steps
1. Run `cd /Users/joaquinfernandezdegamboa/Proj/nebula && .venv/bin/pytest tests/test_health.py tests/test_response_headers.py -q`.
2. Inspect the passing assertions for `/health/ready` and `/health/dependencies` in `tests/test_health.py`.
3. Confirm the degraded optional-dependency case returns HTTP 200 with overall status `degraded` and a dependency payload containing `dependency_class`, `lifecycle_state`, `serving_effect`, `reason_code`, `recovering`, `last_failure_at`, and `last_recovery_at` while preserving `status`, `required`, and `detail`.
4. Confirm the serving-critical governance-store failure case returns HTTP 503 from `/health/ready` with overall status `not_ready` and a payload marked `serving_critical` plus `fail_closed`.
5. Confirm the recovering dependency case remains HTTP 200 but reports overall status `degraded` and dependency `status` / `lifecycle_state` of `recovering`.
6. Confirm `tests/test_response_headers.py` still passes, proving the resilience-contract changes did not regress existing request metadata headers and ledger parity assertions.

## Expected Outcomes
- The targeted pytest suite passes.
- Runtime health surfaces expose the typed resilience contract consistently.
- Serving-critical failures fail readiness closed with HTTP 503.
- Serving-optional and recovering dependencies degrade truthfully without false not-ready semantics.
- Legacy health keys remain present for compatibility.

## Edge Cases
- Optional dependency outage: service stays ready enough to serve, but health truth becomes `degraded`.
- Recovering dependency: service remains degraded until stabilization instead of immediately flipping to `ready`.
- Metadata-only dependency health payloads keep additive recovery fields without changing serving readiness semantics.

## Not Proven By This UAT
- Real dependency outages against live PostgreSQL, Qdrant, or premium providers.
- Operator-console wording or observability UI presentation.
- End-to-end recovery runbooks or post-recovery operational evidence beyond contract-level payload shape.
