# S03 — Research

**Date:** 2026-04-11

## Summary

S03 is targeted research, not deep exploration. The risky architecture choice has already been made in S01/S02: evidence governance is stamped once at write time in `GovernanceStore.record_usage()` and retention deletion is already implemented as `GovernanceStore.delete_expired_usage_records(now=...)`. What is still missing for this slice is the **operational execution path** for that cleanup. Requirement ownership is centered on **R059** (real deletion, not UI-only hiding), while S03 also materially supports **R062** and must stay inside **R064** by avoiding any new retention dashboard, archive surface, or hosted authority expansion.

The natural implementation seam is the same app-lifecycle/background-loop pattern already used for `HeartbeatService` and `RemoteManagementService`. `main.py` starts those services during FastAPI lifespan startup and `ServiceContainer.shutdown()` stops them. There is currently **no retention worker, no cleanup cadence setting, and no health/diagnostic surface for cleanup execution**. Existing tests only prove the callable store method works when invoked directly. That leaves the product claim incomplete: retention is technically implemented, but not yet operationalized in the running gateway.

## Recommendation

Add a small, explicit **RetentionLifecycleService** that periodically calls `GovernanceStore.delete_expired_usage_records()` on the running gateway, tracks last-run/last-result state in memory, and exposes that state through the existing runtime health/dependency seam. Follow the established service pattern from `HeartbeatService` / `RemoteManagementService`: start in FastAPI lifespan, stop on shutdown, keep failures non-fatal but visible, and make the loop callable once for tests.

Do **not** add a new admin cleanup endpoint or a separate governance dashboard. S02 already established the governing rule: prove behavior through the existing `GET /v1/admin/usage/ledger` seam and request-detail/operator surfaces. For console work, keep changes bounded to observability/runtime-health copy if needed; do not broaden request detail beyond truthful explanation. This aligns with the loaded skills: `react-best-practices` reinforces minimizing serialized client data and preserving existing seams, and `userinterface-wiki` reinforces progressive disclosure / cognitive-load reduction instead of adding another surface.

## Implementation Landscape

### Key Files

- `src/nebula/services/governance_store.py` — Source of truth for governed usage persistence and retention cleanup. `delete_expired_usage_records(now=...)` already deletes rows by persisted `evidence_expires_at`, returns deterministic diagnostics (`eligible_count`, `deleted_count`, `cutoff`), and is the method the lifecycle service should call. Do not duplicate cleanup SQL elsewhere.
- `src/nebula/main.py` — FastAPI lifespan startup/shutdown. Currently starts `heartbeat_service` and `remote_management_service`; this is the right place to start/stop a retention lifecycle worker.
- `src/nebula/core/container.py` — Wires all services. Add the new retention lifecycle service here, initialize it with `settings` + `governance_store`, and stop it in `shutdown()`.
- `src/nebula/core/config.py` — Add bounded settings for retention execution cadence and maybe an enable flag if needed. Existing pattern: `remote_management_poll_interval_seconds` is the closest example.
- `src/nebula/services/heartbeat_service.py` — Best reference for a simple background loop with `start()`, `stop()`, `_loop()`, and a single-run helper. Retention should copy this structure, but call local store cleanup instead of HTTP.
- `src/nebula/services/remote_management_service.py` — Best reference for a loop that reads interval from settings and exposes a directly callable `poll_and_apply_once()` method. Retention service should likely expose `run_cleanup_once()` similarly for deterministic tests.
- `src/nebula/services/runtime_health_service.py` — Existing dependency/status aggregator. Add a `retention_lifecycle` dependency payload here so cleanup execution is observable through `/health/ready`, `/health/dependencies`, and the console runtime-health query.
- `src/nebula/models/heartbeat.py` — Documents dependency-summary shape. If a new dependency is surfaced through runtime health, hosted heartbeat dependency summaries may start including `retention_lifecycle` automatically via `HeartbeatService._summarize_deps()`; verify this is acceptable and bounded.
- `src/nebula/api/routes/admin.py` — No retention-specific route exists and none is needed. Existing `/usage/ledger` remains the proof seam before/after cleanup.
- `tests/test_governance_api.py` — Already has the direct deletion proof (`test_governed_usage_ledger_cleanup_deletes_only_rows_with_persisted_expiration_markers`). Extend with app/runtime-level lifecycle tests rather than replacing this coverage.
- `tests/support.py` — `configured_app()` builds a migrated app with real lifespan wiring; ideal for integration tests that verify startup-registered cleanup execution without inventing custom harnesses.
- `console/src/app/(console)/observability/page.tsx` — Existing runtime-health consumer. Only touch if the new health dependency needs explicit rendering/copy.
- `console/src/components/health/runtime-health-cards.tsx` — Existing dependency-health presentation surface if retention lifecycle status should be visible to operators.
- `console/src/components/ledger/ledger-request-detail.tsx` — Already explains that request detail disappears after governed cleanup. Avoid expanding this into a retention control surface.
- `console/src/lib/admin-api.ts` — Mirrors runtime health / admin contracts on the console side if backend health payload shape changes.

