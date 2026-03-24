---
id: T02
parent: S03
milestone: M003
provides:
  - Canonical human-readable embeddings migration proof documentation plus pointer-only discoverability links back to the contract and entry docs.
key_files:
  - docs/embeddings-reference-migration.md
  - docs/embeddings-adoption-contract.md
  - README.md
  - docs/architecture.md
  - .gsd/milestones/M003/slices/S03/S03-PLAN.md
  - .gsd/milestones/M003/slices/S03/tasks/T02-PLAN.md
key_decisions:
  - Keep `docs/embeddings-adoption-contract.md` as the only detailed embeddings boundary and make the new migration guide explicitly subordinate to the executable proof plus contract.
patterns_established:
  - For adoption docs, pair a source-of-truth executable proof with a pointer-only migration guide and entry-doc links instead of duplicating contract details across multiple markdown surfaces.
observability_surfaces:
  - `docs/embeddings-reference-migration.md`, `tests/test_embeddings_reference_migration.py`, public `/v1/embeddings` response headers, and `GET /v1/admin/usage/ledger?request_id=...`.
duration: 33m
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T02: Publish the embeddings migration guide and wire discoverability

**Published the executable-proof-backed embeddings migration guide and added pointer-only discoverability links from the contract and entry docs.**

## What Happened

I first read the existing chat migration guide, the executable embeddings migration proof, the embeddings adoption contract, the slice plan, and the prior task summary so the new documentation stayed derived from live proof rather than inventing a broader story. I also fixed the pre-flight observability gap in `.gsd/milestones/M003/slices/S03/tasks/T02-PLAN.md` by adding an `## Observability Impact` section describing the preserved proof signals, inspection path, and doc-drift failure visibility.

I then created `docs/embeddings-reference-migration.md` as the canonical human-readable migration proof for embeddings. The guide names `tests/test_embeddings_reference_migration.py` as the source of truth, mirrors the credible before/after shape of the existing chat migration document, and keeps the examples deliberately narrow: same OpenAI Python client, same `client.embeddings.create(...)` call, same tested `model` and `input`, and only the base URL, placeholder client `api_key`, and `default_headers={"X-Nebula-API-Key": ...}` changed.

The new guide also documents how to prove the migration worked with the exact observability surfaces exercised by the runtime proof: inspect the OpenAI-like embeddings response shape, record `X-Request-ID`, verify the `X-Nebula-*` evidence headers, and correlate the same request through `GET /v1/admin/usage/ledger?request_id=...`. It explicitly preserves the metadata-only ledger boundary by warning that raw `input` text and returned embedding vectors are not part of the durable admin evidence.

Finally, I added pointer-only cross-links from `docs/embeddings-adoption-contract.md`, `README.md`, and `docs/architecture.md` so readers can find the guide without turning those files into a second embeddings contract. I also marked T02 complete in `.gsd/milestones/M003/slices/S03/S03-PLAN.md`.

## Verification

I ran the task-level doc checks to confirm the guide exists, has sufficient section structure, contains the required migration-proof terms, and is discoverable through cross-links from the contract and entry docs. I also ran the slice verification commands in the worktree context: the executable migration proof test, the embeddings API test module, the governance embeddings correlation check, and the embeddings upstream-failure regression check. All passed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/embeddings-reference-migration.md && ! grep -q "TBD\|TODO" docs/embeddings-reference-migration.md && [ "$(rg -c "^## " docs/embeddings-reference-migration.md)" -ge 6 ]` | 0 | ✅ pass | <1s |
| 2 | `rg -n "tests/test_embeddings_reference_migration.py|X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|What this migration proves|What not to use as migration proof" docs/embeddings-reference-migration.md` | 0 | ✅ pass | <1s |
| 3 | `rg -n "embeddings-reference-migration" docs/embeddings-adoption-contract.md README.md docs/architecture.md docs/*.md` | 0 | ✅ pass | <1s |
| 4 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py` | 0 | ✅ pass | 0.91s |
| 5 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` | 0 | ✅ pass | 1.15s |
| 6 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 0 | ✅ pass | 0.91s |
| 7 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py -k upstream_failures` | 0 | ✅ pass | 0.94s |

## Diagnostics

Future agents should inspect `docs/embeddings-reference-migration.md` first for the human-readable migration path, then compare it against `tests/test_embeddings_reference_migration.py` for the executable source of truth. The durable runtime inspection surfaces remain the public `/v1/embeddings` response headers (`X-Request-ID` plus the embeddings `X-Nebula-*` set) and `GET /v1/admin/usage/ledger?request_id=...` for metadata-only correlation.

## Deviations

None.

## Known Issues

The slice-level verification commands in the milestone plan are written as repository-root invocations, but this auto-mode task runs inside the worktree. I executed the same commands from the required worktree directory, which resolved the paths correctly and exercised the intended checks.

## Files Created/Modified

- `docs/embeddings-reference-migration.md` — Added the canonical embeddings migration guide derived from the executable proof, with before/after examples, observability verification steps, and explicit non-proof boundaries.
- `docs/embeddings-adoption-contract.md` — Added a pointer-only link to the migration guide while keeping the contract doc as the sole detailed embeddings boundary.
- `README.md` — Added a documentation-map entry so adopters can discover the new embeddings migration guide.
- `docs/architecture.md` — Added a pointer-only discoverability link to the embeddings migration guide from the high-level architecture description.
- `.gsd/milestones/M003/slices/S03/tasks/T02-PLAN.md` — Added the missing `## Observability Impact` section required by the pre-flight instruction.
- `.gsd/milestones/M003/slices/S03/S03-PLAN.md` — Marked T02 complete.
