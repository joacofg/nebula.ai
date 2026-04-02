---
id: T01
parent: S01
milestone: M006
provides: []
requires: []
affects: []
key_files: ["src/nebula/services/router_service.py", "tests/test_router_signals.py", "docs/route-decision-vocabulary.md", ".gsd/KNOWLEDGE.md"]
key_decisions: ["Kept the replay-critical signal subset stable while adding route_mode and score_components additively.", "Preserved empty signals and zero route score for explicit override routes so calibrated evidence only appears for token_complexity decisions."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused router suite from the task plan and confirmed the shared router contract, replay compatibility, persisted route signals, and route-score header behavior all pass under the new implementation."
completed_at: 2026-04-02T02:48:04.970Z
blocker_discovered: false
---

# T01: Replaced duplicated router branches with a shared calibrated scoring contract and locked the additive route-signal vocabulary in tests and docs.

> Replaced duplicated router branches with a shared calibrated scoring contract and locked the additive route-signal vocabulary in tests and docs.

## What Happened
---
id: T01
parent: S01
milestone: M006
key_files:
  - src/nebula/services/router_service.py
  - tests/test_router_signals.py
  - docs/route-decision-vocabulary.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Kept the replay-critical signal subset stable while adding route_mode and score_components additively.
  - Preserved empty signals and zero route score for explicit override routes so calibrated evidence only appears for token_complexity decisions.
duration: ""
verification_result: passed
completed_at: 2026-04-02T02:48:04.971Z
blocker_discovered: false
---

# T01: Replaced duplicated router branches with a shared calibrated scoring contract and locked the additive route-signal vocabulary in tests and docs.

**Replaced duplicated router branches with a shared calibrated scoring contract and locked the additive route-signal vocabulary in tests and docs.**

## What Happened

RouterService now routes live traffic and replay traffic through the same calibrated scoring helpers instead of maintaining separate heuristic branches. The shared path derives token-count complexity, keyword contribution, policy bonus, route mode, and final target selection from a single breakdown object, then emits a consistent RouteDecision. The replay-critical subset stayed intact: token_count, keyword_match, and complexity_tier remain the canonical reconstruction inputs used by PolicySimulationService. On top of that, the router now adds route_mode, calibrated_routing, degraded_routing, and score_components additively so downstream slices can inspect whether replay had the full calibrated signal set or had to reconstruct missing inputs. Focused router coverage now asserts the live calibrated path, the low-token keyword-driven premium branch, replay parity when persisted signals are complete, degraded replay behavior when signals are missing, and the exact ledger/header evidence emitted for a routed request. The route vocabulary document was updated to match the shipped contract rather than the old heuristic-only description.

## Verification

Ran the focused router suite from the task plan and confirmed the shared router contract, replay compatibility, persisted route signals, and route-score header behavior all pass under the new implementation.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_router_signals.py -x` | 0 | ✅ pass | 950ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/router_service.py`
- `tests/test_router_signals.py`
- `docs/route-decision-vocabulary.md`
- `.gsd/KNOWLEDGE.md`


## Deviations
None.

## Known Issues
None.
