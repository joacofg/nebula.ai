---
verdict: needs-attention
remediation_round: 0
---

# Milestone Validation: M009

## Success Criteria Checklist
## Reviewer C — Acceptance Criteria

- [x] **S01:** A deterministic recent tenant-scoped outcome-evidence contract exists, including explicit sufficient/thin/stale/degraded state rules and typed backend coverage. | Evidence: No slice `ASSESSMENT` file present; covered by `S01-SUMMARY.md` and `S01-UAT.md`. `S01-SUMMARY.md` states `verification_result: passed` and cites passing backend tests for `tests/test_service_flows.py` and `tests/test_governance_api.py`, proving deterministic tenant/window scoping, degraded precedence, and the shared `calibration_summary` contract.
- [x] **S02:** A real `POST /v1/chat/completions` request can route differently because of recent tenant-scoped outcome evidence, and the persisted request row records the actual factors used. | Evidence: No slice `ASSESSMENT` file present; covered by `S02-SUMMARY.md` and `S02-UAT.md`. `S02-SUMMARY.md` states live routing now consumes tenant outcome evidence and cites passing `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and `tests/test_governance_api.py` proving route flips plus persisted `route_signals.outcome_evidence`, `outcome_bonus`, and `evidence_penalty`.
- [x] **S03:** `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replays the same outcome-grounded semantics as runtime and marks degraded or approximate behavior honestly when evidence is incomplete. | Evidence: No slice `ASSESSMENT` file present; covered by `S03-SUMMARY.md` and `S03-UAT.md`. `S03-SUMMARY.md` states replay reuses the same tenant-window `calibration_summary` and additive scoring semantics as runtime, with passing `tests/test_service_flows.py`, `tests/test_governance_api.py`, and `console/src/components/policy/policy-form.test.tsx`, including honest degraded replay when persisted signals are incomplete.
- [x] **S04:** The selected request in request detail / Observability explains whether routing was grounded, thin, stale, or degraded, and keeps tenant summary context secondary to the persisted request row. | Evidence: No slice `ASSESSMENT` file present; covered by `S04-SUMMARY.md` and `S04-UAT.md`. `S04-SUMMARY.md` states selected-request Observability now explains grounded/thin/stale/degraded states from persisted `route_signals`, with passing `ledger-request-detail.test.tsx`, `observability/page.test.tsx`, and `observability-page.test.tsx` proving request-first hierarchy and subordinate summary cards.
- [x] **S05:** One integrated proof covers a happy-path routed request and an honest degraded-path request without widening Nebula into analytics-product work, black-box optimization, hosted authority, or broad public API expansion. | Evidence: No slice `ASSESSMENT` file present; covered by `S05-SUMMARY.md`, `S05-UAT.md`, and `docs/m009-integrated-proof.md`. `S05-SUMMARY.md` states the milestone closed with a pointer-first integrated proof plus passing backend and console verification for happy and degraded paths; `docs/m009-integrated-proof.md` explicitly orders public request → ledger correlation → replay parity → selected-request-first Observability and calls out anti-drift boundaries.

PASS

## Slice Delivery Audit
| Slice | SUMMARY.md | Assessment result | Notes |
|---|---|---|---|
| S01 | Present (`.gsd/milestones/M009/slices/S01/S01-SUMMARY.md`) | No ASSESSMENT file present | Summary and UAT exist; verification_result is `passed`; known limitations are bounded to later slices. |
| S02 | Present (`.gsd/milestones/M009/slices/S02/S02-SUMMARY.md`) | No ASSESSMENT file present | Summary and UAT exist; verification_result is `passed`; noted verification-command deviation was repaired during execution. |
| S03 | Present (`.gsd/milestones/M009/slices/S03/S03-SUMMARY.md`) | No ASSESSMENT file present | Summary and UAT exist; verification_result is `passed`; bounded limitation defers only operator-surface work to S04/S05. |
| S04 | Present (`.gsd/milestones/M009/slices/S04/S04-SUMMARY.md`) | No ASSESSMENT file present | Summary and UAT exist; verification_result is `passed`; limitation is explicit that final end-to-end proof remains for S05. |
| S05 | Present (`.gsd/milestones/M009/slices/S05/S05-SUMMARY.md`) | No ASSESSMENT file present | Summary and UAT exist; verification_result is `passed`; closes integrated proof and anti-drift boundary. |

