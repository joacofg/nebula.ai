# M005: M005: Adaptive Decisioning Control Plane

## Vision
Turn Nebula's existing routing, policy, ledger, and semantic-cache surfaces into a stronger operator decisioning control plane. v4 should improve route quality, policy safety, spend control, and cache effectiveness through adaptive routing, simulation, hard guardrails, and recommendation-grade feedback while preserving Nebula's compatibility-first product shape and metadata-boundary discipline.

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S01 | Adaptive routing model | high | — | ✅ | Nebula has an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current heuristic. |
| S02 | Policy simulation loop | high | S01 | ✅ | An operator can simulate a candidate routing or policy change against recent ledger-backed traffic before saving it. |
| S03 | Hard budget guardrails | medium | S01 | ✅ | Tenant policy can enforce hard spend limits with explicit downgrade or denial behavior and explainable recorded outcomes. |
| S04 | Recommendations and cache controls | medium | S02, S03 | ✅ | Operators can see grounded next-best-action guidance and tune semantic-cache behavior with enough visibility to improve results intentionally. |
| S05 | Integrated v4 proof | low | S02, S03, S04 | ✅ | The full v4 decisioning story is assembled end to end and stays narrow, interpretable, and convincingly better than the prior heuristic posture. |
