---
id: T02
parent: S03
milestone: M005
provides: []
requires: []
affects: []
key_files: ["src/nebula/services/policy_service.py", "src/nebula/services/policy_simulation_service.py", "tests/test_governance_runtime_hardening.py", "tests/test_service_flows.py", "tests/test_governance_api.py", ".gsd/milestones/M005/slices/S03/tasks/T02-SUMMARY.md"]
key_decisions: ["Enforced cumulative hard-budget outcomes centrally in `PolicyService.evaluate()` and reused that exact path from simulation via `before_timestamp` rather than building a replay-only budget engine.", "Allowed hard-budget downgrade only for auto/default-to-local-compatible requests and kept explicit premium or premium-only paths as exact denials so operator evidence matches the real routing contract."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x` and confirmed the new hard-budget downgrade, explicit-deny, soft-budget advisory, and replay-window tests passed. Ran `./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x` and confirmed runtime ledger and simulation API evidence now show downgrade-versus-deny outcomes with exact operator-readable detail."
completed_at: 2026-03-28T03:37:52.165Z
blocker_discovered: false
---

# T02: Centralized hard-budget downgrade and denial behavior in PolicyService and aligned simulation replay semantics.

> Centralized hard-budget downgrade and denial behavior in PolicyService and aligned simulation replay semantics.

## What Happened
---
id: T02
parent: S03
milestone: M005
key_files:
  - src/nebula/services/policy_service.py
  - src/nebula/services/policy_simulation_service.py
  - tests/test_governance_runtime_hardening.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - .gsd/milestones/M005/slices/S03/tasks/T02-SUMMARY.md
key_decisions:
  - Enforced cumulative hard-budget outcomes centrally in `PolicyService.evaluate()` and reused that exact path from simulation via `before_timestamp` rather than building a replay-only budget engine.
  - Allowed hard-budget downgrade only for auto/default-to-local-compatible requests and kept explicit premium or premium-only paths as exact denials so operator evidence matches the real routing contract.
duration: ""
verification_result: passed
completed_at: 2026-03-28T03:37:52.166Z
blocker_discovered: false
---

# T02: Centralized hard-budget downgrade and denial behavior in PolicyService and aligned simulation replay semantics.

**Centralized hard-budget downgrade and denial behavior in PolicyService and aligned simulation replay semantics.**

## What Happened

Added focused runtime, service, and admin/API coverage for hard cumulative budget exhaustion, then updated PolicyService.evaluate() to compute tenant cumulative spend once, preserve soft-budget advisory behavior, emit stable hard-budget policy_outcome evidence, and choose downgrade or denial deterministically based on request compatibility plus hard_budget_enforcement. Updated PolicySimulationService to pass replay route signals and before_timestamp into the same evaluation path so runtime and simulation now share one budget engine. During verification I corrected test assumptions around stubbed provider ledger cost and replay-window semantics so the new coverage proves the real contract rather than fixture guesses.

## Verification

Ran `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x` and confirmed the new hard-budget downgrade, explicit-deny, soft-budget advisory, and replay-window tests passed. Ran `./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x` and confirmed runtime ledger and simulation API evidence now show downgrade-versus-deny outcomes with exact operator-readable detail.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x` | 0 | ✅ pass | 570ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x` | 0 | ✅ pass | 1080ms |


## Deviations

Adjusted the new API tests to derive hard-budget thresholds from the actual persisted baseline premium cost rather than assuming `max_tokens` would change stubbed provider ledger spend, and updated the replay-window test to include prior spend because the shared `before_timestamp` contract intentionally excludes the replayed row itself.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/policy_service.py`
- `src/nebula/services/policy_simulation_service.py`
- `tests/test_governance_runtime_hardening.py`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`
- `.gsd/milestones/M005/slices/S03/tasks/T02-SUMMARY.md`


## Deviations
Adjusted the new API tests to derive hard-budget thresholds from the actual persisted baseline premium cost rather than assuming `max_tokens` would change stubbed provider ledger spend, and updated the replay-window test to include prior spend because the shared `before_timestamp` contract intentionally excludes the replayed row itself.

## Known Issues
None.