### Build Order

1. **Operationalize backend cleanup first**: add the retention lifecycle service and wire it into `ServiceContainer` + `main.py`. This is the core S03 deliverable for R059 and unblocks all meaningful verification.
2. **Make cleanup observable second**: expose lifecycle status through `RuntimeHealthService` so retention execution is not inferred from code alone. This gives the slice a bounded operational proof path without adding new APIs.
3. **Add runtime/integration tests third**: verify expired rows are actually deleted by the running lifecycle service and that failures/status are surfaced truthfully.
4. **Only then adjust console/runtime-health UI if necessary**: keep UI changes minimal and subordinate to the existing observability/dependency-health surface.

### Verification Approach

- Backend targeted tests:
  - `./.venv/bin/pytest tests/test_governance_api.py -k "retention or expired or ledger"`
  - Add/extend tests to prove the lifecycle service runs cleanup through the app/service seam, not only by direct store invocation.
- Service-level tests:
  - `./.venv/bin/pytest tests/test_service_flows.py -k "retention or health"`
  - If a new service test file is added, verify `run_cleanup_once()` behavior, last-run diagnostics, and failure handling.
- Hosted-boundary regression:
  - `./.venv/bin/pytest tests/test_hosted_contract.py`
  - Needed because runtime dependencies feed heartbeat summaries; ensure hosted metadata-only boundary stays intact and no retention detail leaks into hosted scope.
- Chat/embeddings regression:
  - `./.venv/bin/pytest tests/test_chat_completions.py -k ledger`
  - `./.venv/bin/pytest tests/test_embeddings_api.py`
  - Confirms the shared governed write seam still stamps retention markers that the lifecycle service later consumes.
- Console verification if health surface changes:
  - `npm --prefix console run test -- --run src/app/(console)/observability/page.test.tsx src/components/health/runtime-health-cards.test.tsx src/components/ledger/ledger-request-detail.test.tsx`
- Observable behavior to prove manually/in-tests:
  - create an expired governed row
  - allow/invoke lifecycle cleanup on the running app
  - confirm `/v1/admin/usage/ledger` no longer returns the expired row while surviving/no-expiration rows remain
  - confirm runtime health reports retention lifecycle status/last result truthfully

## Constraints

- Retention deletion must stay keyed to **persisted** `evidence_expires_at`, not recomputed from current tenant policy. `GovernanceStore.delete_expired_usage_records()` already does this; the lifecycle layer should only schedule/invoke it.
- Keep the operator proof path on existing seams: `/v1/admin/usage/ledger`, request detail, and runtime health. Do not add a retention-specific admin endpoint or archive/recovery path.
- Failures should be visible but not widen authority: startup should not fail open into hidden behavior, and hosted export must remain metadata-only.
- Console work should remain subordinate to existing observability surfaces. `userinterface-wiki` rules `ux-progressive-disclosure` and `ux-cognitive-load-reduce` apply here; avoid new dashboard sprawl.
- If runtime health adds retention lifecycle data, keep client payload minimal per `react-best-practices` `server-serialization` / `server-dedup-props` guidance.

## Common Pitfalls

- **Recomputing expiration from current policy** — Avoid any worker logic that derives deletion eligibility from `TenantPolicy.evidence_retention_window`; use only row-level `evidence_expires_at`.
- **Creating a second cleanup implementation** — The service should call `GovernanceStore.delete_expired_usage_records()` directly, not copy its SQL/filtering logic.
- **Making cleanup failures invisible** — A background loop that only logs warnings is insufficient for this slice; also persist in-memory last-run status so health surfaces can show degraded/not_ready truthfully.
- **Turning request detail into a lifecycle console** — `ledger-request-detail.tsx` already has the correct bounded explanation. Prefer dependency health / observability for runtime execution visibility.

## Open Risks

- Adding `retention_lifecycle` to runtime dependencies may affect hosted heartbeat summaries because `HeartbeatService._summarize_deps()` forwards dependency names generically; verify that this extra dependency name does not violate any hosted expectations.
- There is no existing generic background-service base class, so retention will likely mirror heartbeat/remote-management patterns manually. Keep it small to avoid inventing framework-y abstractions in a bounded slice.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js console | installed `react-best-practices` | available |
| UI/UX bounded operator surfaces | installed `userinterface-wiki` | available |
| FastAPI | `mindrally/skills@fastapi-python` | available via `npx skills add mindrally/skills@fastapi-python` |
| SQLAlchemy / Alembic | `bobmatnyc/claude-mpm-skills@sqlalchemy-orm` | available via `npx skills add bobmatnyc/claude-mpm-skills@sqlalchemy-orm` |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | available via `npx skills add wshobson/agents@nextjs-app-router-patterns` |
