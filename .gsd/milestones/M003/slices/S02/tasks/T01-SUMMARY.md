---
id: T01
parent: S02
milestone: M003
provides:
  - Canonical public embeddings contract documentation for POST /v1/embeddings grounded in runtime and test truth
key_files:
  - docs/embeddings-adoption-contract.md
  - .gsd/milestones/M003/slices/S02/S02-PLAN.md
  - .gsd/milestones/M003/slices/S02/tasks/T01-PLAN.md
key_decisions:
  - Documented only the currently tested embeddings surface, including direct ollama evidence and metadata-only ledger correlation, instead of implying broader OpenAI parity
patterns_established:
  - Treat docs/adoption-api-contract.md as the tone/template, but derive every embeddings claim from route code and focused tests rather than by analogy to chat completions
observability_surfaces:
  - POST /v1/embeddings response headers, X-Request-ID correlation, and GET /v1/admin/usage/ledger metadata-only lookup
duration: 27m
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T01: Author the canonical embeddings contract document

**Published the canonical POST /v1/embeddings contract doc with test-backed request, evidence, failure, and exclusion boundaries.**

## What Happened

I first read the slice plan, task plan, the chat adoption contract doc used as the structural reference, and the embeddings runtime/tests that the task plan named as the only allowed truth sources. Before writing the contract, I fixed the pre-flight plan gaps by adding an `## Observability / Diagnostics` section to `S02-PLAN.md`, adding a failure-surface verification grep there, and adding an `## Observability Impact` section to `T01-PLAN.md` so later agents can inspect the embeddings evidence boundary intentionally instead of rediscovering it from code.

I then authored `docs/embeddings-adoption-contract.md` as the single detailed embeddings contract file. The document stays narrow and test-backed: it covers only `POST /v1/embeddings`, `X-Nebula-API-Key` auth, string or flat-list string input, float-vector response items, zeroed usage fields, the emitted `X-Nebula-*`/`X-Request-ID` evidence, metadata-only correlation through `/v1/admin/usage/ledger`, the mapped failure classes, and explicit unsupported/deferred claims such as nested inputs, extra request options, alternate encodings, and broader parity promises.

I did not edit `README.md` or `docs/architecture.md` in this task because the slice plan assigns that discoverability work to T02. The slice-level grep that expects those links therefore still fails at this stage, and I recorded that honestly in verification instead of folding T02 into T01.

## Verification

I ran the focused embeddings tests and document checks required by the task and slice. All runtime-truth checks for the embeddings route and service behavior passed. The canonical doc existence/content checks passed, and the observability failure-surface grep passed. The slice-level discoverability grep against `README.md` and `docs/architecture.md` failed as expected because those files are scheduled for T02.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` | 0 | ✅ pass | 1.03s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 0 | ✅ pass | 0.83s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding` | 0 | ✅ pass | 0.82s |
| 4 | `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" docs/embeddings-adoption-contract.md && [ "$(rg -c "^## " docs/embeddings-adoption-contract.md)" -ge 6 ]` | 0 | ✅ pass | <1s |
| 5 | `rg -n "X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|unsupported|deferred" docs/embeddings-adoption-contract.md` | 0 | ✅ pass | <1s |
| 6 | `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md` | 1 | ❌ fail | <1s |
| 7 | `rg -n "embeddings_validation_error|embeddings_upstream_error|embeddings_empty_result|X-Request-ID|/v1/admin/usage/ledger" src/nebula/api/routes/embeddings.py tests/test_embeddings_api.py tests/test_governance_api.py tests/test_service_flows.py docs/embeddings-adoption-contract.md` | 0 | ✅ pass | <1s |

## Diagnostics

Inspect the shipped contract in `docs/embeddings-adoption-contract.md`. Runtime evidence for the documented behavior is available on real embeddings responses through `X-Request-ID`, `X-Nebula-Tenant-ID`, `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Provider`, `X-Nebula-Cache-Hit`, `X-Nebula-Fallback-Used`, `X-Nebula-Policy-Mode`, and `X-Nebula-Policy-Outcome`. Durable operator-side inspection remains `GET /v1/admin/usage/ledger?request_id=<X-Request-ID>`, where the tested boundary is metadata-only and excludes raw embedding inputs/vectors.

## Deviations

None. I only applied the required pre-flight plan fixes and left README/architecture discoverability work for T02 as the slice plan specifies.

## Known Issues

- Slice-level discoverability is not complete yet because `README.md` and `docs/architecture.md` do not reference `docs/embeddings-adoption-contract.md` until T02 runs.

## Files Created/Modified

- `docs/embeddings-adoption-contract.md` — added the canonical embeddings adoption contract doc grounded in route code and focused tests.
- `.gsd/milestones/M003/slices/S02/S02-PLAN.md` — added the missing observability/diagnostics section, failure-surface verification check, and marked T01 done.
- `.gsd/milestones/M003/slices/S02/tasks/T01-PLAN.md` — added the missing observability impact section required by the execution contract.
- `.gsd/milestones/M003/slices/S02/tasks/T01-SUMMARY.md` — recorded implementation narrative and verification evidence for task completion.
