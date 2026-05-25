# S02: S02 — UAT

**Milestone:** M010
**Written:** 2026-05-23T19:57:56.642Z

# UAT Type
Integration verification

# Preconditions
- Python virtual environment exists at `.venv` with test dependencies installed.
- Worktree contains the S02 outage-proof changes.
- No external PostgreSQL or Qdrant instances are required because the tests use deterministic doubles.

# Steps
1. Run `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q` from the repository root.
2. Observe the serving-critical governance outage scenario in `tests/test_phase10_outage_safety.py` completes successfully.
3. Confirm that scenario asserts a non-200 `/v1/chat/completions` result together with `/health/ready` returning `503` and `/health/dependencies` reporting `governance_store` as serving-critical, `not_ready`, and `fail_closed`.
4. Observe the serving-optional semantic-cache outage scenario in `tests/test_phase10_outage_safety.py` completes successfully.
5. Confirm that scenario asserts `/v1/chat/completions` still returns `200`, `/health/ready` remains non-503, and `/health/dependencies` reports `semantic_cache` as degraded with `continuity_limited` semantics and the expected reason code.
6. Confirm the focused regression coverage in `tests/test_health.py` also passes, proving the health payload contract remains aligned with the outage behavior.

# Expected Outcomes
- The full command exits with status 0.
- Pytest reports all outage and health checks passing.
- Governance-store outages are proven to fail closed with bounded request failure semantics and matching readiness/dependency truth.
- Semantic-cache outages are proven to preserve successful serving while health surfaces truthfully show degraded optional dependency state.

# Edge Cases
- Governance failures that occur during auth/tenant resolution are still bounded into a 503 fail-closed response rather than surfacing as uncaught exceptions.
- Semantic-cache degradation is modeled with production-like fallback semantics, so tests verify degraded continuity instead of an artificially fatal cache exception path.

# Not Proven By This UAT
- Real external PostgreSQL, Qdrant, or network outage behavior outside the deterministic test harness.
- Operator-facing console/admin presentation of these outage states.
- End-to-end recovery after an outage is cleared.
