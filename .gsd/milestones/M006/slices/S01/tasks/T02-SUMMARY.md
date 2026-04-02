---
id: T02
parent: S01
milestone: M006
provides: []
requires: []
affects: []
key_files: ["src/nebula/services/policy_service.py", "src/nebula/services/chat_service.py", "src/nebula/api/routes/chat.py", "tests/test_governance_runtime_hardening.py", "tests/test_service_flows.py", "tests/test_response_headers.py", ".gsd/milestones/M006/slices/S01/tasks/T02-SUMMARY.md"]
key_decisions: ["Exposed `X-Nebula-Route-Mode` only when route signals exist so explicit override routes do not falsely claim calibrated routing.", "Preserved the original calibrated route score and signal payload across fallback-blocked/provider-error evidence so response headers and usage-ledger rows stay correlated."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran LSP diagnostics on the touched runtime files and fixed the missing typing imports in chat_service.py. Ran a stronger focused pytest selection covering governance runtime, service flows, and response headers, then ran the task-plan pytest command exactly as written. Both commands passed; the summary notes that the literal task-plan command under-selected and skipped the touched response-header file because of pytest argument ordering."
completed_at: 2026-04-02T02:54:43.112Z
blocker_discovered: false
---

# T02: Wired calibrated routing metadata through policy resolution, error headers, and usage-ledger evidence.

> Wired calibrated routing metadata through policy resolution, error headers, and usage-ledger evidence.

## What Happened
---
id: T02
parent: S01
milestone: M006
key_files:
  - src/nebula/services/policy_service.py
  - src/nebula/services/chat_service.py
  - src/nebula/api/routes/chat.py
  - tests/test_governance_runtime_hardening.py
  - tests/test_service_flows.py
  - tests/test_response_headers.py
  - .gsd/milestones/M006/slices/S01/tasks/T02-SUMMARY.md
key_decisions:
  - Exposed `X-Nebula-Route-Mode` only when route signals exist so explicit override routes do not falsely claim calibrated routing.
  - Preserved the original calibrated route score and signal payload across fallback-blocked/provider-error evidence so response headers and usage-ledger rows stay correlated.
duration: ""
verification_result: passed
completed_at: 2026-04-02T02:54:43.114Z
blocker_discovered: false
---

# T02: Wired calibrated routing metadata through policy resolution, error headers, and usage-ledger evidence.

**Wired calibrated routing metadata through policy resolution, error headers, and usage-ledger evidence.**

## What Happened

Extended policy resolution so hard-budget context survives as structured runtime state, preserved calibrated route score and signals through fallback-blocked error handling and ledger writes, and added additive route-mode response headers only when routed requests actually carry calibrated/degraded signals. Strengthened focused backend tests to prove hard-budget downgrades, real-request ledger correlation, and fallback-blocked paths all expose the same calibrated routing story across headers and persisted usage evidence.

## Verification

Ran LSP diagnostics on the touched runtime files and fixed the missing typing imports in chat_service.py. Ran a stronger focused pytest selection covering governance runtime, service flows, and response headers, then ran the task-plan pytest command exactly as written. Both commands passed; the summary notes that the literal task-plan command under-selected and skipped the touched response-header file because of pytest argument ordering.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `lsp diagnostics src/nebula/services/policy_service.py` | 0 | ✅ pass | 0ms |
| 2 | `lsp diagnostics src/nebula/services/chat_service.py` | 0 | ✅ pass | 0ms |
| 3 | `lsp diagnostics src/nebula/api/routes/chat.py` | 0 | ✅ pass | 0ms |
| 4 | `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py tests/test_response_headers.py -k "simulation or runtime_policy or response_headers or denied or fallback or hard_budget" -x` | 0 | ✅ pass | 3600ms |
| 5 | `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "simulation or runtime_policy" tests/test_response_headers.py -x` | 0 | ✅ pass | 4000ms |


## Deviations

Executed the task-plan pytest command exactly as written, but its `-k` placement only selected tests before `tests/test_response_headers.py`, so I added a stronger focused pytest run to verify the touched header contract as intended.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/policy_service.py`
- `src/nebula/services/chat_service.py`
- `src/nebula/api/routes/chat.py`
- `tests/test_governance_runtime_hardening.py`
- `tests/test_service_flows.py`
- `tests/test_response_headers.py`
- `.gsd/milestones/M006/slices/S01/tasks/T02-SUMMARY.md`


## Deviations
Executed the task-plan pytest command exactly as written, but its `-k` placement only selected tests before `tests/test_response_headers.py`, so I added a stronger focused pytest run to verify the touched header contract as intended.

## Known Issues
None.
