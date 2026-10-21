# TODOS

## Console / Design (deferred from /design-review 2026-07-13)

### Structural design backlog
**Priority:** P2
**Detail:** Mobile nav toggle below `lg`; componentize ~22 duplicated rose error banners; wire or delete dead tokens `--color-success`/`--color-danger` and unify rose-vs-pink danger; consolidate 76 magic `tracking-[…]` values into a token; trim happy-talk page headers; replace login 3-column feature grid; modal focus trap (Escape done); skeleton loading states; form label casing (id/name/Description/active — asserted in tests). Full report: `~/.gstack/projects/joacofg-nebula.ai/designs/design-audit-20260713/`.

## Gateway / Ledger (deferred from the 2026-10-21 backend-guardrails review)

### Mid-stream premium provider errors record cost 0
**Priority:** P2
**Detail:** When a premium stream fails after it has started sending chunks,
`_wrap_stream_with_ledger` records `terminal_status="provider_error"` with no
usage, so the row carries no cost even though the provider billed the tokens
already streamed. Spend skips `provider_error` rows too, so the hard budget undercounts
these requests (the same class of gap as B5, abandoned streams). Estimate usage
from the content already streamed, as the `client_disconnected` path does, and
decide whether those rows count toward spend.

### A stream abandoned before its first pull records no ledger row
**Priority:** P3
**Detail:** `chat_service` pulls the provider's first chunk (so an upstream
error becomes a 502 before the 200 is committed) before the ledger wrapper
starts. If the client disconnects before the server first pulls from the
wrapper, its `try`/`finally` never runs and no row is written, although a
premium provider already served (and billed) that chunk. Prime the wrapper
(start it before returning the response) or record the row from the route when
the response is torn down unstarted.

## Completed

### Admin create endpoints returned 500 instead of 409 on duplicates
**Priority:** P2
**Completed:** 2026-10-21
**Resolution:** The store raises typed errors that the admin routes map to
409 (duplicate tenant id or API-key secret), 404 (unknown tenant) and 422 (key
scoped to no tenant). `scripts/seed_demo_data.py` now recognises a revoked demo
key instead of treating it as missing.

### `budget_penalty` was a dead routing signal
**Priority:** P2
**Completed:** 2026-10-21
**Resolution:** Removed `budget_penalty` and `budget_proximity` from the score
breakdown, the route signals, the ledger payload and the console ledger detail.
Both were hardcoded to `0.0` / `None`, so `X-Nebula-Route-Score` keeps the same
value. Budgets stay enforced where they always were (hard-budget downgrade or
deny, per-request cap); ledger rows written before this change still carry the
two keys and the console ignores them.

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
