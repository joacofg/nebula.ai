# TODOS

## Console / Design (deferred from /design-review 2026-07-13)

### Structural design backlog
**Priority:** P2
**Detail:** Mobile nav toggle below `lg`; componentize ~22 duplicated rose error banners; wire or delete dead tokens `--color-success`/`--color-danger` and unify rose-vs-pink danger; consolidate 76 magic `tracking-[…]` values into a token; trim happy-talk page headers; replace login 3-column feature grid; modal focus trap (Escape done); skeleton loading states; deployments table repeats identical posture sentence per row (needs coordinated test updates); form label casing (id/name/Description/active — asserted in tests). Full report: `~/.gstack/projects/joacofg-nebula.ai/designs/design-audit-20260713/`.

## Backend / API

### Admin create endpoints return 500 instead of 409 on duplicates
**Priority:** P2
**Noticed:** demo-polish rehearsal, 2026-07-16.
**Detail:** `POST /v1/admin/tenants` with an existing tenant id raises `ValueError("Tenant already exists")` (`src/nebula/services/governance_store.py:154`) which surfaces as HTTP 500; `create_api_key` has no duplicate guard at all. Both should return 409 with a clear detail message. Also: the api-key existence check in `scripts/seed_demo_data.py` matches revoked keys because `list_api_keys` doesn't filter `revoked_at` — fix alongside the 409 work.

### `budget_penalty` is a dead routing signal
**Priority:** P2
**Noticed:** eng review of the v4.0 Fase 1 plan, 2026-08-31.
**Detail:** `src/nebula/services/router_service.py:200` hardcodes `budget_penalty = 0.0`
and never reassigns it; `budget_proximity` stays `None` for every request. Both are
surfaced as routing signals in `X-Nebula-Route-Score` and persisted to the usage ledger,
so an operator who configures a tenant budget reasonably expects routing to respect it,
and it never does. Of the six score components this is the only one dead by hardcoded
value rather than by the `if` in `_decision_from_breakdown` ignoring the score entirely.
**Depends on:** Fase 2 (wiring `total_score` into the routing decision). Fixing this
before Fase 2 changes no behavior, because the score decides nothing today. Fix it as
part of Fase 2, not before. Full context:
`docs/designs/quality-measurement-routing-regret.md`.

## Completed

### Fix 18 pre-existing backend test failures (v2.0 in-flight work)
**Priority:** P0
**Completed:** 2026-08-24
**Resolution:** Root cause was eb9d666 (2026-04-27), which added the
outcome_evidence segment to policy_outcome and updated only the two test files
in its own GSD task scope. Parent commit 6f52d14 was 180 passed / 0 failed;
eb9d666 was 20 failed. Sixteen of those never got fixed. Also surfaced two real
product bugs: policy simulation flagged unchanged rows as changed, and
embeddings.py raised NameError on its own request-id fallback. `make test` is
198 passed, 0 failed.

### Fix broken vitest matcher and fixture types
**Priority:** P0
**Completed:** 2026-08-24
**Resolution:** `toBeSelected` does not exist in @testing-library/jest-dom at
any installed version, and the assertion was unreachable anyway because the
select is controlled. Replaced with the real controlled-component contract.
tsc --noEmit went 27 errors -> 0; ten of them were in production code
(policy-form.tsx reading TenantPolicy fields the type did not declare).
