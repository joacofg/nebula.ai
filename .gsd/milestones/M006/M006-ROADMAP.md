# M006: M006

**Vision:** Close the remaining routing gap from M005 by turning Nebula’s heuristic-first router into an interpretable, outcome-aware calibrated router that uses recent tenant-scoped ledger evidence, keeps runtime and simulation aligned, exposes calibration state through existing operator surfaces, and validates R039 without widening Nebula into a black-box optimizer, analytics product, hosted-authority expansion, or new public API program.

## Success Criteria

- Route choice is no longer explained primarily by prompt-length heuristics alone.
- The calibrated decision remains interpretable in code, ledger output, and operator inspection surfaces.
- Runtime routing and policy simulation replay use the same calibration semantics.
- Nebula clearly reports when calibrated routing is active versus when it has fallen back to heuristic-only mode.
- The final proof stays narrow and operator-driven, with no black-box or analytics drift.

## Slices

- [x] **S01: Calibrated routing core** `risk:high` `depends:[]`
  > After this: After this: a routed request can show calibrated-versus-heuristic routing mode and an explicit additive score breakdown in runtime evidence.

- [x] **S02: Ledger-backed calibration evidence** `risk:high` `depends:[S01]`
  > After this: After this: the router can derive tenant-scoped calibration summaries from existing ledger metadata and report when evidence is sufficient, stale, or thin.

- [x] **S03: Runtime / simulation parity** `risk:medium` `depends:[S01,S02]`
  > After this: After this: policy simulation replay reports the same calibrated routing and degraded-mode semantics as live runtime for the same tenant traffic class.

- [x] **S04: Operator inspection surfaces** `risk:medium` `depends:[S01,S02,S03]`
  > After this: After this: operators can inspect calibrated-vs-heuristic routing state and contributing evidence in existing request-detail and Observability surfaces.

- [x] **S05: Integrated proof and close-out** `risk:low` `depends:[S01,S02,S03,S04]`
  > After this: After this: one integrated proof path demonstrates calibrated live routing, replay parity, degraded fallback, operator inspection, and milestone scope discipline end-to-end.

## Boundary Map

## Boundary Map

### S01 → S02
Produces:
- `router_calibration.py` / router calibration seam → typed calibrated-routing input and score breakdown
- `RouteDecision.signals` / governance types → calibrated-vs-heuristic mode markers and explicit contributing signal fields
- runtime request evidence → persisted calibrated routing metadata for live requests

Consumes:
- nothing (first slice)

### S02 → S03
Produces:
- ledger-backed calibration summary derivation → bounded tenant-scoped recent-window evidence and sufficiency / staleness state
- governance / persistence shapes → calibration evidence contract reusable by runtime and replay

Consumes from S01:
- calibrated route-decision seam and mode markers

### S01,S02 → S04
Produces:
- operator-readable calibration state contract → labels and fields for calibrated vs heuristic-only routing
- request-detail evidence inputs → bounded contributing-signal data for inspection surfaces

Consumes from S01:
- calibrated route-decision seam and mode markers

Consumes from S02:
- calibration summary / sufficiency / staleness evidence

### S01,S02,S03,S04 → S05
Produces:
- final integrated proof path → calibrated runtime request, replay parity evidence, degraded-mode evidence, operator inspection, and evaluation guidance

Consumes from S01:
- calibrated routing runtime behavior

Consumes from S02:
- ledger-backed calibration evidence model

Consumes from S03:
- runtime / replay parity semantics

Consumes from S04:
- operator inspection surfaces and wording
