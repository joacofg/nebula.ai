---
id: T01
parent: S05
milestone: M009
key_files:
  - docs/m009-integrated-proof.md
  - docs/route-decision-vocabulary.md
  - docs/architecture.md
key_decisions:
  - Kept the M009 close-out proof pointer-first and referential, with shared outcome-evidence terms defined in the route vocabulary instead of duplicated inside the integrated proof doc.
  - Scoped updates to additive discoverability links only so the task would not widen into new runtime, admin, or console behavior.
duration: 
verification_result: mixed
completed_at: 2026-04-27T21:36:24.434Z
blocker_discovered: false
---

# T01: Added the M009 integrated proof doc and linked shared vocabulary and architecture references so request-first happy/degraded review stays discoverable without redefining shipped seams.

**Added the M009 integrated proof doc and linked shared vocabulary and architecture references so request-first happy/degraded review stays discoverable without redefining shipped seams.**

## What Happened

I created `docs/m009-integrated-proof.md` in the same pointer-first style as the existing M006–M008 integrated proof walkthroughs. The new doc stays anchored to the existing seams only: the shared route vocabulary, one public `POST /v1/chat/completions` response, correlated `GET /v1/admin/usage/ledger?request_id=...`, `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, and selected-request-first Observability/request detail. I then made additive discoverability updates to `docs/route-decision-vocabulary.md` so `outcome_bonus`, `evidence_penalty`, and `outcome_evidence` are explicitly discoverable there, and added an architecture-guide link to `docs/m009-integrated-proof.md` so the close-out path is easy to find from the canonical overview. No runtime, API, or UI behavior changed; this task tightened the documentation boundary and anti-drift seams only.

## Verification

Ran the task’s explicit documentation verification gate. The first attempt failed because the shell environment does not provide a `python` executable. I tested that hypothesis directly and reran the same gate with `python3.12`, which passed. The passing check confirmed that `docs/m009-integrated-proof.md` exists, contains at least six section headings, includes the required request/ledger/replay/request-first phrases, that `docs/route-decision-vocabulary.md` now contains `outcome_bonus`, `evidence_penalty`, and `outcome_evidence`, and that `docs/architecture.md` links to `docs/m009-integrated-proof.md`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python - <<'PY' ... PY` | 127 | ❌ fail | 17ms |
| 2 | `python3.12 - <<'PY' ... PY` | 0 | ✅ pass | 44ms |

## Deviations

The task-plan verification command used `python`, but the local environment only exposed `python3.12`. I reran the same verification script with `python3.12` without changing the intended assertions.

## Known Issues

None.

## Files Created/Modified

- `docs/m009-integrated-proof.md`
- `docs/route-decision-vocabulary.md`
- `docs/architecture.md`
