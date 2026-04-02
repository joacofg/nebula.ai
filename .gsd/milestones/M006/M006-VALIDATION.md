---
verdict: pass
remediation_round: 0
---

# Milestone Validation: M006

## Success Criteria Checklist
- [x] **Interpretable calibrated routing core delivered.** S01 replaced duplicated heuristic branches with one shared calibrated scoring contract for live routing and replay, preserving the replay-critical subset while adding explicit `route_mode`, calibrated/degraded markers, and additive `score_components`. Evidence: S01 summary plus passing `tests/test_router_signals.py`, `tests/test_service_flows.py`, `tests/test_response_headers.py`, and `tests/test_governance_runtime_hardening.py`.
- [x] **Tenant-scoped ledger-backed calibration evidence delivered.** S02 derives `CalibrationEvidenceSummary` from existing usage-ledger metadata, reports sufficient/thin/stale/gated/degraded states, excludes override/policy-forced rows from sufficiency math, and reuses the same summary in policy simulation and operator surfaces. Evidence: S02 summary and its passed backend + console verification described there.
- [x] **Runtime and simulation parity delivered.** S03 proved replay uses the same calibrated/degraded/rollout-disabled semantics and route-decision vocabulary as live runtime for the same tenant traffic class. Evidence: S03 summary/UAT and the later S05 close-out backend proof in `tests/test_governance_api.py -k "simulation and calibrated" -x`.
- [x] **Existing operator surfaces expose calibration state without product sprawl.** S04 extended existing request-detail and Observability surfaces so operators can inspect calibrated-vs-heuristic/degraded routing state and contributing evidence while keeping the selected persisted request authoritative. Evidence: S04 summary/UAT and passing focused Observability tests carried forward into S05 close-out verification.
- [x] **Integrated end-to-end proof path delivered and remains bounded.** S05 added `docs/m006-integrated-proof.md` as a pointer-only close-out path, linked it from README and architecture docs, and tightened focused backend/console seams to prove public headers → `X-Request-ID` → usage ledger correlation → replay parity → selected-request-first Observability. Evidence: S05 summary/UAT, mechanical doc checks, `tests/test_response_headers.py -x`, `tests/test_governance_api.py -k "simulation and calibrated" -x`, and the focused console test run.
- [x] **Milestone anti-drift scope held.** Across S01-S05, the delivered work stayed within existing runtime, admin, and Observability seams: no new public API family, no analytics dashboard/routing studio, no hosted-authority expansion, and no raw prompt/response persistence widening. Evidence: S05 summary/UAT, requirement R049 validation in slice close-out, pointer-only proof composition, and explicit out-of-scope constraints preserved in `.gsd/REQUIREMENTS.md`.

## Slice Delivery Audit
| Slice | Planned deliverable | Delivered evidence | Verdict |
|---|---|---|---|
| S01 | A routed request shows calibrated-vs-heuristic mode and explicit additive score breakdown in runtime evidence. | S01 summary documents the shared calibrated scoring contract, propagated route metadata through runtime headers and ledger rows, and the bounded `calibrated_routing_enabled` rollout valve. UAT covers calibrated token-complexity routing, denied/fallback-blocked header parity, and rollout-disabled semantics. | pass |
| S02 | Router derives tenant-scoped calibration summaries from existing ledger metadata and reports sufficient/stale/thin states. | S02 summary documents `CalibrationEvidenceSummary`, deterministic aggregation rules, shared simulation vocabulary, and bounded Observability/request-detail rendering. UAT and summary evidence show sufficient/thin/stale/gated/degraded classification without persistence widening. | pass |
| S03 | Policy simulation replay reports the same calibrated/degraded semantics as live runtime for the same tenant traffic class. | S03 summary establishes runtime/replay parity from persisted runtime evidence, including changed-request parity and degraded/disabled semantics. The same parity seam is re-proved in S05 backend close-out verification. | pass |
| S04 | Operators can inspect calibrated-vs-heuristic routing state and contributing evidence in existing request-detail and Observability surfaces. | S04 summary/UAT show selected-request-first request-detail and Observability inspection surfaces with bounded calibration context, matching the shared runtime/replay vocabulary and avoiding a separate analytics surface. | pass |
| S05 | One integrated proof path demonstrates calibrated live routing, replay parity, degraded fallback, operator inspection, and scope discipline end-to-end. | S05 summary/UAT confirm `docs/m006-integrated-proof.md`, README/architecture discoverability links, mechanical integrity checks, backend proof for headers+ledger+replay, and focused console verification that keeps supporting context subordinate. | pass |

