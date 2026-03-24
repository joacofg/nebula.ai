---
id: T01
parent: S01
milestone: M001
provides:
  - Executable contract coverage for Nebula's public chat-completions adoption boundary and the admin Playground non-equivalence boundary.
key_files:
  - tests/test_chat_completions.py
  - tests/test_response_headers.py
  - tests/test_admin_playground_api.py
  - src/nebula/models/openai.py
  - .gsd/milestones/M001/slices/S01/S01-PLAN.md
key_decisions:
  - Enforced the "at least one user message" invariant in ChatCompletionRequest schema and documented FastAPI's structured 422 validation shape in tests instead of flattening it into a custom error payload.
patterns_established:
  - Contract tests should assert actual runtime fixtures and policy defaults, including bootstrap-key tenant inference, header visibility on routed failures, and admin-only Playground behavior.
observability_surfaces:
  - tests/test_chat_completions.py, tests/test_response_headers.py, tests/test_admin_playground_api.py, and X-Nebula-* / X-Request-ID response headers.
duration: 1h
verification_result: passed
completed_at: 2026-03-23T19:08:00-03:00
blocker_discovered: false
---

# T01: Harden contract tests around the public adoption boundary

**Added contract-focused chat/admin boundary tests and schema validation for the required user-message rule.**

## What Happened

I first fixed the slice pre-flight gap by adding a task-level failure-path pytest check to `.gsd/milestones/M001/slices/S01/S01-PLAN.md` so the slice verification explicitly covers observable contract regressions.

Then I read the live request schema, public chat route, auth service, admin route, and the existing tests before changing anything. That showed the public path already enforced most of the contract, but the tests did not yet pin down three important boundaries clearly enough: Nebula-header auth instead of bearer auth, the required presence of a `user` message, and the fact that admin Playground is a separate admin-only non-streaming contract.

I extended `tests/test_chat_completions.py` to prove the public endpoint rejects OpenAI-style `Authorization` auth, allows the bootstrap key to infer its default tenant without an explicit tenant header, preserves SSE framing plus response metadata headers, and returns a structured 422 validation error when no `user` message is present.

I extended `tests/test_response_headers.py` to cover success, cache, fallback, policy denial, and validation/error-path header visibility using the repository's real defaults rather than assumed model aliases. In particular, the tests now explicitly prove that route/policy headers remain inspectable on routed failures, while request-validation failures happen before route metadata exists and therefore do not emit `X-Nebula-*` routing headers.

I extended `tests/test_admin_playground_api.py` so it explicitly proves `/v1/admin/playground/completions` is admin-only, rejects `stream=true`, emits `X-Request-ID`, and remains distinct from the public contract even though it reuses the same underlying chat service.

Finally, I made one minimal runtime change in `src/nebula/models/openai.py`: the required-user-message invariant now lives in `ChatCompletionRequest` schema validation. This keeps the contract narrow at the request boundary instead of relying only on downstream service logic.

## Verification

I ran the task verification commands against the focused contract suites. The final passing runs prove the public contract surface, failure-path metadata expectations, and admin Playground boundary currently match the tightened tests.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q` | 0 | ✅ pass | 1.12s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_chat_completions.py -k "stream or user or auth" -q` | 0 | ✅ pass | 0.58s |

## Diagnostics

Future agents can inspect contract drift by rerunning the two pytest commands above. Failures now localize cleanly to one of four dimensions: public auth/header semantics, required request shape, streaming/header behavior, or admin Playground divergence. For runtime observability, the relevant surfaces remain `X-Nebula-*` headers on routed public responses/errors, `X-Request-ID` on admin requests, and `/v1/admin/usage/ledger` for Playground request correlation.

## Deviations

I did not add runtime changes in `src/nebula/api/routes/chat.py` or `src/nebula/services/auth_service.py` because the existing behavior already satisfied the contract once the tests were aligned to the repository's real bootstrap fixture and premium-model defaults. I also corrected several initial test assumptions after verification showed the live contract differed from the planner snapshot: the bootstrap key is single-tenant by default, FastAPI emits structured 422 validation payloads, and default premium allowlists use `gpt-4o-mini` rather than the `openai/` alias.

## Known Issues

None for this task.

## Files Created/Modified

- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — added the missing slice verification step for task-level failure-path/contract diagnostics.
- `src/nebula/models/openai.py` — added schema-level validation requiring at least one `user` message in chat-completion requests.
- `tests/test_chat_completions.py` — added contract assertions for auth semantics, bootstrap tenant inference, SSE headers, and structured 422 validation behavior.
- `tests/test_response_headers.py` — expanded header coverage for routed success/failure paths and validation-path non-emission of route headers.
- `tests/test_admin_playground_api.py` — added explicit admin-only and non-streaming boundary coverage for the Playground API.
