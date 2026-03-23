# S03: Reference migration integration

**Goal:** Deliver one canonical, realistic migration proof that replaces a direct OpenAI-compatible chat-completions call with Nebula through the existing public `POST /v1/chat/completions` contract, then corroborates the same request through operator-visible evidence.
**Demo:** A developer can follow a single reference migration artifact, run the proof path, and see that a standard chat-completions caller reaches Nebula with only base URL + header changes while producing both `X-Nebula-*` public response evidence and correlated usage-ledger/operator evidence.

## Must-Haves

- A canonical reference migration artifact shows a believable before/after integration path that uses Nebula's real public contract instead of a demo-only façade.
- The migrated example keeps the code diff intentionally small and honest: base URL, `X-Nebula-API-Key`, and optional `X-Nebula-Tenant-ID` are the primary caller changes.
- Executable verification proves the reference path hits `POST /v1/chat/completions`, returns OpenAI-like output, exposes `X-Nebula-*` headers, and can be correlated in `GET /v1/admin/usage/ledger`.
- Repo entry docs link to the migration proof without reopening the S01 contract or duplicating the S02 quickstart/production-model canonicals.
- The finished artifact is realistic enough that engineers can trust it as a day-1 migration example rather than dismissing it as a toy curl snippet.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `pytest tests/test_reference_migration.py tests/test_chat_completions.py tests/test_response_headers.py tests/test_governance_api.py -q`
- `pytest tests/test_reference_migration.py -k "tenant_header or request_id or ledger" -q`
- `python3 -m py_compile tests/test_reference_migration.py`
- `test -f docs/reference-migration.md && rg -n "reference migration|X-Nebula-API-Key|X-Nebula-Tenant-ID|usage ledger|adoption-api-contract|quickstart|production-model" docs/reference-migration.md README.md`

## Observability / Diagnostics

- Runtime signals: `X-Nebula-*` response headers on the public request plus `X-Request-ID`/usage-ledger terminal-status correlation on the operator side.
- Inspection surfaces: `docs/reference-migration.md`, `tests/test_reference_migration.py`, public `POST /v1/chat/completions`, and `GET /v1/admin/usage/ledger`.
- Failure visibility: verification should make it obvious whether the break is in public auth/header wiring, route metadata emission, or ledger persistence/correlation.
- Redaction constraints: do not hard-code or print real admin/client secrets in docs or tests; use fixture keys and placeholder values only.

## Integration Closure

- Upstream surfaces consumed: `docs/adoption-api-contract.md`, `docs/quickstart.md`, `docs/production-model.md`, `tests/support.py`, `tests/test_chat_completions.py`, `tests/test_governance_api.py`, and the existing public/admin routes.
- New wiring introduced in this slice: one canonical migration doc linked from repo entry docs and one focused integration test module that exercises public-request plus operator-correlation proof together.
- What remains before the milestone is truly usable end-to-end: S04 still needs to turn the proven request flow into explicit day-1 value surfacing, and S05 still needs final integrated adoption closure.

## Tasks

- [x] **T01: Add a focused reference-migration proof harness** `est:1.5h`
  - Why: S03's core risk is weak proof. The slice needs executable evidence that a realistic OpenAI-style caller can switch to Nebula with minimal change and still produce public plus operator evidence.
  - Files: `tests/test_reference_migration.py`, `tests/support.py`, `tests/test_chat_completions.py`, `tests/test_governance_api.py`
  - Do: Add a new focused pytest module that models a direct-provider-style chat-completions caller, then points the same request shape at Nebula's real public endpoint using `X-Nebula-API-Key` and optional `X-Nebula-Tenant-ID`; prove the response stays OpenAI-like while surfacing `X-Nebula-*` headers and a correlatable ledger record. Reuse the existing `configured_app()`, `auth_headers()`, `admin_headers()`, `StubProvider`, and `FakeCacheService` harness patterns instead of inventing a parallel test fixture stack.
  - Verify: `pytest tests/test_reference_migration.py tests/test_chat_completions.py tests/test_governance_api.py -q`
  - Done when: the new test file proves both minimal caller-change semantics and public-to-operator evidence correlation using the real existing routes.
- [x] **T02: Publish and wire the canonical migration guide** `est:1h`
  - Why: The runnable proof needs a single human-facing artifact that adopters and downstream slices can point to without duplicating the quickstart, contract, or production-model docs.
  - Files: `docs/reference-migration.md`, `README.md`, `docs/quickstart.md`, `docs/production-model.md`
  - Do: Write one canonical migration guide that starts from the S02 setup assumptions, shows the smallest honest before/after diff for a realistic chat-completions caller, points readers back to `docs/adoption-api-contract.md` for the contract, and explains how to verify success through `X-Nebula-*` headers and `GET /v1/admin/usage/ledger`. Update repo entry/docs links so the new guide is discoverable without cloning contract or operating-model content into multiple places.
  - Verify: `test -f docs/reference-migration.md && rg -n "reference migration|before|after|X-Nebula-API-Key|usage ledger|adoption-api-contract|quickstart|production-model" docs/reference-migration.md README.md docs/quickstart.md`
  - Done when: the repo has one discoverable, canonical migration document that matches the tested proof path and fits the S01/S02 composition rules.

## Files Likely Touched

- `tests/test_reference_migration.py`
- `tests/support.py`
- `docs/reference-migration.md`
- `README.md`
- `docs/quickstart.md`
- `docs/production-model.md`
