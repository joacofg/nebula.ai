---
id: T02
parent: S02
milestone: M009
key_files:
  - tests/test_chat_completions.py
  - tests/test_response_headers.py
  - tests/test_governance_api.py
key_decisions:
  - Kept end-to-end verification request-first by asserting parity between live response headers, `policy_outcome`, and persisted `route_signals` on the correlated usage-ledger row rather than introducing new helper abstractions.
  - Updated existing governance expectations to treat outcome-evidence as an additive observability contract, so unchanged routes can still be surfaced when only explanatory policy-outcome metadata changes.
duration: 
verification_result: mixed
completed_at: 2026-04-27T16:02:22.228Z
blocker_discovered: false
---

# T02: Added end-to-end backend tests that prove outcome-grounded live routing persists matching request headers and ledger route_signals across success, denial, and replay seams.

**Added end-to-end backend tests that prove outcome-grounded live routing persists matching request headers and ledger route_signals across success, denial, and replay seams.**

## What Happened

Extended the backend request-path tests to prove tenant-scoped outcome evidence can materially change a live `/v1/chat/completions` route and that the same request persists matching route factors on the usage ledger row. In `tests/test_chat_completions.py`, I seeded tenant evidence through real requests, then verified a short auto-routed prompt flipped to premium once the evidence summary became sufficient, with header values, `policy_outcome`, and persisted `route_signals.score_components`/`outcome_evidence` matching exactly. I also added a policy-denial proof showing an explicit premium request still carries the outcome-evidence state through `policy_outcome` while persisting an honest `policy_denied` ledger row with no route_signals. In `tests/test_response_headers.py`, I added a focused header-to-ledger parity assertion for the same outcome-grounded request. In `tests/test_governance_api.py`, I repaired a malformed embedded scenario by splitting it into a standalone usage-ledger correlation test, then updated older governance expectations so they match T01’s additive observability contract: `policy_outcome` now includes outcome-evidence summaries on existing happy paths, calibrated-routing disablement remains inspectable alongside that evidence state, and policy simulation may return unchanged routes when only the explanatory outcome contract changes.

## Verification

Ran the task-plan verification suites after the final edits. `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or route"` passed 3 selected tests and proved live outcome-evidence routing plus ledger persistence. The task-plan header command `./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals"` selected zero tests under pytest’s case-sensitive `-k` matching (exit 5), so I ran the lowercase-equivalent `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"`, which passed and verified request-header to ledger parity for outcome-grounded routing. `./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or outcome_grounded or policy_simulation"` passed 11 selected tests and confirmed the request-first inspection seam across usage-ledger reads, degraded/gated routes, and policy simulation replay. The governance suite emitted one pre-existing FastAPI deprecation warning for `HTTP_422_UNPROCESSABLE_ENTITY`; no task-scope failures remained.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or route"` | 0 | ✅ pass | 990ms |
| 2 | `./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals"` | 5 | ❌ fail | 690ms |
| 3 | `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"` | 0 | ✅ pass | 820ms |
| 4 | `./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or outcome_grounded or policy_simulation"` | 0 | ✅ pass | 1640ms |

## Deviations

Adjusted `tests/test_governance_api.py` beyond the originally listed request-path proofs because an existing malformed embedded scenario and several stale `policy_outcome` expectations no longer matched T01’s additive outcome-evidence contract. Also documented the plan-command mismatch for the response-header pytest selector and verified the intended scope with a lowercase-equivalent selector instead of silently claiming the original command passed.

## Known Issues

The task-plan command `./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals"` currently deselects every test because pytest `-k` matching is case-sensitive and the suite uses lowercase names. Verification used the lowercase-equivalent selector so the intended scope still ran. The governance verification suite also continues to emit a pre-existing FastAPI deprecation warning about `HTTP_422_UNPROCESSABLE_ENTITY`.

## Files Created/Modified

- `tests/test_chat_completions.py`
- `tests/test_response_headers.py`
- `tests/test_governance_api.py`
