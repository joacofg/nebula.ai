---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T02: Implement deterministic ledger summarization for sufficient/thin/stale/degraded evidence

Move the highest-risk ambiguity into one authoritative derivation path. This task should make `GovernanceStore.summarize_calibration_evidence()` the fail-safe truth seam for M009 by encoding bounded-window classification, summary-state precedence, and honest handling of governance-suppressed or replay-degraded rows.

Steps:
1. Update `src/nebula/services/governance_store.py` so eligible, sufficient, gated, excluded, and degraded row classification remains deterministic and tenant-scoped while the summary state now reflects explicit degraded semantics when recent eligible evidence is present but not trustworthy enough for grounded use.
2. Preserve the existing bounded-read behavior (`limit`, optional time window) and make any stale-vs-degraded precedence rule explicit in code comments and state reasons.
3. Keep strict-governance `route_signals` suppression and replay-degraded rows distinguishable through degraded reasons so S03 can reconstruct the honest approximation story later.
4. Add focused store-level/service-level tests for no evidence, thin evidence, stale evidence, degraded eligible evidence, and sufficient fresh evidence, including tenant/window scoping assertions.

## Inputs

- ``src/nebula/services/governance_store.py``
- ``tests/test_service_flows.py``
- ``tests/test_governance_api.py``

## Expected Output

- ``src/nebula/services/governance_store.py``
- ``tests/test_service_flows.py``
- ``tests/test_governance_api.py``

## Verification

pytest tests/test_service_flows.py -k "governance_store_calibration_summary or calibration_summary"

## Observability Impact

Improves failure diagnosis by ensuring summary state, state reason, and degraded/gated/excluded counters all point back to authoritative ledger evidence instead of hidden routing heuristics.
