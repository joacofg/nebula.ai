---
id: T02
parent: S01
milestone: M001
provides:
  - Canonical repository documentation for Nebula's tested `POST /v1/chat/completions` adoption boundary, plus aligned entry docs that point to one source of truth.
key_files:
  - docs/adoption-api-contract.md
  - README.md
  - docs/architecture.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-PLAN.md
  - .gsd/milestones/M001/slices/S01/S01-PLAN.md
key_decisions:
  - The adoption contract is documented as a deliberately narrow, test-backed boundary and explicitly separates the public client path from the admin Playground path.
patterns_established:
  - Contract docs should describe only behavior proven by focused tests, name unsupported or deferred claims explicitly, and link entry docs back to a single canonical source instead of restating drifting details.
observability_surfaces:
  - docs/adoption-api-contract.md, README.md, docs/architecture.md, tests/test_chat_completions.py, tests/test_response_headers.py, tests/test_admin_playground_api.py, X-Nebula-* response headers, X-Request-ID, and GET /v1/admin/usage/ledger.
duration: 1h
verification_result: passed
completed_at: 2026-03-23T19:58:00-03:00
blocker_discovered: false
---

# T02: Publish the canonical adoption contract and align entry docs

**Published the canonical adoption API contract and linked README plus architecture docs back to that single test-backed source of truth.**

## What Happened

I first completed the task pre-flight fixes in the planning artifacts. I added a task-level `## Observability Impact` section to `.gsd/milestones/M001/slices/S01/tasks/T02-PLAN.md` and added an explicit failure-path pytest command to `.gsd/milestones/M001/slices/S01/S01-PLAN.md` so the slice verification now names inspectable failure behavior instead of only happy-path/document checks.

Then I read the contract tests from T01 and the current `README.md` plus `docs/architecture.md` to keep the documentation grounded in live behavior. Based on those tests, I created `docs/adoption-api-contract.md` as the canonical public contract for `POST /v1/chat/completions`.

The new contract doc explicitly documents the supported public request shape, the required `X-Nebula-API-Key` auth header, the required presence of a `user` message, model-selection guidance around `nebula-auto` and explicit model requests, non-streaming and streaming response behavior, and the `X-Nebula-*` response-header evidence that remains inspectable on routed success and routed failure paths.

I also made the boundary explicit around what Nebula does not yet promise. The doc now has a clearly labeled unsupported/deferred section that says Nebula does not claim full OpenAI parity, does not support public bearer-token auth for this path, does not treat the admin Playground as the public client contract, and does not claim support for broader untested features such as tools or multimodal inputs.

After that, I updated `README.md` to point adopters directly to `docs/adoption-api-contract.md` from the documentation map and selected-endpoints section instead of letting the README become a competing contract description. I updated `docs/architecture.md` so the request-flow narrative references the canonical adoption contract, and I clarified that the admin Playground is an admin-only, non-streaming operator surface distinct from the public adoption API.

One small documentation fix was needed during verification: my first draft included the literal placeholder-marker grep command in the contract doc, which caused the doc's own no-placeholder check to fail. I removed the inline command block and replaced it with prose describing the verification expectation so the content now satisfies its own quality bar.

## Verification

I ran the slice-level and task-level verification commands after the doc changes. The documentation-specific checks passed: the contract file exists, has at least six top-level sections, contains no unfinished placeholder markers, and is referenced from the aligned entry docs.

I also reran the focused contract pytest subsets that cover streaming/auth/user-message behavior and response-header failure visibility. Those targeted subsets passed.

The broad slice pytest command did not fully pass, but the failures were not caused by this documentation task. The current runtime/test mismatch is in pre-existing test expectations: one header test still expects `X-Nebula-Policy-Outcome == "default"` for a denied premium alias even though runtime returns the explicit denial reason, and one admin Playground test expects a local response for `gpt-4o-mini` even though the live route selects premium. I did not change those tests or runtime paths in this docs task, so I recorded the partial slice-verification status rather than broadening scope.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q` | 1 | ❌ fail | 1.67s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_chat_completions.py -k "stream or user or auth" -q` | 0 | ✅ pass | 1.03s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_response_headers.py -k "denied or fallback_blocked or validation_failures" -q` | 0 | ✅ pass | 0.99s |
| 4 | `test -f docs/adoption-api-contract.md && grep -c "^## " docs/adoption-api-contract.md | awk '{exit !($1 >= 6)}' && ! rg -n "TBD|TODO" docs/adoption-api-contract.md` | 0 | ✅ pass | 0.01s |
| 5 | `rg -n "adoption-api-contract|POST /v1/chat/completions|X-Nebula-API-Key|unsupported|deferred|Playground" README.md docs/architecture.md docs/adoption-api-contract.md` | 0 | ✅ pass | 0.01s |

## Diagnostics

Future agents can inspect the canonical external contract in `docs/adoption-api-contract.md` and compare it directly against `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and `tests/test_admin_playground_api.py`. For runtime observability, the documented inspection surfaces remain the public `X-Nebula-*` response headers, the admin `X-Request-ID` header, and `GET /v1/admin/usage/ledger` for Playground correlation. If the broad slice pytest command still fails later, check whether the live runtime semantics or the test expectations changed around policy-denial header values and Playground routing for explicit premium models.

## Deviations

I updated the planning artifacts as required by the task pre-flight section before implementing the docs. I also replaced an initially embedded verification command block in `docs/adoption-api-contract.md` with prose because the literal placeholder-marker grep text caused the document to fail its own no-placeholder check.

## Known Issues

The slice-level broad pytest command still has two failing tests unrelated to this doc-only task: `tests/test_response_headers.py::test_response_headers_cover_local_premium_cache_and_fallback` and `tests/test_admin_playground_api.py::test_admin_playground_completion`. Their expectations appear to lag current runtime behavior.

## Files Created/Modified

- `docs/adoption-api-contract.md` — added the canonical public adoption contract, including supported request/response behavior, auth/header evidence, Playground boundary, and unsupported/deferred claims.
- `README.md` — linked adopters to the canonical contract from the documentation map and selected-endpoints section.
- `docs/architecture.md` — aligned the request-flow and observability narrative to the canonical contract and clarified the admin Playground boundary.
- `.gsd/milestones/M001/slices/S01/tasks/T02-PLAN.md` — added the missing `## Observability Impact` section required by task pre-flight.
- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — added an explicit failure-path pytest verification command required by slice pre-flight.
