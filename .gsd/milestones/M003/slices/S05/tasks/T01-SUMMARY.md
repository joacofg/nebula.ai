---
id: T01
parent: S05
milestone: M003
provides:
  - Embeddings-specific integrated adoption walkthrough that preserves the public-request to ledger to Observability proof order without duplicating the canonical contract
key_files:
  - docs/embeddings-integrated-adoption-proof.md
  - .gsd/milestones/M003/slices/S05/tasks/T01-PLAN.md
  - .gsd/milestones/M003/slices/S05/S05-PLAN.md
key_decisions:
  - Kept Observability explicitly subordinate to public response headers plus usage-ledger correlation, mirroring the established integrated-proof structure for embeddings
patterns_established:
  - Final assembly docs should delegate detailed API semantics to the contract doc, delegate realistic migration diffs to the migration guide and executable test, and name failure modes that expose scope drift
observability_surfaces:
  - docs/embeddings-integrated-adoption-proof.md
  - tests/test_embeddings_reference_migration.py
  - console/e2e/observability.spec.ts
  - GET /v1/admin/usage/ledger?request_id=...
duration: 39m
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T01: Author the embeddings integrated adoption walkthrough

**Added the embeddings integrated adoption walkthrough and anchored it to the existing public-response, usage-ledger, and Observability proof seams without creating a second contract surface.**

## What Happened

I first read the task inputs and the existing integrated adoption precedent to mirror the established proof shape rather than improvising a new one. I also fixed the task plan's missing `## Observability Impact` section so the unit now explains which existing inspection surfaces matter and what documentation drift would make the proof misleading.

I then authored `docs/embeddings-integrated-adoption-proof.md` as the embeddings-specific final assembly walkthrough. The new document explicitly preserves the required proof order: public `POST /v1/embeddings` first, `X-Request-ID` plus `X-Nebula-*` headers second, `GET /v1/admin/usage/ledger?request_id=...` third, and Observability only as subordinate corroboration of the same persisted row. It also delegates detailed contract semantics to `docs/embeddings-adoption-contract.md`, delegates the realistic migration diff to `docs/embeddings-reference-migration.md` and `tests/test_embeddings_reference_migration.py`, and names failure modes that would expose scope drift under the slice goal.

Finally, I marked T01 done in the slice plan and captured the verification results, including the local pytest/rootdir mismatch that prevented the slice-level test commands from seeing this worktree's `tests/` files even though they exist under the worktree.

## Verification

I verified the new walkthrough structurally and semantically:

- confirmed the file exists, contains no `TBD` or `TODO`, and has at least six `##` sections
- confirmed the required canonical links and guardrail phrases are present
- confirmed repository-wide discoverability searches now include the new walkthrough alongside the canonical embeddings contract and migration docs

I also ran the slice's focused pytest commands. Those did not validate runtime behavior for this task because pytest resolved `rootdir` to the parent repository (`/Users/joaquinfernandezdegamboa/Proj/nebula`) instead of the worktree, then reported the worktree-local `tests/test_embeddings_reference_migration.py` and `tests/test_embeddings_api.py` paths as missing. The docs introduced in this task do not change runtime code, so I recorded that environment mismatch explicitly rather than misreporting those checks as product failures.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/embeddings-integrated-adoption-proof.md && ! grep -q "TBD\|TODO" docs/embeddings-integrated-adoption-proof.md && [ "$(rg -c "^## " docs/embeddings-integrated-adoption-proof.md)" -ge 6 ]` | 0 | ✅ pass | ~1s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python - <<'PY' ... Path('docs/embeddings-integrated-adoption-proof.md') ... required needles ... PY` | 0 | ✅ pass | ~1s |
| 3 | `rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md` | 0 | ✅ pass | ~1s |
| 4 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py` | 4 | ❌ fail | 25.8s |
| 5 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` | 4 | ❌ fail | 20.3s |
| 6 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 5 | ❌ fail | 17.5s |

## Diagnostics

Future agents can inspect this task through:

- `docs/embeddings-integrated-adoption-proof.md` for the canonical joined proof order and guardrails
- `tests/test_embeddings_reference_migration.py` for the executable public-response to usage-ledger correlation path
- `console/e2e/observability.spec.ts` for the embeddings Observability corroboration flow
- `GET /v1/admin/usage/ledger?request_id=...` as the durable evidence seam named by the walkthrough

The only failure state observed during execution was tooling-related: pytest selected the parent repo root instead of the worktree and therefore treated worktree-local test paths as missing. The task's documentation content checks all passed.

## Deviations

- I updated `.gsd/milestones/M003/slices/S05/tasks/T01-PLAN.md` to add the missing `## Observability Impact` section before implementation, as explicitly required by the task contract.
- I used the project venv interpreter for the content-verification Python check because bare `python` is not available in this environment.

## Known Issues

- The slice-level pytest commands in this worktree currently resolve `rootdir` to the parent repository and fail to locate worktree-local `tests/...` paths. This appears to be a worktree/environment path-resolution issue rather than a failure caused by the documentation changes in T01.

## Files Created/Modified

- `docs/embeddings-integrated-adoption-proof.md` — new embeddings-specific final assembly walkthrough joining contract, migration proof, ledger correlation, and Observability corroboration
- `.gsd/milestones/M003/slices/S05/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section required by the task pre-flight
- `.gsd/milestones/M003/slices/S05/S05-PLAN.md` — marked T01 complete