Verdict: needs-attention because every slice has SUMMARY evidence and completed status, but the requested per-slice ASSESSMENT artifacts are absent, so MV02 cannot be rated as a clean pass under the stated validation question.

## Cross-Slice Integration
## Reviewer B — Cross-Slice Integration

| Boundary | Producer Summary | Consumer Summary | Status |
|---|---|---|---|
| S01 → S02 | `S01-SUMMARY.md` says S01 provides the deterministic tenant-scoped outcome-evidence summary contract, authoritative `GovernanceStore.summarize_calibration_evidence()` seam, and replay-safe degraded reason vocabulary. | `S02-SUMMARY.md` says live routing wires `GovernanceStore.summarize_calibration_evidence()` into `PolicyService.evaluate()` and reuses the shared summary seam instead of re-classifying evidence. | Honored |
| S02 → S03 | `S02-SUMMARY.md` says S02 provides persisted live route factors, additive runtime scoring semantics, and request evidence fields on usage-ledger rows. | `S03-SUMMARY.md` frontmatter `requires` explicitly consumes S02’s persisted live route factors, additive runtime scoring semantics, and request evidence fields to prove unchanged-policy replay parity. | Honored |
| S02 → S04 | `S02-SUMMARY.md` says persisted `UsageLedgerRecord.route_signals` now carries `outcome_evidence` and additive score components for live requests. | `S04-SUMMARY.md` frontmatter `requires` explicitly consumes S02’s persisted request-level `route_signals` and outcome-grounded route factors for selected-request explanation. | Honored |
| S03 → S04 | `S03-SUMMARY.md` says replay keeps the additive console/admin evidence contract and extends `calibration_summary.state` with `degraded` rather than a replay-only field. | `S04-SUMMARY.md` frontmatter `requires` explicitly consumes S03’s replay-aligned grounded/thin/stale/degraded vocabulary carried through `calibration_summary` for supporting operator context. | Honored |
| S02 → S05 | `S02-SUMMARY.md` says live request routing can flip because of tenant evidence and headers / `policy_outcome` / ledger row agree on persisted grounded factors. | `S05-SUMMARY.md` says the selected happy-path request proves the chain from live `POST /v1/chat/completions` response headers into persisted `route_signals.outcome_evidence` and unchanged-policy replay parity. | Honored |
| S03 → S05 | `S03-SUMMARY.md` says replay now reuses the same tenant-window evidence summary and additive routing semantics as runtime, including honest degraded replay when persisted signals are incomplete. | `S05-SUMMARY.md` says degraded replay tests preserve honesty when persisted route signals are incomplete by returning missing parity fields rather than inventing replay-only metadata. | Honored |
| S04 → S05 | `S04-SUMMARY.md` says selected-request Observability explains grounded/thin/stale/degraded states while keeping request-first authority. | `S05-SUMMARY.md` says T03 hardened the request-first console proof by keeping the selected request row authoritative in deterministic request-detail coverage and leaving broader Observability framing intact. | Honored |

PASS

