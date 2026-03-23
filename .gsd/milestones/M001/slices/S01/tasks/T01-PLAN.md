---
estimated_steps: 4
estimated_files: 6
skills_used:
  - test
  - debug-like-expert
---

# T01: Harden contract tests around the public adoption boundary

**Slice:** S01 — Adoption API contract and compatibility boundary
**Milestone:** M001

## Description

Lock the slice to the live public contract before any documentation work. This task should make the public `POST /v1/chat/completions` boundary executable and unambiguous by tightening tests around supported request/response behavior, auth expectations, error/header visibility, and the explicit non-equivalence of the admin Playground path.

## Steps

1. Review the existing public contract in `src/nebula/models/openai.py`, `src/nebula/api/routes/chat.py`, `src/nebula/services/auth_service.py`, and `src/nebula/api/routes/admin.py`, then identify any under-specified behaviors the roadmap/research says S01 must make explicit.
2. Extend `tests/test_chat_completions.py` and `tests/test_response_headers.py` with focused assertions for the public adoption boundary: required Nebula auth headers, the requirement that at least one `user` message exists, SSE streaming/header behavior, and failure-path metadata visibility.
3. Extend `tests/test_admin_playground_api.py` so it explicitly proves the admin Playground contract differs from the public adoption path, including the non-streaming rejection behavior and any relevant admin-only assumptions.
4. Make only the minimal runtime/schema changes in `src/nebula/models/openai.py`, `src/nebula/api/routes/chat.py`, or `src/nebula/services/auth_service.py` needed to keep the tested behavior internally consistent and narrow rather than expanding compatibility.

## Must-Haves

- [ ] Tests prove the public adoption path uses `X-Nebula-API-Key` / `X-Nebula-Tenant-ID` semantics rather than OpenAI `Authorization` semantics.
- [ ] Tests prove the request must contain at least one `user` message and document the actual failure behavior.
- [ ] Tests continue to prove SSE chunking plus `X-Nebula-*` headers on the public path.
- [ ] Tests explicitly prove `/v1/admin/playground/completions` is admin-only and rejects `stream=true`.

## Verification

- `pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q`
- `pytest tests/test_chat_completions.py -k "stream or user or auth" -q`

## Observability Impact

- Signals added/changed: stronger executable coverage for `X-Nebula-*` headers, HTTP error details, and Playground `X-Request-ID`/ledger-adjacent boundary expectations.
- How a future agent inspects this: run `pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q` and inspect failing assertions for the exact contract dimension that drifted.
- Failure state exposed: missing/changed auth behavior, missing metadata headers, changed streaming framing, or accidental Playground/public-contract conflation become immediately visible in test failures.

## Inputs

- `src/nebula/models/openai.py` — request/response schema that defines the supported public shape
- `src/nebula/api/routes/chat.py` — public `/v1/chat/completions` entrypoint and header mapping
- `src/nebula/services/auth_service.py` — public auth-header and tenant-resolution contract
- `src/nebula/api/routes/admin.py` — admin Playground behavior and streaming rejection boundary
- `tests/test_chat_completions.py` — existing public-path happy-path and streaming proof
- `tests/test_response_headers.py` — existing metadata/failure-path coverage
- `tests/test_admin_playground_api.py` — existing admin Playground proof

## Expected Output

- `tests/test_chat_completions.py` — expanded assertions for public auth, request-shape, and streaming boundary behavior
- `tests/test_response_headers.py` — expanded assertions for failure-path metadata visibility and contract evidence
- `tests/test_admin_playground_api.py` — explicit proof that Playground is a separate non-streaming admin contract
- `src/nebula/models/openai.py` — minimal schema adjustments only if needed to match the intended narrow contract
- `src/nebula/api/routes/chat.py` — minimal contract-alignment updates only if tests expose drift
- `src/nebula/services/auth_service.py` — minimal auth/tenant-boundary updates only if tests expose drift
