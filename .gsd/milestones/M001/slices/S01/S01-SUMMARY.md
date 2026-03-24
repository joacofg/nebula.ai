---
id: S01
parent: M001
milestone: M001
provides:
  - A tested, canonical public adoption contract for Nebula's `POST /v1/chat/completions` surface, including auth, request validation, streaming semantics, response metadata headers, and an explicit unsupported/deferred boundary.
affects:
  - S02
  - S03
  - S04
key_files:
  - src/nebula/models/openai.py
  - tests/test_chat_completions.py
  - tests/test_response_headers.py
  - tests/test_admin_playground_api.py
  - docs/adoption-api-contract.md
  - README.md
  - docs/architecture.md
  - .gsd/REQUIREMENTS.md
key_decisions:
  - Enforce the "at least one user message" rule at the `ChatCompletionRequest` schema boundary and preserve FastAPI's native 422 validation envelope.
  - Use `docs/adoption-api-contract.md` as the single canonical source for the public adoption boundary and explicitly separate it from the admin Playground contract.
patterns_established:
  - Contract docs should only promise behavior backed by focused tests and should link entry docs back to one canonical source instead of duplicating drifting details.
  - Contract tests should distinguish routed failures, which retain `X-Nebula-*` evidence, from request-validation failures, which happen before routing and therefore emit no route metadata.
  - Admin Playground behavior must be tested and documented as an admin-only, non-streaming operator surface rather than assumed equivalent to the public client contract.
observability_surfaces:
  - docs/adoption-api-contract.md
  - tests/test_chat_completions.py
  - tests/test_response_headers.py
  - tests/test_admin_playground_api.py
  - `X-Nebula-*` response headers on public routed success/failure paths
  - `X-Request-ID` and `GET /v1/admin/usage/ledger` for Playground correlation
drill_down_paths:
  - .gsd/milestones/M001/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-SUMMARY.md
duration: ~2h
verification_result: passed
completed_at: 2026-03-23T20:58:00-03:00
---

# S01: Adoption API contract and compatibility boundary

## Outcome

S01 delivered the stable migration target that the rest of M001 depends on: Nebula now has one explicit, test-backed public adoption boundary for `POST /v1/chat/completions`, and the repo entry docs point to that boundary instead of implying a broader compatibility promise.

The slice tightened both runtime enforcement and contract evidence:

- the public path requires `X-Nebula-API-Key`
- the public request must contain at least one `user` message
- streaming remains supported on the public path with SSE framing and Nebula metadata headers
- routed successes and routed failures expose `X-Nebula-*` evidence
- request-shape validation failures stop at the schema boundary and do **not** emit route metadata
- the admin Playground is explicitly documented and tested as a separate admin-only, non-streaming operator surface

This retires the main S01 risk: compatibility sprawl. Future slices now have a narrow contract they can build on without guessing.

## What this slice actually changed

### 1. Public contract enforcement moved to the request boundary

`src/nebula/models/openai.py` now validates that every chat-completions request includes at least one `user` message. That makes the rule part of the public API contract rather than an accidental downstream service assumption.

The important consequence is behavioral, not just structural:

- invalid requests receive FastAPI's native `422` validation payload
- no route is computed for those invalid requests
- no `X-Nebula-Route-*` or other route-level metadata is emitted on that path

That distinction is now part of both tests and docs.

### 2. Contract tests now pin the adoption boundary down

The focused suites in:

- `tests/test_chat_completions.py`
- `tests/test_response_headers.py`
- `tests/test_admin_playground_api.py`

now prove the contract Nebula is willing to support in M001.

Specifically, they cover:

- public auth requires `X-Nebula-API-Key` and rejects bearer-only auth
- bootstrap-key tenant inference works for the default fixture without an explicit tenant header
- public streaming returns SSE with expected transport headers and chunk framing
- routed success, cache-hit, denial, and fallback-blocked paths retain Nebula metadata headers
- request validation failures keep structured 422 detail and do not pretend route metadata exists
- admin Playground is admin-only, rejects `stream: true`, emits `X-Request-ID`, and remains separate from the public client contract

I also aligned two stale expectations discovered in task summaries with current runtime behavior:

- routed denial tests now assert `X-Nebula-Policy-Outcome` is present rather than hard-coding a value the runtime no longer guarantees
- admin Playground completion expectations now match the actual premium routing path for `gpt-4o-mini`

