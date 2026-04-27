---
id: S02
parent: M009
milestone: M009
provides:
  - Live outcome-grounded route decisions that can change because of recent bounded tenant evidence, plus persisted request-level route factors that record exactly why the runtime decision happened.
requires:
  []
affects:
  - S03
  - S04
  - S05
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - tests/test_router_signals.py
  - tests/test_service_flows.py
  - tests/test_chat_completions.py
  - tests/test_response_headers.py
  - tests/test_governance_api.py
key_decisions:
  - Kept `GovernanceStore.summarize_calibration_evidence()` as the sole source of live outcome-evidence classification and passed its summary into runtime routing instead of re-classifying evidence in the router.
  - Made the request-first observability contract additive by preserving existing route-mode and score fields while appending `outcome_evidence` state and additive score components to `route_signals`.
  - Verified end-to-end parity by asserting agreement between live response headers, `policy_outcome`, and persisted usage-ledger `route_signals` rather than introducing new helper abstractions or public API surfaces.
patterns_established:
  - Use a single typed evidence-summary contract across live routing, persistence, and future replay work to prevent semantic drift between runtime and admin flows.
  - Extend request-first diagnostics additively so ledger rows and headers can explain richer routing behavior without widening into a new analytics surface.
  - Treat policy-denied and governance-minimized paths as first-class evidence states that preserve truthful explanatory metadata without fabricating route-score factors.
observability_surfaces:
  - Persisted `UsageLedgerRecord.route_signals` now carries `outcome_evidence` state and additive score components for live requests.
  - Existing response headers and `policy_outcome` remain the request-first diagnostic seam and now expose outcome-grounded routing context.
  - Governance usage-ledger reads and related backend tests remain the authoritative place to inspect whether runtime and persistence stayed in sync.
drill_down_paths:
  - .gsd/milestones/M009/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M009/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-27T20:57:35.172Z
blocker_discovered: false
---

# S02: S02

**Live chat routing now consumes bounded tenant-scoped outcome evidence at decision time and persists the exact outcome-grounded route factors on the correlated usage-ledger row.**

## What Happened

S02 closes the live runtime seam introduced in S01 by wiring `GovernanceStore.summarize_calibration_evidence()` into policy evaluation and router scoring without introducing a second evidence classifier. `PolicyService.evaluate()` now fetches tenant-scoped outcome evidence immediately before route selection, passes the summary into the router, and preserves existing authoritative controls: explicit model overrides, forced routing, calibrated-routing disablement, hard-budget downgrade or deny behavior, and governance-minimization semantics still win when present. The router contract was extended additively so existing route diagnostics remain stable while `route_signals` now records outcome-evidence state plus additive score components such as `outcome_bonus` and `evidence_penalty`. End-to-end request-path tests then proved a real `POST /v1/chat/completions` call can route differently because of recent tenant evidence, and that response headers, `policy_outcome`, and the correlated usage-ledger row all agree on the same grounded factors. The slice also proved honest degraded behavior: policy-denied or minimized paths preserve truthful evidence-state metadata without fabricating route factors, so downstream replay and operator slices can reuse the persisted seam rather than rebuilding it.

## Verification

Slice verification reran every planned backend proof for the live-routing seam. `./.venv/bin/pytest tests/test_router_signals.py -k "outcome or evidence or route"` passed (10 passed) and confirmed the enriched additive `route_signals` payload and router scoring behavior. `./.venv/bin/pytest tests/test_service_flows.py -k "outcome_grounded or policy_service_live_evidence or hard_budget"` passed (2 passed) and confirmed live policy evidence lookup, score impact, and preserved hard-budget guardrails. `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or route"` passed (3 passed) and proved live request routing can flip because of tenant evidence while persisting matching ledger factors. The plan-listed header verification command `./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals"` deselected all tests because pytest `-k` matching is case-sensitive; the intended lowercase-equivalent command `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"` then passed (1 passed) and verified header-to-ledger parity. `./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or outcome_grounded or policy_simulation"` passed (11 passed, 1 pre-existing FastAPI deprecation warning) and confirmed request-first inspection across usage-ledger reads, degraded or gated routes, and policy simulation expectations updated for the additive contract.

## Requirements Advanced

- R073 — Closed the live routing seam so tenant-scoped outcome evidence now influences real runtime route selection through the existing policy/router path.
- R075 — Persisted the exact outcome-grounded route factors, evidence state, and additive score components on the correlated usage-ledger row for live requests.

## Requirements Validated

- R073 — Backend routing and request-path tests proved recent tenant outcome evidence can materially change a live POST /v1/chat/completions route while preserving guardrails.
- R075 — Header, policy_outcome, and usage-ledger assertions proved the actual live route factors are recorded faithfully on the same request row.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

The planned response-header verification command used a mixed-case pytest `-k` selector (`Route-Mode`) that matched no lowercase-named tests and exited with code 5. Verification was completed with the lowercase-equivalent selector so the intended scope still ran. `tests/test_governance_api.py` also needed small expectation repairs beyond the original request-path focus because an existing malformed embedded scenario and older `policy_outcome` assertions no longer matched the additive outcome-evidence contract introduced in T01.

## Known Limitations

S02 does not yet prove replay parity for the same outcome-grounded semantics; S03 still needs to ensure admin policy simulation reuses the same runtime scoring meaning and degrades honestly when evidence is incomplete. Operator-surface rendering of grounded/thin/stale/degraded request evidence is also still pending in S04. The response-header task-plan selector remains fragile because pytest `-k` matching is case-sensitive, and the governance suite still emits a pre-existing FastAPI deprecation warning.

## Follow-ups

Update the response-header verification command in future planning artifacts to use lowercase pytest selectors so slice-level verification does not depend on manual correction. Reuse the persisted `route_signals.outcome_evidence` and score-component contract as the canonical live seam in S03 replay work and S04 request-detail/operator rendering. Consider separately cleaning up the pre-existing FastAPI `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning to keep future verification output quieter.

## Files Created/Modified

- `src/nebula/services/router_service.py` — Extended router scoring and route-signals vocabulary to carry outcome-evidence state and additive score components.
- `src/nebula/services/policy_service.py` — Fetched tenant outcome evidence during live evaluation and passed the summary into routing while preserving existing override and budget guardrails.
- `tests/test_router_signals.py` — Added router-level assertions for additive outcome-grounded score factors and persisted route-signals structure.
- `tests/test_service_flows.py` — Proved live policy evidence lookup, score impact, and preserved hard-budget behavior.
- `tests/test_chat_completions.py` — Added end-to-end request-path tests showing live routing can flip because of sufficient tenant evidence and persist matching ledger factors.
- `tests/test_response_headers.py` — Added focused header-to-ledger parity proof for outcome-grounded routing diagnostics.
- `tests/test_governance_api.py` — Updated governance and usage-ledger expectations to match the additive outcome-evidence contract and repaired malformed scenario coverage.
