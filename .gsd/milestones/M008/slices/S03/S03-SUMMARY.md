---
id: S03
parent: M008
milestone: M008
provides:
  - A running retention cleanup lifecycle wired into app startup and shutdown.
  - Truthful bounded health diagnostics for retention execution and failures.
  - An operational proof path showing real evidence deletion through existing ledger and observability seams.
requires:
  - slice: S01
    provides: Typed evidence retention policy fields and persisted row-level governance markers including `evidence_expires_at`.
  - slice: S02
    provides: The explicit governance-store deletion seam and historically truthful ledger/request-detail evidence model that S03 operationalizes.
affects:
  - S04
  - S05
key_files:
  - src/nebula/services/retention_lifecycle_service.py
  - src/nebula/core/config.py
  - src/nebula/core/container.py
  - src/nebula/main.py
  - src/nebula/services/runtime_health_service.py
  - src/nebula/services/heartbeat_service.py
  - tests/test_retention_lifecycle_service.py
  - tests/test_governance_api.py
  - tests/test_health.py
  - tests/test_hosted_contract.py
  - console/src/components/health/runtime-health-cards.tsx
  - console/src/components/health/runtime-health-cards.test.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/lib/admin-api.ts
key_decisions:
  - Implemented retention cleanup as a small background lifecycle service following the existing heartbeat/remote-management loop pattern instead of introducing a new abstraction.
  - Kept operator proof on existing runtime-health cards and `/v1/admin/usage/ledger` rather than adding a retention-specific endpoint or dashboard.
  - Preserved the hosted metadata-only boundary by reducing the new dependency to coarse heartbeat summary membership only.
patterns_established:
  - Use persisted row-level governance markers as the source of truth for later lifecycle behavior; do not recompute cleanup eligibility from current tenant policy.
  - For bounded runtime features, publish optional dependency state through `RuntimeHealthService` so failures are visible without unnecessarily blocking local serving.
  - When verifying historical governance behavior, seed exact ledger rows instead of calling write-time governance seams that intentionally recompute policy-derived fields.
observability_surfaces:
  - `/health/ready` retention_lifecycle dependency payload
  - `/health/dependencies` retention_lifecycle dependency payload
  - Console Observability runtime-health dependency cards
  - Hosted heartbeat dependency summary (coarse healthy/degraded/unavailable membership only)
  - `/v1/admin/usage/ledger` before/after cleanup proof path
drill_down_paths:
  - .gsd/milestones/M008/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-12T17:03:23.552Z
blocker_discovered: false
---

# S03: Retention lifecycle enforcement

**Operationalized governed evidence deletion as a running retention lifecycle that deletes expired ledger rows by persisted expiration markers, reports truthful runtime status through existing health/observability seams, and keeps hosted export bounded to coarse dependency metadata.**

## What Happened

S03 turned the governed deletion seam from S02 into a real runtime lifecycle without widening Nebula’s trust boundary. The backend now includes a dedicated `RetentionLifecycleService` that follows the existing background-service shape already used for heartbeat and remote-management loops. It is registered in the service container, started and stopped from FastAPI lifespan, and controlled by bounded settings for enablement and cleanup cadence. The lifecycle calls `GovernanceStore.delete_expired_usage_records()` directly and therefore deletes evidence only according to each row’s persisted `evidence_expires_at` marker rather than recomputing eligibility from current tenant policy. The service keeps in-memory execution diagnostics — last status, last run and attempt timestamps, deleted and eligible counts, cutoff, and last error — so operators can inspect runtime truth without exposing raw evidence.

That operational state is now surfaced on the existing runtime-health seams rather than through a new retention product surface. `RuntimeHealthService` publishes a `retention_lifecycle` dependency payload on `/health/ready` and `/health/dependencies`, and optional degradation from cleanup failures is visible without blocking local serving. The existing hosted heartbeat summary was reverified so the new dependency remains reduced to coarse healthy/degraded/unavailable membership only, preserving the metadata-only hosted boundary. On the operator side, the console runtime-health cards now render retention lifecycle status, counts, timestamps, and last error on the existing observability dependency cards. There is no new retention-specific endpoint or dashboard; before/after proof remains on the existing `/v1/admin/usage/ledger` seam.

