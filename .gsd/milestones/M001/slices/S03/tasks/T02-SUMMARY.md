---
id: T02
parent: S03
milestone: M001
provides:
  - Canonical human-facing migration guide that turns the tested chat-completions proof into a discoverable before/after adoption path with public-header and usage-ledger confirmation.
key_files:
  - docs/reference-migration.md
  - README.md
  - docs/quickstart.md
  - .gsd/milestones/M001/slices/S03/tasks/T02-PLAN.md
key_decisions:
  - The migration guide stays narrowly scoped to caller changes and verification surfaces, while deferring setup, contract semantics, and operating-model details to the existing canonical docs.
patterns_established:
  - Hand off from quickstart to the reference migration guide, then verify a migrated public request by pairing X-Nebula-* response headers and X-Request-ID with GET /v1/admin/usage/ledger?request_id=...
observability_surfaces:
  - docs/reference-migration.md, README.md documentation map, docs/quickstart.md next-step links, X-Nebula-* response headers, X-Request-ID, GET /v1/admin/usage/ledger
duration: 39m
verification_result: passed
completed_at: 2026-03-23 19:58:00 -03
blocker_discovered: false
---

# T02: Publish and wire the canonical migration guide

**Published a canonical reference migration guide and linked it from the main adoption flow without duplicating the contract or production-model docs.**

## What Happened

I started by reading the slice plan, task plan, task-summary template, prior T01 summary, the executable proof in `tests/test_reference_migration.py`, and the canonical docs the planner said this task must compose with rather than repeat. Before touching product docs, I fixed the pre-flight plan gap in `.gsd/milestones/M001/slices/S03/tasks/T02-PLAN.md` by adding an `## Observability Impact` section describing the public-header and usage-ledger signals that this documentation task must surface.

I then wrote `docs/reference-migration.md` as the single canonical human-facing migration proof for S03. The new guide is grounded in the tested proof path from `tests/test_reference_migration.py` and intentionally stays narrow: it shows a believable OpenAI-style before/after example, a small integration diff centered on Nebula base URL plus `X-Nebula-API-Key` and optional `X-Nebula-Tenant-ID`, and a verification flow that correlates public response evidence (`X-Nebula-*`, `X-Request-ID`) with operator evidence from `GET /v1/admin/usage/ledger?request_id=...`.

To keep the S01/S02 composition rules intact, I did not restate setup, contract, or operating-model canonicals. Instead, I linked the migration guide back to `docs/quickstart.md`, `docs/adoption-api-contract.md`, and `docs/production-model.md` at the points where readers need those boundaries.

Finally, I updated the doc entry points so the migration guide is discoverable from the main adoption flow: `README.md` now lists the reference migration guide in the documentation map, points to it from the quick-start adoption narrative, and references it from the selected public endpoint description; `docs/quickstart.md` now hands successful first-request users into the migration guide and includes it in related docs.

## Verification

I verified the new guide exists, contains the required migration/observability language, and is linked from the repo entry points without TODO/TBD placeholders. I also reran the slice-level proof commands that exercise the migration test harness and compilation check. The focused migration-proof test and compile check passed. The broader slice aggregate pytest command still fails only in the same pre-existing `tests/test_governance_api.py` expectations already documented in T01: one expected premium-model string no longer matches runtime defaults, and one explicit premium-request expectation conflicts with the currently observed default policy behavior.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/reference-migration.md && rg -n "reference migration|before|after|X-Nebula-API-Key|X-Nebula-Tenant-ID|usage ledger|adoption-api-contract|quickstart|production-model" docs/reference-migration.md README.md docs/quickstart.md` | 0 | ✅ pass | ~0.1s |
| 2 | `python3 - <<'PY' ... assert 'TODO' not in text and 'TBD' not in text ... PY` | 0 | ✅ pass | ~0.1s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_reference_migration.py tests/test_chat_completions.py tests/test_response_headers.py tests/test_governance_api.py -q` | 1 | ❌ fail | ~2.2s |
| 4 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_reference_migration.py -k "tenant_header or request_id or ledger" -q` | 0 | ✅ pass | ~0.9s |
| 5 | `python3 -m py_compile tests/test_reference_migration.py` | 0 | ✅ pass | ~0.1s |
| 6 | `test -f docs/reference-migration.md && rg -n "reference migration|X-Nebula-API-Key|X-Nebula-Tenant-ID|usage ledger|adoption-api-contract|quickstart|production-model" docs/reference-migration.md README.md` | 0 | ✅ pass | ~0.1s |

## Diagnostics

Future agents can inspect the shipped migration artifact directly in `docs/reference-migration.md`, then follow the discovery links from `README.md` and `docs/quickstart.md`. The runtime signals that the guide now makes explicit are the public `X-Nebula-*` headers, `X-Request-ID`, and operator-side confirmation through `GET /v1/admin/usage/ledger?request_id=...`. If the migration proof ever drifts, the quickest inspection path is:

1. read `docs/reference-migration.md`
2. compare it to `tests/test_reference_migration.py`
3. run the focused pytest command for `tenant_header`, `request_id`, and `ledger`
4. run the doc grep checks to confirm the repo entry points still point to the canonical guide

## Deviations

I updated `.gsd/milestones/M001/slices/S03/tasks/T02-PLAN.md` to add the missing `## Observability Impact` section required by the task pre-flight note. This was a contract-fix for the execution artifact, not a scope change.

## Known Issues

The broader slice aggregate suite still has the same unrelated failures already observed in T01:

- `tests/test_governance_api.py::test_policy_options_endpoint_is_admin_protected_and_includes_default_model` expects `openai/gpt-4o-mini`, but current runtime default config returns `gpt-4o-mini`.
- `tests/test_governance_api.py::test_usage_ledger_tracks_local_premium_cache_and_fallback_outcomes` expects an explicit premium request to complete, but the current runtime behavior records that scenario as `policy_denied` while fallback traffic still completes.

These failures did not block the documentation work or the focused migration-proof verification for this task.

## Files Created/Modified

- `docs/reference-migration.md` — Added the canonical human-facing before/after migration guide grounded in the tested proof path.
- `README.md` — Added discovery links so the migration guide appears in the documentation map, adoption flow, and public endpoint description.
- `docs/quickstart.md` — Added handoff links from first-request setup into the reference migration guide and related docs.
- `.gsd/milestones/M001/slices/S03/tasks/T02-PLAN.md` — Added the required observability-impact section for the task artifact.
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — Marked T02 complete.