## Cross-Slice Integration
- **S01 → S02:** S02 explicitly consumes the stable replay-critical calibrated signal subset and bounded rollout valve introduced in S01. The summary claims align: S01 provides shared vocabulary and persistence/header propagation; S02 builds tenant-scoped evidence summaries from the existing ledger metadata rather than inventing a new contract.
- **S01 + S02 → S03:** S03 depends on both the live-routing score contract and the ledger-derived calibration evidence summary. The delivered parity behavior described in S03 matches those upstream seams and is corroborated again by S05’s `tests/test_governance_api.py -k "simulation and calibrated" -x` close-out proof.
- **S01 + S02 + S03 → S04:** S04’s operator surfaces use the same calibrated/degraded/disabled vocabulary and keep the selected persisted request authoritative, which matches the knowledge guardrails recorded during earlier slices. No mismatch is visible between the upstream runtime/admin seams and the console-facing evidence surfaces.
- **S01-S04 → S05:** S05 stays composition-first and pointer-only, joining the already-shipped seams in the roadmap’s intended order instead of re-specifying them. README and architecture docs link to the integrated proof without duplicating contracts, and the executable seams used in S05 verification line up with the earlier slices’ strongest proof points.
- **Boundary verdict:** Cross-slice produces/consumes relationships are coherent. I did not find a slice whose delivered output contradicted an upstream dependency or required a compensating undocumented seam. The only noted issue is a pre-existing unrelated Ruff duplicate-test-name warning in `tests/test_governance_api.py`, which does not represent an integration mismatch.

## Requirement Coverage
- **R039:** Addressed across S01, S02, S03, and S05. The assembled milestone now proves shared calibrated routing semantics, tenant-scoped ledger-backed evidence, replay parity, and an executable integrated proof path. This validation finds the assembled work sufficient to validate the requirement at milestone close-out rather than leaving it as merely advanced.
- **R045:** Addressed by S02 with support from S01 and S03. Calibration is derived from recent tenant-scoped observed outcomes using existing ledger evidence, with bounded/interpretable classification and no raw payload persistence expansion.
- **R046:** Addressed by S04 with support from S01 and S02. Existing request-detail and Observability surfaces expose whether routing was calibrated or degraded/heuristic and show the influencing evidence without creating a new analytics surface.
- **R047:** Addressed by S01-S04. Degraded, stale, thin, and rollout-disabled states are explicit and deterministic across runtime headers, replay, ledger evidence, and operator surfaces.
- **R048:** Addressed by S03 with support from S01, S02, and S05. Policy simulation replay uses the same calibrated/degraded semantics and route vocabulary as runtime, and the final close-out backend proof reasserts that parity.
- **R049:** Addressed by all slices and explicitly validated in S05. The milestone improved routing quality while preserving anti-sprawl scope boundaries.

All active M006 requirements are addressed by at least one delivered slice. Based on the assembled evidence, R039, R045, R046, R047, R048, and R049 should now be considered validated at milestone completion time; no active requirement remains uncovered.

## Verification Class Compliance
### Contract
Status: **pass**

Focused backend tests exist and were run for the critical contract seams: calibrated route composition, degraded fallback semantics, typed evidence propagation, rollout-disabled behavior, and header/ledger parity. Evidence is strongest in S01’s router/header/governance tests and S05’s final `tests/test_response_headers.py -x` plus `tests/test_governance_api.py -k "simulation and calibrated" -x` reruns.

### Integration
Status: **pass**

The assembled milestone provides evidence that live runtime routing, policy simulation replay, usage-ledger persistence, and Observability/request-detail surfaces agree on calibrated versus degraded/disabled behavior. The proof path is explicit: public request headers → `X-Request-ID` → usage-ledger row → replay parity → selected-request-first operator inspection. S03 and S05 provide the clearest integration proof.

### Operational
Status: **pass**

Operationally, operators can tell when calibrated routing is active, thin, stale, disabled, or degraded, and they have a bounded tenant-scoped rollout valve. Evidence exists in S01 (policy field + runtime enforcement), S02 (calibration evidence summary states), S04 (operator surfaces), and S05 (close-out console verification). There is no deployment-level production rollout proof here, but the planned operational class as written was about operator-visible state and safe control, and that evidence is present.

### UAT
Status: **pass**

Slice UATs cumulatively cover the reviewer journey the roadmap asked for: trace a calibrated request, inspect its persisted evidence, compare it with replay behavior, verify degraded/disabled semantics, and follow one integrated proof path without black-box or analytics drift. S05’s UAT is the final assembled walkthrough and matches the roadmap’s milestone-level UAT intent.


## Verdict Rationale
Pass. The milestone roadmap’s slice claims are all substantiated by their summaries and UATs, the cross-slice boundaries line up, every active M006 requirement is covered, and each planned verification class has concrete evidence. The assembled work is stronger than a partial close-out: it includes shared calibrated runtime/replay semantics, bounded tenant-scoped calibration evidence, replay parity, operator inspection in existing surfaces, and a pointer-only integrated proof that preserves scope discipline. The only loose end surfaced during validation is a pre-existing unrelated duplicate-test-name Ruff warning in `tests/test_governance_api.py`, which does not undermine milestone integrity or the calibrated-routing proof.
