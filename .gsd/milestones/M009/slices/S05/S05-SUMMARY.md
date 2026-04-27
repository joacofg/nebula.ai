---
id: S05
parent: M009
milestone: M009
provides:
  - A final integrated proof path for outcome-grounded routing quality that future milestone readers can follow from public request to persisted evidence to replay parity to request-first operator inspection.
  - Focused anti-drift coverage ensuring happy-path and degraded-path routing reviews stay aligned across runtime, admin replay, documentation, and console surfaces without product sprawl.
requires:
  []
affects:
  - milestone-closeout
key_files:
  - docs/m009-integrated-proof.md
  - docs/route-decision-vocabulary.md
  - docs/architecture.md
  - tests/test_response_headers.py
  - tests/test_governance_api.py
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - .gsd/PROJECT.md
key_decisions:
  - Kept M009 close-out proof pointer-first and referential, with shared outcome-grounded vocabulary defined once in route-decision docs rather than duplicated in the integrated proof.
  - Asserted replay parity at the route semantics layer while allowing policy outcome summaries to be recomputed from the replay window, matching the shipped simulation contract.
  - Kept degraded request-first authority proof in deterministic request-detail tests instead of widening into a more brittle integration-only console flow.
patterns_established:
  - Integrated proof docs should link existing request, ledger, simulation, and request-detail seams rather than restating contracts inline.
  - Replay verification should bind persisted route signals and route-level parity directly to the selected request under unchanged policy while staying explicit about degraded gaps.
  - Request-first observability proof belongs where the selected request row and supporting calibration context render together, keeping anti-drift coverage stable.
observability_surfaces:
  - Existing request-first operator surfaces remain authoritative: live `X-Nebula-*` response headers, persisted usage-ledger route signals, admin simulation parity output, and selected request detail in Observability.
drill_down_paths:
  - .gsd/milestones/M009/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M009/slices/S05/tasks/T02-SUMMARY.md
  - .gsd/milestones/M009/slices/S05/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-27T21:48:43.448Z
blocker_discovered: false
---

# S05: S05

**Closed M009 with a pointer-first integrated proof, backend parity tests, and request-first console coverage that together prove the happy and degraded outcome-grounded routing review paths without widening Nebula’s product boundary.**

## What Happened

S05 completed the final assembly for M009 by tightening documentation, backend proof seams, and console proof seams around the already-shipped runtime/admin/operator surfaces. T01 added `docs/m009-integrated-proof.md` in the same pointer-first style as prior milestone close-out docs and updated `docs/route-decision-vocabulary.md` plus `docs/architecture.md` so outcome-grounded routing terms and the integrated proof path are discoverable without duplicating contracts inline. T02 hardened the backend proof chain on existing tests instead of adding a new harness: the selected happy-path request now proves the chain from live `POST /v1/chat/completions` response headers into persisted `route_signals.outcome_evidence` and unchanged-policy replay parity, while degraded replay tests explicitly preserve honesty when persisted route signals are incomplete by returning missing parity fields rather than inventing replay-only metadata. T03 hardened the request-first console proof for degraded inspection by keeping the selected request row authoritative in deterministic request-detail coverage and leaving broader Observability framing intact, avoiding a new dashboard or brittle browser-only flow. Together these tasks closed the milestone exactly at its intended boundary: one review path from public request to persisted ledger evidence to replay parity to request-first operator inspection for both a happy path and a degraded path, with anti-drift coverage locked into docs and focused tests rather than new product surface area.

## Verification

Fresh slice-level verification was rerun after the task changes. Backend verification passed with `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or policy_denied"` (3 passed), `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"` (1 passed), and `./.venv/bin/pytest tests/test_governance_api.py -k "returns_summary_and_preserves_saved_policy or supports_unchanged_and_empty_windows"` (2 passed). Console verification passed with `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'` (16 passed), `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'` (1 passed), and `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'` (4 passed). Requirement R078 was also advanced to validated because the integrated proof and focused tests demonstrate the anti-sprawl boundary in docs and verification evidence without adding a new API, analytics workflow, or hosted-authoritative control path.

## Requirements Advanced

None.

## Requirements Validated

- R078 — S05 validated the anti-sprawl guardrail through the pointer-first integrated proof plus passing backend and console verification on existing runtime, ledger, replay, and request-detail seams, with no new API surface, analytics dashboard, or hosted-authoritative behavior introduced.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

Two execution deviations were retained from the task work but did not change the slice outcome. T01’s planned verification command used `python`, but the local environment exposes `python3.12`, so the equivalent script was rerun with `python3.12`. T02’s plan-provided `pytest -k "policy_simulation and (outcome_grounded or degraded or parity or usage_ledger)"` selector matched zero tests because of current test naming and case-sensitive selection, so the touched governance simulation tests were verified by direct test-name selection instead. T03 also briefly attempted a broader Observability-page degraded proof, but that approach proved brittle and the authoritative degraded assertion was kept in the deterministic request-detail suite instead.

## Known Limitations

S05 proves the integrated review path through focused documentation and automated tests rather than a manually executed live browser walkthrough. The milestone now has strong anti-drift coverage for the shipped seams, but any future semantic change to route vocabulary, replay parity expectations, or request-detail evidence hierarchy still requires those focused tests and the integrated proof document to be updated together.

## Follow-ups

None.

## Files Created/Modified

- `docs/m009-integrated-proof.md` — Added the final M009 integrated proof walkthrough for happy and degraded request-first review paths.
- `docs/route-decision-vocabulary.md` — Linked and clarified shared outcome-grounded route vocabulary terms used by the close-out proof.
- `docs/architecture.md` — Added discoverability link to the M009 integrated proof from the canonical architecture guide.
- `tests/test_response_headers.py` — Strengthened happy-path header-to-ledger outcome-grounded proof assertions.
- `tests/test_governance_api.py` — Hardened unchanged-policy replay parity and degraded missing-route-signal honesty coverage.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Added deterministic degraded request-first authority assertions in the request-detail seam.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Kept Observability proof aligned with request-first degraded inspection without widening the UI flow.
- `.gsd/PROJECT.md` — Refreshed project state to mark M009 and S05 complete.