## Requirement Coverage
## Reviewer A — Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| R073 | COVERED | S01 establishes the tenant-scoped outcome-evidence summary contract consumed by downstream work. S02 explicitly says live chat routing now consumes bounded tenant-scoped outcome evidence at decision time and proves a real request can route differently because of recent tenant evidence while preserving guardrails. |
| R074 | COVERED | S03 explicitly advances and validates replay parity: `PolicyService.evaluate()` accepts an injected calibration evidence summary, `PolicySimulationService.simulate()` reuses one tenant-window summary across replayed rows, and tests prove unchanged-policy route score/mode parity plus honest degraded replay. |
| R075 | COVERED | S01 provides the typed factor/evidence vocabulary and authoritative summarization seam. S02 explicitly says persisted `UsageLedgerRecord.route_signals` now carries `outcome_evidence` state plus additive score components and validates header / `policy_outcome` / usage-ledger agreement on the same live request. |
| R076 | COVERED | S01 provides the shared grounded/thin/stale/degraded vocabulary. S04 explicitly advances and validates request-first Observability/request-detail explanation of grounded, thin, stale, degraded, rollout-disabled, and unscored states on existing surfaces, backed by focused console tests. |
| R077 | COVERED | S01 explicitly validates fail-safe classification for missing, thin, stale, degraded, and suppressed-route-signal cases through deterministic GovernanceStore summarization and backend tests. S03 and S05 reinforce that degraded replay remains honest when persisted signals are incomplete. |
| R078 | COVERED | S03 says replay credibility improved without adding provider side effects, replay-only evidence vocabulary, or dashboard-heavy surfaces. S04 says request-first explanation was added without a new dashboard. S05 validates the anti-sprawl boundary with pointer-first docs and focused tests, explicitly stating no new API surface, analytics dashboard, or hosted-authoritative behavior was introduced. |

PASS

## Verification Class Compliance
| Class | Planned Check | Evidence | Verdict |
|---|---|---|---|
| Contract | Unit/contract coverage for outcome-evidence derivation, additive scoring logic, and state transitions between grounded, thin, stale, and degraded behavior. | `M009-CONTEXT.md` defines this layer. `S01-SUMMARY.md` cites passing `tests/test_service_flows.py -k "calibration_summary or outcome or governance_store_calibration_summary or policy_simulation_exposes_window_calibration_summary"` and `tests/test_governance_api.py -k "calibration_summary or policy_simulation"` proving summary-state transitions, deterministic windowing/scoping, degraded precedence, and serialized contract stability. `S01-UAT.md` covers the same contract checks explicitly. | PASS |
| Integration | Backend integration coverage proving live routing uses the shared outcome-evidence contract, replay uses the same semantics, and persisted request rows capture the actual route factors used. | `S02-SUMMARY.md` cites passing live-path tests in `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and `tests/test_governance_api.py` proving runtime routing changes and persisted factors. `S03-SUMMARY.md` cites passing `tests/test_service_flows.py` and `tests/test_governance_api.py` proving unchanged-policy replay parity plus honest degraded replay. Together they cover runtime + persistence + replay. | PASS |
| Operational | When outcome evidence is missing, stale, thin, or inconsistent, Nebula degrades explicitly to simpler behavior, preserves service continuity, and records honest request-level evidence rather than blocking requests or pretending precision. | `M009-CONTEXT.md` defines this class. `S01-SUMMARY.md` proves explicit summary states and degraded reasons (`missing_route_signals`, `degraded_replay_signals`). `S02-SUMMARY.md` proves denied/constrained paths keep truthful evidence metadata and do not fabricate scored factors. `S03-SUMMARY.md` proves degraded replay honesty when persisted signals are incomplete. `S05-UAT.md` adds degraded-path replay expectation that parity fields stay unset rather than fabricated. | PASS |
| UAT | Final integrated verification proving both a happy-path request and a degraded-path request across public request → persisted ledger row → replay parity → request-first operator inspection. | `S05-UAT.md` defines the close-out artifact-driven UAT and requires `docs/m009-integrated-proof.md` plus passing backend and console seams. `S05-SUMMARY.md` cites passing `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_governance_api.py`, `ledger-request-detail.test.tsx`, `observability/page.test.tsx`, and `observability-page.test.tsx`. `docs/m009-integrated-proof.md` explicitly assembles the happy/degraded proof order. | PASS |


## Verdict Rationale
All three parallel review areas found substantive milestone evidence for requirements, cross-slice integration, success criteria, and verification classes. However, the slice-delivery audit cannot cleanly pass because each roadmap slice has a SUMMARY and UAT artifact but no per-slice ASSESSMENT artifact, despite MV02 explicitly asking to confirm a passing assessment for every slice; that artifact gap warrants needs-attention rather than remediation because delivered work and verification remain intact.
