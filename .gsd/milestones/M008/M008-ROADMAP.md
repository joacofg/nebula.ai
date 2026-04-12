# M008: Evidence Governance and Privacy Controls

## Vision
Make Nebula’s evidence layer tenant-governed, retention-aware, historically explainable, and visibly bounded without widening into payload capture, compliance-platform sprawl, or hosted authority.

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S01 | S01 | high | — | ✅ | Operators can configure explicit tenant evidence-retention and metadata-minimization policy through the existing policy boundary, and backend/admin contracts treat those controls as runtime-enforced rather than advisory. |
| S02 | S02 | high | — | ⬜ | New requests persist only the allowed evidence shape for the tenant and carry per-request governance markers so request detail can later show what policy applied at write time. |
| S03 | Retention lifecycle enforcement | high | S01, S02 | ⬜ | Expired evidence is actually deleted according to tenant policy, with a bounded retention execution path that can be exercised and verified rather than inferred. |
| S04 | Operator evidence-boundary surfaces | medium | S02, S03 | ⬜ | The policy page and request-detail surface clearly show the effective evidence boundary, including what is retained, suppressed, or no longer available due to policy. |
| S05 | Integrated governance proof | medium | S01, S02, S03, S04 | ⬜ | Nebula proves end to end that tenant policy governs persistence and deletion, request detail explains historical evidence truthfully, and the hosted metadata-only boundary remains intact without payload-capture or hosted-authority drift. |
