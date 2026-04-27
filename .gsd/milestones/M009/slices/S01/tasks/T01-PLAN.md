---
estimated_steps: 6
estimated_files: 4
skills_used: []
---

# T01: Define the outcome-evidence contract and state precedence

Codify the shared backend vocabulary before touching derivation logic so S02-S04 inherit one stable seam rather than re-inventing semantics. Use the existing calibration contract as the starting point, evolve it additively where possible, and make the degraded summary-state precedence explicit in code comments and tests.

Steps:
1. Inspect the current calibration summary types and router score types, then define the outcome-evidence state vocabulary needed by M009 (`sufficient`, `thin`, `stale`, `degraded`) plus any renamed/additive reason fields required for replay-safe serialization.
2. Update `src/nebula/models/governance.py` and any directly-coupled typed seams so admin/policy simulation payloads can carry the richer state without widening Nebula into a new API family.
3. Add or update focused tests that lock state precedence expectations at the contract level, including the key design choice that degraded is a summary-state outcome rather than only a per-row reason.
4. Document any compatibility assumption inline in the code/tests so downstream slices know whether they should keep using `calibration_summary` naming while reading richer outcome semantics.

## Inputs

- ``src/nebula/models/governance.py``
- ``src/nebula/services/router_service.py``
- ``tests/test_service_flows.py``
- ``tests/test_governance_api.py``

## Expected Output

- ``src/nebula/models/governance.py``
- ``src/nebula/services/router_service.py``
- ``tests/test_service_flows.py``

## Verification

pytest tests/test_service_flows.py -k "calibration_summary or outcome"

## Observability Impact

Clarifies the typed evidence-state and reason fields future agents inspect in admin/replay payloads; makes degraded-state diagnosis explicit instead of inferred from scattered counters.
