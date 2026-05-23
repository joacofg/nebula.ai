---
id: T01
parent: S02
milestone: M010
key_files:
  - tests/test_phase10_outage_safety.py
  - src/nebula/services/auth_service.py
key_decisions: []
duration: 
verification_result: passed
completed_at: 2026-05-23T19:54:38.344Z
blocker_discovered: false
---

# T01: Added deterministic governance outage proof plus bounded auth-layer fail-closed handling so request failures align with readiness and dependency health.

**Added deterministic governance outage proof plus bounded auth-layer fail-closed handling so request failures align with readiness and dependency health.**

## What Happened

Extended the phase 10 outage safety test module with a deterministic governance outage proof that swaps the existing app harness to a failing governance-store seam during request authentication, then verifies the same outage across three layers: chat request failure, readiness 503, and dependency payload truth. The first verification run showed that governance-store exceptions during tenant-context resolution escaped as raw runtime errors, so I made the smallest backend fix in AuthService: catch unexpected governance access failures, log them, and convert them into a bounded 503 'Governance store unavailable.' response. Re-running the targeted outage test file then passed end to end.

## Verification

Ran `.venv/bin/pytest tests/test_phase10_outage_safety.py -q` and confirmed the outage safety suite passes, including the new governance outage proof that asserts non-200 request failure semantics together with `/health/ready` returning 503/not_ready and `/health/dependencies` reporting `governance_store` as serving-critical `not_ready` with `fail_closed` semantics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `.venv/bin/pytest tests/test_phase10_outage_safety.py -q` | 0 | ✅ pass | 1145ms |

## Deviations

Added a minimal auth-layer 503 mapping for governance-store access failures because the new end-to-end outage proof exposed an unbounded raw exception instead of the required bounded fail-closed response.

## Known Issues

None.

## Files Created/Modified

- `tests/test_phase10_outage_safety.py`
- `src/nebula/services/auth_service.py`
