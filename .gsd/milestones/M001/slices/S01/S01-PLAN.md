# S01: Adoption API contract and compatibility boundary

**Goal:** Make Nebula's current `POST /v1/chat/completions` adoption surface explicit, narrowly bounded, and test-backed so downstream quickstart and migration work can target a stable contract instead of inferred behavior.
**Demo:** A developer can inspect one canonical compatibility document, see supported vs unsupported chat-completions behavior grounded in the live gateway code/tests, and run contract-focused tests that prove the public path, header evidence, auth expectations, and admin-playground boundary all match the written story.

## Must-Haves

- Public adoption guidance names the supported request/response contract for common chat-completions usage on `POST /v1/chat/completions`, including auth headers, model naming guidance, streaming behavior, and Nebula response headers.
- Unsupported or deferred features are called out explicitly so Nebula does not imply broad OpenAI parity beyond the current milestone boundary.
- Contract verification covers success, streaming, failure/header evidence, and the admin Playground non-equivalence boundary so docs stay honest to runtime behavior.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q`
- `pytest tests/test_chat_completions.py -k "stream or user or auth" -q`
- `pytest tests/test_response_headers.py -k "denied or fallback_blocked or validation_failures" -q`
- `test -f docs/adoption-api-contract.md && grep -c "^## " docs/adoption-api-contract.md | awk '{exit !($1 >= 6)}' && ! rg -n "TBD|TODO" docs/adoption-api-contract.md`
- `rg -n "adoption-api-contract|POST /v1/chat/completions|X-Nebula-API-Key|unsupported|deferred" README.md docs/architecture.md docs/adoption-api-contract.md`

## Observability / Diagnostics

- Runtime signals: `X-Nebula-*` response headers on success and failure paths, plus Playground `X-Request-ID` and usage-ledger evidence on the admin side.
- Inspection surfaces: `tests/test_response_headers.py`, `tests/test_chat_completions.py`, `tests/test_admin_playground_api.py`, `docs/adoption-api-contract.md`, and `GET /v1/admin/usage/ledger` for Playground proof language.
- Failure visibility: route target/reason, provider, cache hit, fallback used, policy outcome, request id, and explicit HTTP error details remain inspectable when contract behavior regresses.
- Redaction constraints: docs and tests must describe header names and behavior without exposing raw secrets, tenant credentials, prompts beyond fixture text, or provider keys.

## Integration Closure

- Upstream surfaces consumed: `src/nebula/models/openai.py`, `src/nebula/api/routes/chat.py`, `src/nebula/api/routes/admin.py`, `src/nebula/services/auth_service.py`, `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_admin_playground_api.py`, `README.md`, `docs/architecture.md`.
- New wiring introduced in this slice: a canonical adoption-contract doc linked from repo entry docs and backed by focused contract/boundary tests.
- What remains before the milestone is truly usable end-to-end: S02 must turn this boundary into a fast quickstart and production model; S03 must prove a realistic migration against this contract; S04-S05 must connect operator-visible value and final adoption proof.

## Tasks

- [x] **T01: Harden contract tests around the public adoption boundary** `est:1h`
  - Why: Downstream slices need the live contract pinned down in executable tests before docs can safely promise anything.
  - Files: `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_admin_playground_api.py`, `src/nebula/models/openai.py`, `src/nebula/api/routes/chat.py`, `src/nebula/services/auth_service.py`
  - Do: Add or tighten focused tests for the public `POST /v1/chat/completions` contract, especially auth-header expectations, required user-message boundary, streaming/header semantics, and the fact that admin Playground is a different non-streaming contract; make only minimal implementation changes needed to keep tests and runtime behavior aligned with the intended narrow boundary.
  - Verify: `pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q`
  - Done when: the contract-focused tests pass and clearly prove what public adoption supports, what failure/header evidence remains visible, and that Playground is not the same contract.
- [x] **T02: Publish the canonical adoption contract and align entry docs** `est:1h`
  - Why: R001, R002, and R010 are only satisfied if the supported surface and explicit omissions are easy to find without reverse-engineering code.
  - Files: `docs/adoption-api-contract.md`, `README.md`, `docs/architecture.md`
  - Do: Write one canonical contract doc for the public chat-completions adoption path, covering supported request/response shape, auth headers, model naming/routing guidance, streaming, Nebula response headers, and an explicit unsupported/deferred list; then link and align `README.md` and `docs/architecture.md` to that canonical source without duplicating drifting detail.
  - Verify: `test -f docs/adoption-api-contract.md && grep -c "^## " docs/adoption-api-contract.md | awk '{exit !($1 >= 6)}' && ! rg -n "TBD|TODO" docs/adoption-api-contract.md && rg -n "adoption-api-contract" README.md docs/architecture.md`
  - Done when: the repository has a single discoverable compatibility boundary doc, entry docs point to it, and the written contract matches the tested public behavior without implying unsupported parity.

## Files Likely Touched

- `tests/test_chat_completions.py`
- `tests/test_response_headers.py`
- `tests/test_admin_playground_api.py`
- `src/nebula/models/openai.py`
- `src/nebula/api/routes/chat.py`
- `src/nebula/services/auth_service.py`
- `docs/adoption-api-contract.md`
- `README.md`
- `docs/architecture.md`
