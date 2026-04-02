# M006: 

## Vision
Close the remaining routing gap from M005 by turning Nebula’s heuristic-first router into an interpretable, outcome-aware calibrated router that uses recent tenant-scoped ledger evidence, keeps runtime and simulation aligned, exposes calibration state through existing operator surfaces, and validates R039 without widening Nebula into a black-box optimizer, analytics product, hosted-authority expansion, or new public API program.

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S01 | Calibrated routing core | high | — | ✅ | After this: a routed request can show calibrated-versus-heuristic routing mode and an explicit additive score breakdown in runtime evidence. |
| S02 | Ledger-backed calibration evidence | high | S01 | ✅ | After this: the router can derive tenant-scoped calibration summaries from existing ledger metadata and report when evidence is sufficient, stale, or thin. |
| S03 | Runtime / simulation parity | medium | S01, S02 | ✅ | After this: policy simulation replay reports the same calibrated routing and degraded-mode semantics as live runtime for the same tenant traffic class. |
| S04 | Operator inspection surfaces | medium | S01, S02, S03 | ⬜ | After this: operators can inspect calibrated-vs-heuristic routing state and contributing evidence in existing request-detail and Observability surfaces. |
| S05 | Integrated proof and close-out | low | S01, S02, S03, S04 | ⬜ | After this: one integrated proof path demonstrates calibrated live routing, replay parity, degraded fallback, operator inspection, and milestone scope discipline end-to-end. |