End-to-end proof was tightened around the real seams. Tests now seed expired, surviving, and no-expiration rows, invoke cleanup through the running lifecycle service, and verify expired rows disappear from `/v1/admin/usage/ledger` while future or null-expiration rows remain. Health tests prove the dependency appears on readiness surfaces, and hosted-contract coverage proves the added dependency name does not widen exported payload detail. During execution, one important lesson emerged: tests that need historical expiration markers must not use `GovernanceStore.record_usage()`, because that seam intentionally reapplies current governance policy and will overwrite hand-crafted expiration timestamps. Direct ledger-row insertion is the correct pattern when proving persisted-marker deletion behavior.

Overall, the slice delivers the bounded operational claim M008 needed: retention is now enforced as real deletion performed by a running lifecycle, operators can inspect whether that lifecycle is healthy or degraded through existing health and observability surfaces, and Nebula still avoids payload capture, archive semantics, or hosted-authority drift.

## Verification

Passed the slice-plan verification checks. Backend verification: `./.venv/bin/pytest tests/test_governance_api.py tests/test_health.py tests/test_hosted_contract.py -k "retention or health or heartbeat"` → 5 selected tests passed. Console verification: `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx'` → 2 files / 3 tests passed. These checks verified: retention lifecycle dependency state appears on `/health/ready` and `/health/dependencies`; cleanup through the lifecycle service removes only rows whose persisted `evidence_expires_at` is expired while preserving future/null-expiration rows; hosted heartbeat export stays metadata-only and coarse despite the new dependency; and the console observability runtime-health cards render truthful retention lifecycle status/count/error details on the existing dependency-card surface.

## Requirements Advanced

- R062 — Provides the operational deletion and runtime-health leg needed for the end-to-end governance chain proof in M008/S05.
- R064 — Proves retention enforcement while keeping scope bounded to existing health, ledger, and hosted-summary seams instead of adding payload capture or new compliance surfaces.

## Requirements Validated

- R059 — Validated by passing backend and console slice verification showing that the running lifecycle deletes expired ledger rows by persisted `evidence_expires_at`, exposes truthful health state, and keeps hosted export metadata-only.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Console verification initially failed because the shell interpreted the unquoted `src/app/(console)/observability/page.test.tsx` path. Re-running the exact Vitest command with that path quoted resolved the shell issue; no product code change was required. Earlier task execution also corrected tests that had mistakenly used `record_usage()` when direct ledger-row insertion was required to preserve historical expiration markers.

## Known Limitations

Retention lifecycle diagnostics are kept in memory only. They provide truthful current-process status for health and observability, but they do not yet persist historical run history across process restarts.

## Follow-ups

S04 should build directly on these seams by making the effective evidence boundary clearer in request-detail and policy/operator surfaces without adding a separate retention console. S05 should use the running lifecycle, health dependency, and before/after ledger proof path as the operational leg of the final end-to-end governance proof.

## Files Created/Modified

- `src/nebula/services/retention_lifecycle_service.py` — Added the retention cleanup background service, health snapshot model, and deterministic single-run helper.
- `src/nebula/core/config.py` — Added bounded settings for retention lifecycle enablement and cleanup cadence.
- `src/nebula/core/container.py` — Registered the retention lifecycle service in the service container.
- `src/nebula/main.py` — Started the retention lifecycle service from FastAPI lifespan and shut it down with the app.
- `src/nebula/services/runtime_health_service.py` — Exposed `retention_lifecycle` as an optional dependency in runtime health output.
- `src/nebula/services/heartbeat_service.py` — Reused dependency summaries so hosted heartbeat sees the new dependency only as coarse healthy/degraded/unavailable state.
- `tests/test_retention_lifecycle_service.py` — Added lifecycle tests for expired-row deletion, disabled mode, failure capture, and health visibility.
- `tests/test_governance_api.py` — Added end-to-end ledger proof that expired rows disappear after lifecycle cleanup while surviving rows remain.
- `tests/test_health.py` — Verified health endpoints include the retention lifecycle dependency and degraded semantics.
- `tests/test_hosted_contract.py` — Locked the hosted metadata-only dependency summary contract with the added retention lifecycle dependency.
- `console/src/components/health/runtime-health-cards.tsx` — Rendered retention lifecycle status, counts, timestamps, and last error on existing runtime-health cards.
- `console/src/components/health/runtime-health-cards.test.tsx` — Verified runtime-health cards render retention lifecycle diagnostics truthfully.
- `console/src/app/(console)/observability/page.test.tsx` — Verified the Observability page continues to show the lifecycle on existing health surfaces without a new dashboard.
- `console/src/lib/admin-api.ts` — Widened runtime-health dependency typing so richer lifecycle payload fields can be consumed safely.
