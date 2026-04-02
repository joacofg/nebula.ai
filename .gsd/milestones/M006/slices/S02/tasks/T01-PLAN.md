---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T01: Define and verify the ledger-backed calibration summary contract

Add the typed calibration-evidence summary models and deterministic ledger aggregation rules that S02 needs before simulation or UI wiring can proceed.

Steps:
1. Extend `src/nebula/models/governance.py` with a bounded tenant-scoped calibration summary contract that can express evidence state, recency, eligibility scope, gated/disabled counts, degraded counts, and operator-readable reason fields without widening persistence.
2. Implement the summary derivation seam in `src/nebula/services/governance_store.py` or a narrowly focused companion service, using only existing `UsageLedgerRecord` metadata and explicitly excluding override/policy-forced traffic from calibration sufficiency math while keeping `calibrated_routing_disabled` traffic visible as operator-controlled gating.
3. Add focused backend tests in `tests/test_service_flows.py` that prove sufficient, thin, and stale classification, plus the guardrails that override traffic does not poison the summary and gated rows are reported distinctly from accidental missing evidence.
4. Keep the contract bounded and deterministic so S03 and S04 can reuse it directly; do not add raw payload capture, new ledger columns, or analytics-style aggregate sprawl.

## Inputs

- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/router_service.py`
- `src/nebula/services/policy_service.py`
- `tests/test_service_flows.py`

## Expected Output

- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `tests/test_service_flows.py`

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x

## Observability Impact

Adds a durable backend inspection seam for tenant-scoped calibration evidence state and the reasons behind thin/stale/sufficient classification.
