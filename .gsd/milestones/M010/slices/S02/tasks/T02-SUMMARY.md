---
id: T02
parent: S02
milestone: M010
key_files:
  - tests/test_phase10_outage_safety.py
  - tests/test_health.py
  - tests/support.py
key_decisions:
  - Optional-dependency outage tests should reuse the typed health contract and preserve production request fallback semantics instead of injecting uncaught exceptions into higher layers.
duration: 
verification_result: mixed
completed_at: 2026-05-23T19:57:01.837Z
blocker_discovered: false
---

# T02: Added semantic-cache outage proofs that keep chat serving successful while `/health/ready` and `/health/dependencies` truthfully report serving-optional degraded continuity-limited state.

**Added semantic-cache outage proofs that keep chat serving successful while `/health/ready` and `/health/dependencies` truthfully report serving-optional degraded continuity-limited state.**

## What Happened

Extended `tests/test_phase10_outage_safety.py` with a serving-optional semantic-cache outage scenario that swaps in a degraded cache double, proves chat completions still succeed through the existing local stub path, and asserts the runtime health endpoints expose the typed `semantic_cache` degraded payload with `serving_optional`, `continuity_limited`, and `semantic_cache_unavailable` evidence. Updated `tests/test_health.py` with a focused readiness/dependencies regression covering degraded semantic-cache payloads, and expanded `tests/support.py` so cache doubles can express degraded health state without changing request-path behavior. During verification, the first attempt failed because a thrown lookup exception bypassed the production cache service’s internal graceful degradation and because the health payload includes the `enabled` field; I corrected the test double to emulate real fallback semantics and aligned assertions with the typed payload contract.

## Verification

Ran `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q` and confirmed the focused outage plus health verification suite passes (`10 passed`). This verifies both outage classes coexist with the established readiness contract: governance outages still fail closed, while semantic-cache outages degrade health truthfully without blocking successful local chat completions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q` | 1 | ❌ fail | 2285ms |
| 2 | `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q` | 0 | ✅ pass | 2221ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- `tests/support.py`
