# S03: Retention lifecycle enforcement

**Goal:** Operationalize governed evidence retention as a running cleanup lifecycle that deletes expired usage-ledger rows by persisted expiration markers, exposes truthful runtime status through existing health surfaces, and keeps operator proof on the current ledger/observability seams.
**Demo:** Expired evidence is actually deleted according to tenant policy, with a bounded retention execution path that can be exercised and verified rather than inferred.

## Must-Haves

- Expired usage-ledger evidence is deleted by a running lifecycle service that calls the existing `GovernanceStore.delete_expired_usage_records()` seam rather than duplicating cleanup logic.
- Cleanup eligibility remains keyed to persisted `evidence_expires_at` markers, not recomputed from current tenant policy.
- Runtime health exposes retention lifecycle status and failure diagnostics through existing health/dependency surfaces.
- `/v1/admin/usage/ledger` and existing observability surfaces provide the proof path before/after cleanup without adding a retention-specific endpoint or dashboard.
- Hosted metadata-only summaries remain bounded after the new dependency is introduced.

## Proof Level

- This slice proves: operational

## Integration Closure

Compose the new retention lifecycle service into `ServiceContainer` and FastAPI lifespan, surface it through `RuntimeHealthService` and heartbeat dependency summaries, and leave no separate cleanup trigger surface for later slices to wire.

## Verification

- Runtime signals: retention lifecycle last-run timestamp, deleted/eligible counts, status, and last error kept in memory by the lifecycle service.
- Inspection surfaces: `/health/ready`, `/health/dependencies`, existing observability dependency cards, and `/v1/admin/usage/ledger` before/after cleanup.
- Failure visibility: degraded/not_ready retention dependency state plus last failure detail and last attempted run time.
- Redaction constraints: expose only summary counts/timestamps/errors; never raw request evidence or hosted-authority expansion.

## Tasks

- [x] **T01: Wire the retention cleanup lifecycle into the running gateway** `est:1h`
  Add a small retention lifecycle service that periodically invokes `GovernanceStore.delete_expired_usage_records()` using persisted `evidence_expires_at` markers only, tracks in-memory last-run diagnostics, and is started/stopped through the existing application lifecycle. Follow the existing background-service shape from `src/nebula/services/heartbeat_service.py` and `src/nebula/services/remote_management_service.py` rather than introducing a new framework abstraction. Add bounded settings in `src/nebula/core/config.py` for cleanup cadence and optional enablement, register the service in `src/nebula/core/container.py`, and start it from `src/nebula/main.py` alongside the current background services. Keep failures non-fatal to local serving but make them capturable for health inspection, and expose a deterministic single-run helper (for example `run_cleanup_once()`) so tests can exercise the real lifecycle seam without sleeping. Record expected executor skills in frontmatter as `fastapi-python`, `sqlalchemy-orm`, and `best-practices`. Include Failure Modes, Load Profile, and Negative Tests in the task plan because this task touches the database, background execution, app startup, and malformed/failing runtime states.
  - Files: `src/nebula/core/config.py`, `src/nebula/core/container.py`, `src/nebula/main.py`, `src/nebula/services/governance_store.py`, `src/nebula/services/retention_lifecycle_service.py`
  - Verify: ./.venv/bin/pytest tests/test_retention_lifecycle_service.py tests/test_health.py -k "retention or lifecycle"

- [x] **T02: Expose retention lifecycle health and prove end-to-end deletion through real seams** `est:1h`
  Extend runtime health to include a `retention_lifecycle` dependency payload with truthful readiness/degraded state, last-run timestamps/results, and last error details while keeping the hosted plane metadata-only and bounded to dependency summaries rather than raw cleanup payloads. Use the lifecycle service added in T01 as the single source for this health data. Add backend tests that seed expired and surviving governed rows through the normal ledger path, invoke lifecycle cleanup through the running app/container seam, and verify `/v1/admin/usage/ledger` no longer returns expired rows while surviving/no-expiration rows remain. Re-verify hosted heartbeat/dependency summary behavior so the extra dependency name does not widen the export contract, and add/update console runtime-health tests only as needed to confirm the new dependency renders truthfully in existing observability cards without creating a retention dashboard. Keep request-detail/operator proof on existing seams. Record expected executor skills in frontmatter as `fastapi-python`, `react-best-practices`, and `userinterface-wiki`. Include Failure Modes, Load Profile, and Negative Tests in the task plan because this task spans app health, hosted summarization, operator surfaces, and retention edge cases.
  - Files: `src/nebula/services/runtime_health_service.py`, `src/nebula/services/heartbeat_service.py`, `tests/test_governance_api.py`, `tests/test_health.py`, `tests/test_hosted_contract.py`, `console/src/components/health/runtime-health-cards.tsx`, `console/src/components/health/runtime-health-cards.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py tests/test_health.py tests/test_hosted_contract.py -k "retention or health or heartbeat" && npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx src/app/(console)/observability/page.test.tsx

## Files Likely Touched

- src/nebula/core/config.py
- src/nebula/core/container.py
- src/nebula/main.py
- src/nebula/services/governance_store.py
- src/nebula/services/retention_lifecycle_service.py
- src/nebula/services/runtime_health_service.py
- src/nebula/services/heartbeat_service.py
- tests/test_governance_api.py
- tests/test_health.py
- tests/test_hosted_contract.py
- console/src/components/health/runtime-health-cards.tsx
- console/src/components/health/runtime-health-cards.test.tsx
- console/src/app/(console)/observability/page.test.tsx
