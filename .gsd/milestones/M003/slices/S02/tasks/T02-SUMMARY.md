---
id: T02
parent: S02
milestone: M003
provides:
  - Repo entry docs that point readers to the canonical embeddings adoption contract without creating a second contract source
key_files:
  - README.md
  - docs/architecture.md
  - docs/embeddings-adoption-contract.md
  - .gsd/milestones/M003/slices/S02/tasks/T02-PLAN.md
key_decisions:
  - Kept README and architecture mentions pointer-only and deferred all detailed embeddings semantics back to docs/embeddings-adoption-contract.md
patterns_established:
  - When adding discoverability for a canonical contract doc, update entry docs with narrow links and endpoint references only, not duplicated request or failure detail
observability_surfaces:
  - README.md and docs/architecture.md discoverability grep plus the existing POST /v1/embeddings X-Request-ID/X-Nebula-* and /v1/admin/usage/ledger evidence path
duration: 26m
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T02: Link entry docs back to the canonical embeddings contract

**Linked README and architecture entry points to the canonical embeddings contract without creating a competing source of truth.**

## What Happened

I first read the task plan, the prior T01 summary, the canonical `docs/embeddings-adoption-contract.md`, and the current `README.md` and `docs/architecture.md` sections that control documentation discovery. Before editing user-facing docs, I fixed the pre-flight plan gap by adding an `## Observability Impact` section to `.gsd/milestones/M003/slices/S02/tasks/T02-PLAN.md` so later agents can inspect the doc-linking outcome intentionally instead of inferring it.

I then updated `README.md` in two pointer-only places: the documentation map now includes `docs/embeddings-adoption-contract.md`, and the selected public endpoint inventory now lists `POST /v1/embeddings` with an explicit redirect back to the canonical contract file. I kept both additions concise so the README improves discoverability without restating supported request shape, failure semantics, or evidence details that belong in the canonical doc.

In `docs/architecture.md`, I added a short note under request flow acknowledging that Nebula exposes a narrow public `POST /v1/embeddings` surface while explicitly deferring the exact request/response, evidence, and exclusions to `docs/embeddings-adoption-contract.md`. I also added one observability-level pointer in the operator-proof section so architecture readers who are validating embeddings behavior know where the canonical evidence contract lives.

During verification I hit two local-reality mismatches and corrected them surgically. First, initial async pytest commands resolved against the parent repository root instead of this worktree, which produced false failures for missing or deselected tests; rerunning the same test targets from the worktree path passed. Second, the canonical doc's local verification snippet contained the literal strings `TBD|TODO` inside an example grep command, which caused the slice's own `grep -q "TBD\|TODO"` check to fail even though the document had no real placeholders. I replaced that self-referential example with a TODO-free Python section-count snippet so the gate reflects actual doc quality.

## Verification

I re-read the changed README and architecture sections to confirm they stayed pointer-only. I then ran the task-level and slice-level verification commands from the worktree: the focused embeddings API, governance, and service-flow pytest targets all passed; the discoverability grep confirmed both entry docs now point to the canonical file; the canonical-doc integrity check passed after removing the self-failing TODO/TBD example text; and the observability grep confirmed the documented failure reasons, `X-Request-ID`, and `/v1/admin/usage/ledger` evidence path remain visible in code, tests, and docs.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` | 0 | ✅ pass | 1.49s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 0 | ✅ pass | 1.37s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding` | 0 | ✅ pass | 1.37s |
| 4 | `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" docs/embeddings-adoption-contract.md && [ "$(rg -c "^## " docs/embeddings-adoption-contract.md)" -ge 6 ]` | 0 | ✅ pass | <1s |
| 5 | `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md` | 0 | ✅ pass | <1s |
| 6 | `rg -n "embeddings_validation_error|embeddings_upstream_error|embeddings_empty_result|X-Request-ID|/v1/admin/usage/ledger" src/nebula/api/routes/embeddings.py tests/test_embeddings_api.py tests/test_governance_api.py tests/test_service_flows.py docs/embeddings-adoption-contract.md` | 0 | ✅ pass | <1s |
| 7 | `(initial async run) /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` | 4 | ❌ fail | 7.2s |
| 8 | `(initial async run) /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 5 | ❌ fail | 7.2s |
| 9 | `(initial async run) /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding` | 5 | ❌ fail | 7.2s |

## Diagnostics

For discoverability validation, inspect `README.md` and `docs/architecture.md` with `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md`. For runtime evidence, continue to inspect real `POST /v1/embeddings` responses via `X-Request-ID`, `X-Nebula-Tenant-ID`, `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Provider`, `X-Nebula-Cache-Hit`, `X-Nebula-Fallback-Used`, `X-Nebula-Policy-Mode`, and `X-Nebula-Policy-Outcome`, then correlate durable metadata through `GET /v1/admin/usage/ledger?request_id=<X-Request-ID>`.

## Deviations

I made one unplanned but necessary follow-up edit to `docs/embeddings-adoption-contract.md`: the document's own local verification example included the literal strings `TBD|TODO`, which caused the slice's placeholder grep to fail. I replaced that example with an equivalent TODO-free integrity snippet so the documented verification path no longer invalidates the document.

## Known Issues

- Initial async pytest invocations resolved against `/Users/joaquinfernandezdegamboa/Proj/nebula` instead of this worktree and therefore produced misleading failures. The rerun evidence above reflects the correct worktree-local execution and passed.

## Files Created/Modified

- `README.md` — added the embeddings adoption contract to the documentation map and linked `POST /v1/embeddings` back to the canonical contract from the selected endpoint list.
- `docs/architecture.md` — added pointer-only embeddings surface references in request-flow and observability sections without duplicating contract semantics.
- `docs/embeddings-adoption-contract.md` — removed a self-failing `TBD|TODO` verification example so slice-level doc integrity checks reflect real placeholder state.
- `.gsd/milestones/M003/slices/S02/tasks/T02-PLAN.md` — added the missing observability impact section required by the execution contract.
- `.gsd/milestones/M003/slices/S02/tasks/T02-SUMMARY.md` — recorded implementation narrative, local mismatches, and verification evidence for task completion.
