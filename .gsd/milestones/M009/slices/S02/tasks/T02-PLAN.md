---
estimated_steps: 1
estimated_files: 4
skills_used: []
---

# T02: Prove request-to-ledger persistence for outcome-grounded live routing

Close the slice on the real request path by proving a live `/v1/chat/completions` call can route differently because of seeded tenant evidence and that the correlated usage-ledger row records the actual outcome-grounded route factors used. Cover both happy-path persistence and honest degraded/minimized behavior so downstream replay and operator slices can trust the stored seam. Record installed skills in frontmatter as `verify-before-complete` and `test` because this task must finish with executable evidence from tracked backend tests.

## Inputs

- ``src/nebula/services/router_service.py``
- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/chat_service.py``
- ``src/nebula/services/governance_store.py``
- ``tests/test_chat_completions.py``
- ``tests/test_response_headers.py``
- ``tests/test_governance_api.py``
- ``tests/support.py``

## Expected Output

- ``tests/test_chat_completions.py``
- ``tests/test_response_headers.py``
- ``tests/test_governance_api.py``
- ``tests/support.py``

## Verification

./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or route" && ./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals" && ./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or outcome_grounded or policy_simulation"

## Observability Impact

Locks the request-first inspection seam by asserting the same request ID links response metadata, optional route-mode header exposure, governance suppression markers, and persisted `route_signals` truth on the ledger row.
