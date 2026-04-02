---
id: T01
parent: S02
milestone: M006
provides: []
requires: []
affects: []
key_files: ["src/nebula/models/governance.py", "src/nebula/services/governance_store.py", "tests/test_service_flows.py", ".gsd/KNOWLEDGE.md"]
key_decisions: ["Derived calibration evidence strictly from existing usage-ledger metadata instead of adding persistence or replay-only summary fields.", "Excluded explicit overrides and policy-forced routing from calibration sufficiency while keeping calibrated_routing_disabled rows visible as gated operator-controlled traffic.", "Treated stale evidence as a function of the newest eligible ledger row so fresh degraded rows prevent a misleading stale classification."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x` and it passed with 7 selected tests passing. Ran LSP diagnostics for src/nebula/models/governance.py, src/nebula/services/governance_store.py, and tests/test_service_flows.py; all returned clean with no diagnostics."
completed_at: 2026-04-02T03:21:48.906Z
blocker_discovered: false
---

# T01: Added tenant-scoped calibration evidence summaries backed by existing ledger metadata and verified sufficient, thin, stale, gated, and degraded classification rules.

> Added tenant-scoped calibration evidence summaries backed by existing ledger metadata and verified sufficient, thin, stale, gated, and degraded classification rules.

## What Happened
---
id: T01
parent: S02
milestone: M006
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/governance_store.py
  - tests/test_service_flows.py
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Derived calibration evidence strictly from existing usage-ledger metadata instead of adding persistence or replay-only summary fields.
  - Excluded explicit overrides and policy-forced routing from calibration sufficiency while keeping calibrated_routing_disabled rows visible as gated operator-controlled traffic.
  - Treated stale evidence as a function of the newest eligible ledger row so fresh degraded rows prevent a misleading stale classification.
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:21:48.906Z
blocker_discovered: false
---

# T01: Added tenant-scoped calibration evidence summaries backed by existing ledger metadata and verified sufficient, thin, stale, gated, and degraded classification rules.

**Added tenant-scoped calibration evidence summaries backed by existing ledger metadata and verified sufficient, thin, stale, gated, and degraded classification rules.**

## What Happened

Extended src/nebula/models/governance.py with a bounded CalibrationEvidenceSummary contract and typed reason/count helpers. Implemented GovernanceStore.summarize_calibration_evidence() in src/nebula/services/governance_store.py to derive tenant-scoped evidence state from existing usage-ledger rows only, excluding explicit model overrides and policy-forced routing from sufficiency math while reporting calibrated_routing_disabled rows as operator-controlled gating and degraded/missing-signal rows as separate eligible-but-not-sufficient evidence. Added focused tests in tests/test_service_flows.py covering sufficient, thin, and stale classification plus override exclusion and gated-versus-degraded guardrails. Verification surfaced one fixture mistake around freshness; the final tests now lock the intended rule that staleness is based on the newest eligible evidence row.

## Verification

Ran `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x` and it passed with 7 selected tests passing. Ran LSP diagnostics for src/nebula/models/governance.py, src/nebula/services/governance_store.py, and tests/test_service_flows.py; all returned clean with no diagnostics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x` | 0 | ✅ pass | 620ms |
| 2 | `lsp diagnostics src/nebula/models/governance.py` | 0 | ✅ pass | 0ms |
| 3 | `lsp diagnostics src/nebula/services/governance_store.py` | 0 | ✅ pass | 0ms |
| 4 | `lsp diagnostics tests/test_service_flows.py` | 0 | ✅ pass | 0ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `tests/test_service_flows.py`
- `.gsd/KNOWLEDGE.md`


## Deviations
None.

## Known Issues
None.