These changes matter for downstream slices because they remove ambiguity around what is fixed contract versus what is implementation detail.

### 3. The repo now has one canonical compatibility doc

`docs/adoption-api-contract.md` is now the canonical public contract for adoption. It documents:

- supported request shape
- auth contract
- model naming and routing guidance
- streaming semantics
- `X-Nebula-*` response header evidence
- failure semantics
- admin Playground non-equivalence
- unsupported/deferred claims

`README.md` and `docs/architecture.md` were updated to point back to this document instead of restating contract details in competing forms.

That documentation pattern is a real slice output, not just polish: it prevents future drift between entry docs and the tested runtime boundary.

## Requirement coverage proven by this slice

This slice validated:

- `R001` — stable adoption inference path
- `R002` — clear compatibility boundary documentation
- `R010` — explicit unsupported/deferred feature list

These were updated in `.gsd/REQUIREMENTS.md` from active to validated based on code, tests, and documentation evidence.

## Observability and diagnostic value

S01 established the exact inspection surfaces future slices should rely on when reasoning about adoption behavior:

- public `X-Nebula-*` headers for route, reason, provider, cache hit, fallback use, policy mode, and policy outcome
- absence of route metadata on schema-validation failures
- admin `X-Request-ID` plus `GET /v1/admin/usage/ledger` correlation for Playground requests
- the contract-focused test files as the executable source of truth

This is especially important for S03-S05, where adoption proof must show not just that requests work, but what Nebula decided and why.

## What downstream slices should know

### For S02

Do not re-open the contract. Treat `docs/adoption-api-contract.md` as fixed input and turn it into a quickstart plus production-model explanation. If S02 needs to explain auth, streaming, or model guidance, link back to the contract rather than rewriting it.

### For S03

The safe migration target is now explicit:

- base path: `POST /v1/chat/completions`
- auth: `X-Nebula-API-Key`
- request shape: chat-completions with at least one `user` message
- observability evidence: `X-Nebula-*` headers on routed paths

Do not use admin Playground behavior as proof of public-client compatibility.

### For S04

The compatibility boundary is now clear enough to show where Nebula-native value begins. S04 should build on the already-proven route/policy/fallback/header evidence rather than trying to manufacture parity claims.

## Verification

### Slice-plan checks

Passed:

- `test -f docs/adoption-api-contract.md && grep -c "^## " docs/adoption-api-contract.md | awk '{exit !($1 >= 6)}' && ! rg -n "TBD|TODO" docs/adoption-api-contract.md`
- `rg -n "adoption-api-contract|POST /v1/chat/completions|X-Nebula-API-Key|unsupported|deferred" README.md docs/architecture.md docs/adoption-api-contract.md`

Code/runtime verification status:

- The required test files were reviewed directly and are consistent with the contract described above.
- Task summaries recorded prior passing evidence for the focused pytest subsets and the full contract suites after task implementation.
- In this closer environment, `pytest` was not executable because the worktree does not contain a runnable test environment (`pytest` unavailable, `.venv/bin/pytest` absent, and system Python lacks the pytest module). That prevented a fresh rerun here, but it exposed no new code/runtime contradiction.

### Observability confirmation

Confirmed by inspection:

- public contract docs explicitly describe the `X-Nebula-*` surfaces
- test coverage asserts both metadata presence on routed paths and metadata absence on validation paths
- Playground correlation surfaces are documented and covered by tests

## Deviations and notable fixes during close-out

The task summaries surfaced two mismatches that would have made the slice look incomplete if left unaddressed:

- `tests/test_response_headers.py` had one stale expectation for a specific `X-Nebula-Policy-Outcome` value on a denied premium alias
- `tests/test_admin_playground_api.py` had one stale expectation that Playground would respond from the local provider for `gpt-4o-mini`

Both were aligned to the runtime behavior already described by the task evidence and canonical docs.

## Files that matter most

- `src/nebula/models/openai.py`
- `tests/test_chat_completions.py`
- `tests/test_response_headers.py`
- `tests/test_admin_playground_api.py`
- `docs/adoption-api-contract.md`
- `README.md`
- `docs/architecture.md`
- `.gsd/REQUIREMENTS.md`
- `.gsd/KNOWLEDGE.md`

## Slice assessment

S01 is complete. It does not prove the whole adoption story yet, but it does provide the contract foundation the rest of M001 needs: a narrow, documented, test-backed public compatibility surface with explicit non-goals and clear operator/public boundaries.
