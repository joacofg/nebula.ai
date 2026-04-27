# S01: Outcome evidence contract

**Goal:** Lock the shared backend contract for tenant-scoped outcome evidence so downstream runtime routing, replay, and operator evidence all consume one deterministic summary seam with explicit sufficient/thin/stale/degraded semantics.
**Demo:** After this: one tenant’s recent ledger-backed outcome evidence can be derived deterministically with explicit sufficient/thin/stale/degraded states and proved through backend tests and typed artifacts.

## Must-Haves

- `GovernanceStore.summarize_calibration_evidence()` deterministically derives tenant-scoped evidence summaries from bounded recent ledger rows with explicit sufficient/thin/stale/degraded semantics.
- Typed governance/backend artifacts carry the outcome evidence vocabulary in a way that remains serializable through existing request evidence and replay surfaces.
- Backend tests prove summary-state transitions, tenant/window scoping, and governance-suppressed degraded behavior without changing live route-choice semantics yet.

## Proof Level

- This slice proves: contract

## Integration Closure

This slice closes the backend contract and proof seam only: governance models, store summarization, and replay-facing/admin response shapes agree on one outcome-evidence vocabulary. Live route-choice behavior, request-level persistence of new factors, and console rendering remain for S02-S04.

## Verification

- The slice keeps the existing authoritative inspection seams intact by making degraded/thin/stale state derivable from persisted ledger rows and visible through existing backend summary payloads and tests. Failure diagnosis remains request/ledger-first: a future agent can inspect `route_signals`, `route_reason`, and summary counts/reasons to understand why evidence is sufficient, thin, stale, or degraded.

## Tasks

- [x] **T01: Define the outcome-evidence contract and state precedence** `est:1h`
  Codify the shared backend vocabulary before touching derivation logic so S02-S04 inherit one stable seam rather than re-inventing semantics. Use the existing calibration contract as the starting point, evolve it additively where possible, and make the degraded summary-state precedence explicit in code comments and tests.

Steps:
1. Inspect the current calibration summary types and router score types, then define the outcome-evidence state vocabulary needed by M009 (`sufficient`, `thin`, `stale`, `degraded`) plus any renamed/additive reason fields required for replay-safe serialization.
2. Update `src/nebula/models/governance.py` and any directly-coupled typed seams so admin/policy simulation payloads can carry the richer state without widening Nebula into a new API family.
3. Add or update focused tests that lock state precedence expectations at the contract level, including the key design choice that degraded is a summary-state outcome rather than only a per-row reason.
4. Document any compatibility assumption inline in the code/tests so downstream slices know whether they should keep using `calibration_summary` naming while reading richer outcome semantics.
  - Files: `src/nebula/models/governance.py`, `src/nebula/services/router_service.py`, `tests/test_service_flows.py`, `tests/test_governance_api.py`
  - Verify: pytest tests/test_service_flows.py -k "calibration_summary or outcome"

- [ ] **T02: Implement deterministic ledger summarization for sufficient/thin/stale/degraded evidence** `est:1h`
  Move the highest-risk ambiguity into one authoritative derivation path. This task should make `GovernanceStore.summarize_calibration_evidence()` the fail-safe truth seam for M009 by encoding bounded-window classification, summary-state precedence, and honest handling of governance-suppressed or replay-degraded rows.

Steps:
1. Update `src/nebula/services/governance_store.py` so eligible, sufficient, gated, excluded, and degraded row classification remains deterministic and tenant-scoped while the summary state now reflects explicit degraded semantics when recent eligible evidence is present but not trustworthy enough for grounded use.
2. Preserve the existing bounded-read behavior (`limit`, optional time window) and make any stale-vs-degraded precedence rule explicit in code comments and state reasons.
3. Keep strict-governance `route_signals` suppression and replay-degraded rows distinguishable through degraded reasons so S03 can reconstruct the honest approximation story later.
4. Add focused store-level/service-level tests for no evidence, thin evidence, stale evidence, degraded eligible evidence, and sufficient fresh evidence, including tenant/window scoping assertions.
  - Files: `src/nebula/services/governance_store.py`, `tests/test_service_flows.py`, `tests/test_governance_api.py`
  - Verify: pytest tests/test_service_flows.py -k "governance_store_calibration_summary or calibration_summary"

- [ ] **T03: Prove replay-facing and admin summary consumers honor the new contract** `est:45m`
  Close the slice by proving that the richer evidence contract survives through existing backend consumers without changing live route choice yet. This gives S02/S03 a stable integration seam and catches accidental drift between typed models, summary derivation, and simulation/admin responses.

Steps:
1. Update replay/admin-facing tests to assert the summary contract shape and semantics exposed through policy simulation and governance APIs still serialize correctly and remain bounded to persisted ledger metadata.
2. Verify that request rows with suppressed or degraded `route_signals` surface honest degraded summary reasons instead of being silently counted as thin/sufficient evidence.
3. Keep assertions focused on contract stability and replay-safe payloads; do not introduce live routing behavior changes in this slice.
4. If needed, add narrowly scoped fixtures/helpers to keep the new evidence-state assertions readable for downstream slices.
  - Files: `src/nebula/services/policy_simulation_service.py`, `tests/test_governance_api.py`, `tests/test_service_flows.py`
  - Verify: pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation" && pytest tests/test_service_flows.py -k "policy_simulation_exposes_window_calibration_summary"

## Files Likely Touched

- src/nebula/models/governance.py
- src/nebula/services/router_service.py
- tests/test_service_flows.py
- tests/test_governance_api.py
- src/nebula/services/governance_store.py
- src/nebula/services/policy_simulation_service.py
