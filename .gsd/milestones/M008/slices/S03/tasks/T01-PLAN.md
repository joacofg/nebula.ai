---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T01: Wire the retention cleanup lifecycle into the running gateway

Add a small retention lifecycle service that periodically invokes `GovernanceStore.delete_expired_usage_records()` using persisted `evidence_expires_at` markers only, tracks in-memory last-run diagnostics, and is started/stopped through the existing application lifecycle. Follow the existing background-service shape from `src/nebula/services/heartbeat_service.py` and `src/nebula/services/remote_management_service.py` rather than introducing a new framework abstraction. Add bounded settings in `src/nebula/core/config.py` for cleanup cadence and optional enablement, register the service in `src/nebula/core/container.py`, and start it from `src/nebula/main.py` alongside the current background services. Keep failures non-fatal to local serving but make them capturable for health inspection, and expose a deterministic single-run helper (for example `run_cleanup_once()`) so tests can exercise the real lifecycle seam without sleeping. Record expected executor skills in frontmatter as `fastapi-python`, `sqlalchemy-orm`, and `best-practices`. Include Failure Modes, Load Profile, and Negative Tests in the task plan because this task touches the database, background execution, app startup, and malformed/failing runtime states.

## Inputs

- ``src/nebula/services/governance_store.py``
- ``src/nebula/services/heartbeat_service.py``
- ``src/nebula/services/remote_management_service.py``
- ``src/nebula/core/config.py``
- ``src/nebula/core/container.py``
- ``src/nebula/main.py``

## Expected Output

- ``src/nebula/services/retention_lifecycle_service.py``
- ``src/nebula/core/config.py``
- ``src/nebula/core/container.py``
- ``src/nebula/main.py``
- ``tests/test_retention_lifecycle_service.py``

## Verification

./.venv/bin/pytest tests/test_retention_lifecycle_service.py tests/test_health.py -k "retention or lifecycle"

## Observability Impact

Adds lifecycle status and failure-state data that later health/hosted verification can inspect instead of inferring cleanup from code paths alone.
