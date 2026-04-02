---
estimated_steps: 5
estimated_files: 6
skills_used: []
---

# T02: Wire calibrated routing through policy resolution and runtime evidence

Make policy evaluation and runtime propagation consume the new router contract without drifting. Preserve hard-budget downgrade/deny behavior over calibrated route decisions, keep replay reconstruction compatible with the stable subset of persisted signals, and prove that request headers plus usage-ledger rows carry the same calibrated story for a real request.

Steps:
1. Update `src/nebula/services/policy_service.py` and any small supporting code in `src/nebula/services/chat_service.py` or `src/nebula/api/routes/chat.py` so calibrated route reasons, scores, and signal payloads propagate unchanged through policy resolution, downgrade/fallback paths, headers, and ledger writes.
2. Extend focused backend tests in `tests/test_governance_runtime_hardening.py`, `tests/test_service_flows.py`, and `tests/test_response_headers.py` so they assert runtime/replay compatibility, hard-budget interaction, and outward header/ledger evidence for calibrated versus degraded routing.
3. Run Python diagnostics after edits and keep any contract-sensitive expectations aligned across runtime, replay, and persisted metadata.

## Inputs

- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/chat_service.py``
- ``src/nebula/api/routes/chat.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``tests/test_governance_runtime_hardening.py``
- ``tests/test_service_flows.py``
- ``tests/test_response_headers.py``
- ``src/nebula/services/router_service.py``

## Expected Output

- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/chat_service.py``
- ``src/nebula/api/routes/chat.py``
- ``tests/test_governance_runtime_hardening.py``
- ``tests/test_service_flows.py``
- ``tests/test_response_headers.py``

## Verification

./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "simulation or runtime_policy" tests/test_response_headers.py -x

## Observability Impact

Verifies the future debugging path: a request’s `X-Nebula-*` headers and the correlated usage-ledger row must expose the same calibrated or degraded routing evidence, including route reason and score components, even across downgrade and fallback paths.
