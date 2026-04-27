---
estimated_steps: 1
estimated_files: 3
skills_used: []
---

# T02: Lock the happy-path and degraded backend proof chain

Tighten the backend proof seams so one happy-path scenario and one degraded-path scenario each explicitly support the final integrated walkthrough. Reuse the existing request, header, ledger, and simulation tests rather than adding a new orchestration API or synthetic proof harness. Happy-path assertions should bind live response headers, persisted `route_signals.outcome_evidence`, and unchanged-policy replay parity for the same request shape. Degraded-path assertions should keep replay honesty explicit when persisted route signals are incomplete and preserve the anti-sprawl boundary by proving missing-route-signal handling rather than adding a replay-only contract.

## Inputs

- ``tests/test_chat_completions.py``
- ``tests/test_response_headers.py``
- ``tests/test_governance_api.py``
- ``docs/m009-integrated-proof.md``
- ``docs/route-decision-vocabulary.md``

## Expected Output

- ``tests/test_chat_completions.py``
- ``tests/test_response_headers.py``
- ``tests/test_governance_api.py``

## Verification

./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or policy_denied" && ./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals" && ./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or usage_ledger)"

## Observability Impact

Strengthens the executable inspection seam for runtime headers, ledger rows, and replay payloads so parity/degraded drift fails in the same backend surfaces operators and future agents already inspect.
