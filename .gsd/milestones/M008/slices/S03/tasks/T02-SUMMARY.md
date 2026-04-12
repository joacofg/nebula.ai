---
id: T02
parent: S03
milestone: M008
key_files:
  - tests/test_governance_api.py
  - tests/test_hosted_contract.py
  - console/src/components/health/runtime-health-cards.tsx
  - console/src/components/health/runtime-health-cards.test.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/lib/admin-api.ts
key_decisions:
  - Kept retention lifecycle operator proof on the existing dependency health cards instead of adding a dedicated retention UI surface.
  - Locked hosted export behavior with a heartbeat summary test so retention lifecycle health remains coarse metadata-only when sent to the hosted plane.
duration: 
verification_result: passed
completed_at: 2026-04-12T00:57:37.926Z
blocker_discovered: false
---

# T02: Exposed truthful retention lifecycle health on existing observability seams and verified cleanup deletes expired ledger rows through the running app seam.

**Exposed truthful retention lifecycle health on existing observability seams and verified cleanup deletes expired ledger rows through the running app seam.**

## What Happened

Extended the existing observability surfaces around the retention lifecycle introduced in T01 instead of creating any new retention dashboard. On the backend, I hardened end-to-end proof by updating the governance API test to seed expired, surviving, and no-expiration ledger rows through the normal app/admin path, invoke retention cleanup through the running container’s lifecycle service, and then verify `/v1/admin/usage/ledger` no longer returns the expired row while preserving future/null-expiration rows. I also added a hosted-contract regression test that drives `HeartbeatService._send_once()` with a real stored deployment credential and confirms the new `retention_lifecycle` dependency is summarized only as a coarse healthy/degraded/unavailable name set, with no detailed cleanup payload leaking into hosted metadata. On the console side, I widened the runtime-health dependency typing to accept richer dependency payloads, updated `RuntimeHealthCards` to render summary metrics like last status/run counts/error when present, and adjusted observability tests to confirm the existing dependency card area renders truthful retention lifecycle state without introducing a dedicated retention dashboard. During verification I hit two test-fixture mismatches: the hosted heartbeat test initially bypassed the real enrollment accessor incorrectly, and the observability fixture lacked newer ledger governance fields consumed by `LedgerRequestDetail`. I corrected both against the real seams and reran the full task verification successfully.

## Verification

Ran the task-plan verification command exactly: `./.venv/bin/pytest tests/test_governance_api.py tests/test_health.py tests/test_hosted_contract.py -k "retention or health or heartbeat" && npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx'`. The final passing run verified that health endpoints expose retention lifecycle state truthfully, hosted heartbeat export remains metadata-only and coarse even with the extra dependency, governed cleanup removes only rows whose persisted expiration markers are expired through the lifecycle service seam, and the console observability/runtime-health cards render retention lifecycle status/count/error details on existing cards without adding a new dashboard surface.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py tests/test_health.py tests/test_hosted_contract.py -k "retention or health or heartbeat"` | 0 | ✅ pass | 840ms |
| 2 | `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx'` | 0 | ✅ pass | 605ms |

## Deviations

Adjusted local test fixtures rather than production behavior in two places: the hosted-contract test had to persist a full local hosted identity via `_store_local_identity()` because `_send_once()` reads through `get_deployment_credential()`, and the observability page fixture needed the newer ledger governance fields expected by `LedgerRequestDetail`. These were local reality corrections, not contract changes.

## Known Issues

None.

## Files Created/Modified

- `tests/test_governance_api.py`
- `tests/test_hosted_contract.py`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/components/health/runtime-health-cards.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/lib/admin-api.ts`
