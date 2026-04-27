# S02: S02 — UAT

**Milestone:** M009
**Written:** 2026-04-27T20:57:35.173Z

# S02: S02 — UAT

**Milestone:** M009
**Written:** 2026-04-27

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: this slice changes backend routing semantics and persisted request evidence rather than a human-facing UI flow, so backend integration tests against real request, header, and ledger seams are the authoritative proof.

## Preconditions

- Python virtualenv exists at `./.venv` with test dependencies installed.
- Test database fixtures can create tenants, API keys, and usage-ledger rows.
- The repository contains the S01 outcome-evidence summarization contract used by runtime routing.

## Smoke Test

Run `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or route"` and confirm the selected request can complete successfully while persisting matching route evidence on the usage ledger.

## Test Cases

### 1. Live request upgrades to premium because recent tenant evidence is sufficient

1. Seed tenant-scoped outcome evidence using the existing backend test fixtures so the tenant has recent successful premium-calibration history.
2. Send a short `POST /v1/chat/completions` request that would normally stay on the heuristic local path when no outcome evidence is present.
3. Inspect the response headers and persisted usage-ledger row for the correlated request.
4. **Expected:** the request routes to premium because of the bounded recent evidence, response headers expose the outcome-grounded route mode, `policy_outcome` includes the outcome-evidence state, and the ledger `route_signals` payload records the same `outcome_evidence` summary plus additive score components such as `outcome_bonus` and `evidence_penalty`.

### 2. Request-first parity holds between headers and persisted ledger evidence

1. Run `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"`.
2. Read the selected test’s assertions for response headers and the correlated usage-ledger record.
3. **Expected:** the same request-level routing story appears in both places; headers and persisted `route_signals` agree on route mode and outcome-grounded evidence details rather than drifting into separate explanations.

### 3. Denied or governance-constrained paths stay honest about evidence

1. Seed tenant outcome evidence, then issue a request path that is denied or constrained by policy (for example an explicit premium request that breaches policy).
2. Inspect the resulting ledger row and `policy_outcome` field.
3. **Expected:** the request records a truthful `policy_denied` or constrained outcome, retains the outcome-evidence state in explanatory metadata, and does not fabricate live route factors when the request never actually routed through the normal scored path.

## Edge Cases

### Case-sensitive pytest selector mismatch

1. Run `./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals"`.
2. Observe pytest selection output, then rerun with `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"`.
3. **Expected:** the mixed-case selector deselects all tests because `-k` matching is case-sensitive, while the lowercase-equivalent selector executes the intended parity proof successfully.

## Failure Signals

- Short prompts continue to route locally even after sufficient tenant outcome evidence is seeded.
- Response headers, `policy_outcome`, and persisted `route_signals` disagree about route mode or outcome-evidence state.
- Policy-denied requests persist synthetic route factors instead of an honest denied/minimized record.
- Hard-budget downgrade or deny behavior changes when outcome evidence is introduced.

## Not Proven By This UAT

- Replay parity for the same outcome-grounded semantics in admin policy simulation; that belongs to S03.
- Operator-surface rendering of grounded, thin, stale, or degraded evidence on Observability request detail pages; that belongs to S04.

## Notes for Tester

This UAT intentionally treats backend tests as the user-acceptance surface because the slice’s customer-visible contract is request behavior plus persisted request evidence, not a new UI. One pre-existing FastAPI deprecation warning about `HTTP_422_UNPROCESSABLE_ENTITY` may appear in the governance suite and does not indicate a regression in S02.
