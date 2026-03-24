---
estimated_steps: 4
estimated_files: 5
skills_used:
  - test
---

# T02: Extend executable public-to-operator integration proof

**Slice:** S05 — Final integrated adoption proof
**Milestone:** M001

## Description

Strengthen the backend/integration verification so the final assembled adoption story is proved in code, not just in docs. The test seam should stay narrow, reuse the existing runtime harness, and assert that the public request path remains the authoritative starting point for the operator-visible story.

## Steps

1. Inspect `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, and `tests/test_governance_api.py` for the strongest existing seams around public headers, `X-Request-ID`, ledger correlation, Playground corroboration, and policy/runtime truth.
2. Add or refine focused assertions so one integrated backend proof preserves the exact order public response evidence first, ledger correlation second, operator corroboration third, without promoting Playground into the adoption boundary.
3. Reuse existing fixtures and helper utilities from the test suite rather than introducing new standalone harnesses or duplicated setup.
4. Run the planned pytest suite, and if the local worktree lacks `pytest`, record that as an environment gap in downstream bookkeeping rather than weakening the proof contract.

## Must-Haves

- [ ] The integrated pytest seam still starts from `POST /v1/chat/completions` and asserts `X-Nebula-*` plus `X-Request-ID` evidence.
- [ ] The tests prove usage-ledger correlation remains the binding mechanism between public response truth and operator evidence.
- [ ] Any Playground-related assertions keep it explicitly admin-only and corroborative.

## Verification

- `python3 -m pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_chat_completions.py tests/test_response_headers.py -q`
- `python3 -m pytest tests/test_reference_migration.py -k "tenant_header or request_id or ledger" -q`

## Observability Impact

- Signals added/changed: tighter assertions around `X-Nebula-*` headers, `X-Request-ID`, ledger fields, and any corroboration ordering encoded in tests
- How a future agent inspects this: run `python3 -m pytest` on the named files and inspect which assertion fails for public headers, ledger correlation, or admin-surface boundaries
- Failure state exposed: contract drift between public response evidence, persisted ledger evidence, and operator corroboration becomes explicit in failing tests

## Inputs

- `tests/test_reference_migration.py` — current migration proof and public-to-ledger correlation baseline
- `tests/test_admin_playground_api.py` — Playground admin-only boundary and ledger-correlation coverage
- `tests/test_governance_api.py` — runtime-truth assertions for ledger outcomes and policy behavior
- `tests/test_chat_completions.py` — public route contract regressions relevant to final assembly
- `tests/test_response_headers.py` — response-header contract coverage for the adoption path

## Expected Output

- `tests/test_reference_migration.py` — integrated proof assertions refined or expanded
- `tests/test_admin_playground_api.py` — corroboration-boundary assertions kept aligned with final proof
- `tests/test_governance_api.py` — runtime-truth coverage aligned where needed for final assembly
- `tests/test_chat_completions.py` — supporting public-path assertions updated if required
- `tests/test_response_headers.py` — supporting header assertions updated if required
