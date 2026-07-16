# TODOS

## Backend / Tests

### Fix 18 pre-existing backend test failures (v2.0 in-flight work)
**Priority:** P0
**Noticed:** /ship on main, 2026-07-13. Pre-existing on origin/main (25 failing there; this branch fixes 7, none introduced).
**Detail:** Failures cluster around v2.0 hosted-control-plane features that look half-landed: policy simulation (`tests/test_governance_api.py`), outcome evidence / route signals (`tests/test_service_flows.py`, `tests/test_chat_completions.py`), usage-ledger filters (`tests/test_admin_playground_api.py`), reference migration tenant-header rules (`tests/test_reference_migration.py`), response headers (`tests/test_response_headers.py`). Run `make test` for the current list (18 as of 2026-07-13).

## Console / Tests

### Fix broken vitest matcher and fixture types
**Priority:** P0
**Noticed:** /ship on main, 2026-07-13. Pre-existing.
**Detail:** `console/src/components/ledger/ledger-filters.test.tsx:75` fails with "Invalid Chai property: toBeSelected" (jest-dom matcher not registered or wrong matcher name). Additionally 28 pre-existing `tsc --noEmit` errors in test fixtures (`UsageLedgerRecord` fields missing in ledger/policy/playground test fixtures, `toBeSelected` typing, e2e fixture literal).

## Console / Design (deferred from /design-review 2026-07-13)

### Structural design backlog
**Priority:** P2
**Detail:** Mobile nav toggle below `lg`; componentize ~22 duplicated rose error banners; wire or delete dead tokens `--color-success`/`--color-danger` and unify rose-vs-pink danger; consolidate 76 magic `tracking-[…]` values into a token; trim happy-talk page headers; replace login 3-column feature grid; modal focus trap (Escape done); skeleton loading states; deployments table repeats identical posture sentence per row (needs coordinated test updates); form label casing (id/name/Description/active — asserted in tests). Full report: `~/.gstack/projects/joacofg-nebula.ai/designs/design-audit-20260713/`.

## Backend / API

### Admin create endpoints return 500 instead of 409 on duplicates
**Priority:** P2
**Noticed:** demo-polish rehearsal, 2026-07-16.
**Detail:** `POST /v1/admin/tenants` with an existing tenant id raises `ValueError("Tenant already exists")` (`src/nebula/services/governance_store.py:154`) which surfaces as HTTP 500; `create_api_key` has no duplicate guard at all. Both should return 409 with a clear detail message. Also: the api-key existence check in `scripts/seed_demo_data.py` matches revoked keys because `list_api_keys` doesn't filter `revoked_at` — fix alongside the 409 work.

## Completed
