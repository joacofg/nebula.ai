---
id: T01
parent: S02
milestone: M009
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - tests/test_router_signals.py
  - tests/test_service_flows.py
key_decisions:
  - Kept `GovernanceStore.summarize_calibration_evidence()` as the sole source of live outcome-evidence classification and passed its summary into router scoring rather than duplicating classification logic in the router.
  - Made the runtime observability contract additive: existing route-mode and score fields remain stable while new outcome-evidence state and score-factor details are appended for request-first diagnostics.
duration: 
verification_result: passed
completed_at: 2026-04-27T15:11:49.606Z
blocker_discovered: false
---

# T01: Extended live routing to score against tenant outcome evidence and persist the additive route-signal contract.

**Extended live routing to score against tenant outcome evidence and persist the additive route-signal contract.**

## What Happened

Updated the shared router contract so calibrated route scoring can optionally consume a tenant-scoped `CalibrationEvidenceSummary` without reclassifying evidence. `RouterService` now carries bounded `outcome_evidence` details and additive score terms (`outcome_bonus`, `evidence_penalty`) inside `route_signals.score_components` while preserving existing route mode, replay, and explicit-override behavior. `PolicyService.evaluate()` now fetches tenant outcome evidence immediately before live route choice, passes that summary into routing, and appends a parity-friendly `outcome_evidence=...` segment to `policy_outcome` without changing hard-budget, soft-budget, calibrated-routing-disablement, or explicit-model guardrails. I also repaired a pre-existing duplicate `OutcomeEvidenceState` alias in `router_service.py` that was breaking the Python LSP process, then updated backend tests and runtime fakes to assert the new additive observability contract on both direct router decisions and real request/ledger persistence.

## Verification

Ran the task-plan verification commands after the final code changes. `./.venv/bin/pytest tests/test_router_signals.py -k "outcome or evidence or route"` passed 10/10 and confirmed the enriched `route_signals` payload, including persisted ledger assertions for `outcome_evidence` and additive score components. `./.venv/bin/pytest tests/test_service_flows.py -k "outcome_grounded or policy_service_live_evidence or hard_budget"` passed 2/2 and confirmed live policy evidence lookup, score impact, preserved hard-budget downgrade behavior, and parity-friendly policy outcomes.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_router_signals.py -k "outcome or evidence or route"` | 0 | ✅ pass | 960ms |
| 2 | `./.venv/bin/pytest tests/test_service_flows.py -k "outcome_grounded or policy_service_live_evidence or hard_budget"` | 0 | ✅ pass | 650ms |

## Deviations

Recorded the missing executor skills (`verify-before-complete`, `test`) in execution behavior rather than task-plan frontmatter because the DB-backed task plan artifact was not the canonical edit target for this task. No runtime scope changes beyond the additive live-evidence contract were introduced.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/router_service.py`
- `src/nebula/services/policy_service.py`
- `tests/test_router_signals.py`
- `tests/test_service_flows.py`
