---
id: T01
parent: S03
milestone: M008
key_files:
  - src/nebula/services/retention_lifecycle_service.py
  - src/nebula/core/config.py
  - src/nebula/core/container.py
  - src/nebula/services/runtime_health_service.py
  - src/nebula/main.py
  - tests/test_retention_lifecycle_service.py
  - tests/test_health.py
key_decisions:
  - Implemented retention cleanup as a small service following the existing heartbeat/remote-management background loop pattern instead of introducing a new abstraction.
  - Published retention lifecycle state through `RuntimeHealthService` as an optional dependency so failures degrade health visibility without blocking local serving.
  - Verified persisted expiration-marker behavior by inserting exact ledger rows in tests rather than using `record_usage()`, which intentionally reapplies governance policy.
duration: 
verification_result: mixed
completed_at: 2026-04-12T00:53:46.960Z
blocker_discovered: false
---

# T01: Added the retention cleanup lifecycle service with startup wiring, health visibility, and deterministic lifecycle tests.

**Added the retention cleanup lifecycle service with startup wiring, health visibility, and deterministic lifecycle tests.**

## What Happened

Implemented `src/nebula/services/retention_lifecycle_service.py` as a lightweight background service following the same start/stop loop shape used by the existing heartbeat and remote-management services. The service periodically calls `GovernanceStore.delete_expired_usage_records()` against persisted `evidence_expires_at` markers, tracks in-memory runtime diagnostics (`last_run_at`, `last_attempted_run_at`, deleted/eligible counts, status, cutoff, and last error), and exposes a deterministic `run_cleanup_once()` helper so tests can exercise the real cleanup seam without sleeping. Added bounded configuration in `src/nebula/core/config.py` for enablement and cadence, registered the service in `src/nebula/core/container.py`, and started/stopped it from the FastAPI lifespan in `src/nebula/main.py`. Extended `RuntimeHealthService` so `/health/ready` and `/health/dependencies` now include a `retention_lifecycle` dependency payload that degrades on cleanup failure but does not make serving not-ready. Added `tests/test_retention_lifecycle_service.py` to verify expired-row deletion by persisted expiration marker, disabled-mode startup behavior, failure-state capture, and runtime-health exposure, and updated `tests/test_health.py` to assert the new dependency appears on readiness surfaces. During verification, I found my initial tests were incorrectly using `record_usage()`, which recomputes governance fields; I corrected them to insert exact ledger rows through `UsageLedgerModel`, matching the existing retention seam and preserving the intended persisted-marker behavior.

## Verification

Ran `./.venv/bin/pytest tests/test_retention_lifecycle_service.py tests/test_health.py -k "retention or lifecycle"`. The first run failed because the tests were creating records through `record_usage()`, which reapplies tenant policy and overwrites manually supplied expiration timestamps. After confirming that behavior against the existing governance retention tests, I updated the new lifecycle tests to insert exact `UsageLedgerModel` rows for persisted-marker assertions and reran the command successfully. The passing run verified: expired rows are deleted only when persisted `evidence_expires_at` is at or before the cleanup cutoff; rows with future or null expiration markers survive; failures are captured as degraded health state with last error and last attempted run time; disabled lifecycle mode does not start a background task; and the health surfaces expose the retention lifecycle dependency with truthful runtime state.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_retention_lifecycle_service.py tests/test_health.py -k "retention or lifecycle"` | 1 | ❌ fail | 6500ms |
| 2 | `./.venv/bin/pytest tests/test_retention_lifecycle_service.py tests/test_health.py -k "retention or lifecycle"` | 0 | ✅ pass | 2600ms |

## Deviations

Adjusted the new tests to insert `UsageLedgerModel` rows directly instead of using `GovernanceStore.record_usage()`. This was a local correction to honor the task’s requirement that cleanup use persisted expiration markers only, because `record_usage()` intentionally recomputes governance metadata from tenant policy.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/retention_lifecycle_service.py`
- `src/nebula/core/config.py`
- `src/nebula/core/container.py`
- `src/nebula/services/runtime_health_service.py`
- `src/nebula/main.py`
- `tests/test_retention_lifecycle_service.py`
- `tests/test_health.py`
