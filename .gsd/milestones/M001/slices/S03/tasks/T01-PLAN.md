---
estimated_steps: 5
estimated_files: 4
skills_used:
  - test
---

# T01: Add a focused reference-migration proof harness

**Slice:** S03 — Reference migration integration
**Milestone:** M001

## Description

Build the executable heart of S03: a focused pytest module that proves a realistic OpenAI-style chat-completions caller can switch to Nebula's existing public `POST /v1/chat/completions` route with minimal caller changes and still produce both immediate public-path metadata and operator-correlatable ledger evidence. Reuse the existing backend test harness instead of adding new runtime infrastructure.

## Steps

1. Read the existing harness patterns in `tests/support.py`, `tests/test_chat_completions.py`, and `tests/test_governance_api.py` and define the specific migration-proof scenarios the new file must cover.
2. Create `tests/test_reference_migration.py` with focused tests that model the minimal migration delta honestly: unchanged chat-completions body shape, Nebula public path, `X-Nebula-API-Key`, and `X-Nebula-Tenant-ID` only when the scenario truly needs multi-tenant disambiguation.
3. Add assertions that the migrated call returns an OpenAI-like completion payload plus meaningful `X-Nebula-*` headers for tenant, route target, provider, cache/fallback, and policy outcome.
4. Add correlation assertions that use `X-Request-ID` and `GET /v1/admin/usage/ledger` to prove the same request persists operator-visible evidence with expected route/terminal-status data.
5. Keep the test file narrow and slice-specific: no new gateway features, no duplicate coverage of the full contract suite, and no demo-only fake route.

## Must-Haves

- [ ] `tests/test_reference_migration.py` proves a believable migration path against the real public route rather than a fixture-only façade.
- [ ] The new tests explicitly verify both public response evidence and usage-ledger correlation for the same request flow.
- [ ] The scenarios stay honest about auth/header changes: they must use `X-Nebula-API-Key` and only require `X-Nebula-Tenant-ID` when tenant inference is intentionally ambiguous.

## Verification

- `pytest tests/test_reference_migration.py tests/test_chat_completions.py tests/test_governance_api.py -q`
- `python3 -m py_compile tests/test_reference_migration.py`

## Observability Impact

- Signals added/changed: stronger slice-specific test evidence around `X-Nebula-*` headers, `X-Request-ID`, ledger `terminal_status`, and final route correlation.
- How a future agent inspects this: run `pytest tests/test_reference_migration.py -q` and compare assertions against `tests/support.py`, `tests/test_chat_completions.py`, and `tests/test_governance_api.py`.
- Failure state exposed: broken auth/header wiring, missing route metadata, or missing/incorrect usage-ledger persistence becomes explicit at test time.

## Inputs

- `tests/support.py` — existing test harness helpers and stub providers to reuse
- `tests/test_chat_completions.py` — current public-contract happy-path and streaming assertion patterns
- `tests/test_governance_api.py` — existing usage-ledger and request-correlation assertion patterns
- `docs/adoption-api-contract.md` — canonical public boundary the migration proof must respect
- `docs/production-model.md` — tenant/API-key/operator rules that constrain realistic scenarios

## Expected Output

- `tests/test_reference_migration.py` — focused migration-proof tests covering minimal caller changes plus public/ledger evidence correlation
