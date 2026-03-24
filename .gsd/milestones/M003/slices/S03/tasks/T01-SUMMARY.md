---
id: T01
parent: S03
milestone: M003
provides:
  - Executable embeddings migration proof coverage that locks the public `/v1/embeddings` happy path, evidence headers, and request-id ledger correlation.
key_files:
  - tests/test_embeddings_reference_migration.py
  - .gsd/milestones/M003/slices/S03/S03-PLAN.md
key_decisions:
  - Keep the proof narrow by stubbing only `embeddings_service.create_embeddings` inside `configured_app()` and asserting the public route plus persisted ledger metadata rather than introducing helper abstractions or unsupported auth/options.
patterns_established:
  - Mirror the reference-migration test style with exact public-evidence assertions and explicit metadata-redaction checks against the usage ledger.
observability_surfaces:
  - Public `/v1/embeddings` response headers, `GET /v1/admin/usage/ledger?request_id=...`, and the targeted `tests/test_embeddings_api.py -k upstream_failures` failure-surface regression.
duration: 35m
verification_result: passed
completed_at: 2026-03-23T23:53:00-03:00
blocker_discovered: false
---

# T01: Add executable embeddings migration proof coverage

**Added a focused embeddings migration proof test that validates `/v1/embeddings` success evidence and metadata-only ledger correlation.**

## What Happened

I first read the existing chat migration proof, embeddings API tests, governance ledger assertions, the embeddings adoption contract, and the embeddings route so the new proof stayed inside the already-shipped boundary. I also fixed the pre-flight observability gap in `.gsd/milestones/M003/slices/S03/S03-PLAN.md` by adding an explicit failure-surface verification step for embeddings upstream failures.

I then created `tests/test_embeddings_reference_migration.py` as the executable proof for the minimal-change migration story. The test uses `configured_app()` and overrides only `app.state.container.embeddings_service.create_embeddings` with a deterministic stub, so it still exercises the real public `POST /v1/embeddings` route, public response headers, request-id generation, and usage-ledger persistence path.

The proof sends a realistic OpenAI-style embeddings request body authenticated only with `X-Nebula-API-Key`, captures `X-Request-ID`, fetches `GET /v1/admin/usage/ledger?request_id=...`, and asserts the returned body shape, exact `X-Nebula-*` headers, and matching persisted metadata. It also explicitly checks the redaction boundary by confirming the ledger row does not expose raw request input strings or returned embedding vectors.

## Verification

I ran the new proof test directly, re-ran the existing governance embeddings correlation test to ensure no regression in the durable evidence path, and ran the added embeddings upstream-failure check to confirm the slice now includes an inspectable diagnostic surface.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest /Users/joaquinfernandezdegamboa/Proj/nebula/.gsd/worktrees/M003/tests/test_embeddings_reference_migration.py` | 0 | ✅ pass | 12.6s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest /Users/joaquinfernandezdegamboa/Proj/nebula/.gsd/worktrees/M003/tests/test_governance_api.py -k embeddings` | 0 | ✅ pass | 8.6s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest /Users/joaquinfernandezdegamboa/Proj/nebula/.gsd/worktrees/M003/tests/test_embeddings_api.py -k upstream_failures` | 0 | ✅ pass | 4.5s |

## Diagnostics

The primary inspection surfaces are the assertions in `tests/test_embeddings_reference_migration.py`, the public `/v1/embeddings` response headers (`X-Request-ID` plus the embeddings `X-Nebula-*` set), and `GET /v1/admin/usage/ledger?request_id=...` for durable metadata correlation. The added `tests/test_embeddings_api.py -k upstream_failures` check is the slice-level failure-path diagnostic for embeddings route regressions.

## Deviations

None.

## Known Issues

The slice-level verification commands provided in plan documents use repository-root test paths, but this auto-mode task executes in a worktree. I verified the same commands against absolute paths inside `/Users/joaquinfernandezdegamboa/Proj/nebula/.gsd/worktrees/M003/`, which is the local execution context required by the task.

## Files Created/Modified

- `tests/test_embeddings_reference_migration.py` — Added the executable embeddings migration proof with body, header, ledger, and redaction-boundary assertions.
- `.gsd/milestones/M003/slices/S03/S03-PLAN.md` — Added an explicit embeddings failure-surface verification step to satisfy the pre-flight observability requirement.
