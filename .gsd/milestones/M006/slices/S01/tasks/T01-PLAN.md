---
estimated_steps: 5
estimated_files: 3
skills_used: []
---

# T01: Define the shared calibrated routing contract

Move `RouterService` from duplicated heuristic branches to a shared calibrated scoring helper used by both live routing and replay. Keep the replay-critical signal subset stable (`token_count`, `keyword_match`, `complexity_tier`) while adding explicit routing mode markers and additive breakdown fields that later slices can consume without guessing. Update the route vocabulary doc and focused router tests in the same task so the contract is nailed down before policy or persistence work builds on it.

Steps:
1. Extract shared router helpers in `src/nebula/services/router_service.py` that derive calibrated score components, route mode markers, reason codes, and target selection for both live and replay paths.
2. Expand the `signals` payload additively so it includes calibrated-versus-heuristic/degraded state plus named score components, while preserving existing keys consumed by `PolicySimulationService` and current ledger/detail surfaces.
3. Update `tests/test_router_signals.py` to assert the new score breakdown, route reason vocabulary, replay compatibility, and degraded/heuristic fallback branches; update `docs/route-decision-vocabulary.md` to match the shipped contract exactly.

## Inputs

- ``src/nebula/services/router_service.py``
- ``tests/test_router_signals.py``
- ``docs/route-decision-vocabulary.md``
- ``src/nebula/services/policy_simulation_service.py``

## Expected Output

- ``src/nebula/services/router_service.py``
- ``tests/test_router_signals.py``
- ``docs/route-decision-vocabulary.md``

## Verification

./.venv/bin/pytest tests/test_router_signals.py -x

## Observability Impact

Defines the runtime/ledger route-signal vocabulary that later slices and future agents inspect. The task should make calibrated mode, degraded mode, and additive score components mechanically visible in `route_signals` and `route_score`, not just implicit in code paths.
