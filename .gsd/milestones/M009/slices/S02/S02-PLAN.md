# S02: Live outcome-grounded routing

**Goal:** Wire bounded tenant-scoped outcome evidence into live chat routing so runtime decisions can change because of recent evidence and the same request persists the exact outcome-grounded factors used on its ledger row.
**Demo:** After this: a real `POST /v1/chat/completions` request can route differently because of recent tenant-scoped outcome evidence, and the correlated persisted ledger row records the actual route factors used.

## Must-Haves

- Live `POST /v1/chat/completions` routing consumes `GovernanceStore.summarize_calibration_evidence()` through the existing policy/router seam and can choose a different target because of bounded recent tenant evidence.
- Persisted `route_signals` on the correlated usage-ledger row record the typed outcome-grounded factors, evidence state, and additive score components that actually influenced the live decision.
- Existing override, gating, and governance-minimization paths remain authoritative: explicit model choices, forced routing, calibrated-routing disablement, hard-budget downgrade/deny, and strict metadata suppression still behave honestly.
- Backend tests prove both a grounded happy path and a degraded/thin path without introducing a second evidence classifier or widening public APIs.

## Proof Level

- This slice proves: integration

## Integration Closure

This slice closes the runtime composition seam between `GovernanceStore.summarize_calibration_evidence()`, `PolicyService.evaluate()`, `RouterService.choose_target_with_reason()`, and `ChatService` ledger persistence for live requests. After S02, S03 still needs replay parity on the same persisted factors and S04 still needs request-first operator rendering of the grounded/thin/stale/degraded story.

## Verification

- Live request diagnostics remain request-first through `route_signals` persisted on `UsageLedgerRecord` and surfaced via existing headers/ledger reads. Failures or degraded routing should remain inspectable via `route_reason`, `route_mode`, evidence-state fields, score components, and governance suppression markers instead of requiring new dashboards.

## Tasks

- [x] **T01: Extend router and policy seams for live outcome-grounded scoring** `est:90m`
  Add the shared runtime contract that lets live routing consume the S01 calibration summary without re-classifying evidence. Keep the change additive: extend the router breakdown/signals vocabulary with bounded outcome-grounded factors and teach `PolicyService.evaluate()` to fetch tenant-scoped evidence immediately before live route choice, while preserving explicit overrides, calibrated-routing disablement, hard-budget guardrails, and serializable parity-friendly signals. Record installed skills in frontmatter as `verify-before-complete` and `test` because executors must prove the new contract with real backend assertions before claiming the task is done.
  - Files: `src/nebula/services/router_service.py`, `src/nebula/services/policy_service.py`, `src/nebula/models/governance.py`, `tests/test_router_signals.py`, `tests/test_service_flows.py`
  - Verify: ./.venv/bin/pytest tests/test_router_signals.py -k "outcome or evidence or route" && ./.venv/bin/pytest tests/test_service_flows.py -k "outcome_grounded or policy_service_live_evidence or hard_budget"

- [ ] **T02: Prove request-to-ledger persistence for outcome-grounded live routing** `est:90m`
  Close the slice on the real request path by proving a live `/v1/chat/completions` call can route differently because of seeded tenant evidence and that the correlated usage-ledger row records the actual outcome-grounded route factors used. Cover both happy-path persistence and honest degraded/minimized behavior so downstream replay and operator slices can trust the stored seam. Record installed skills in frontmatter as `verify-before-complete` and `test` because this task must finish with executable evidence from tracked backend tests.
  - Files: `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_governance_api.py`, `tests/support.py`
  - Verify: ./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or route" && ./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals" && ./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or outcome_grounded or policy_simulation"

## Files Likely Touched

- src/nebula/services/router_service.py
- src/nebula/services/policy_service.py
- src/nebula/models/governance.py
- tests/test_router_signals.py
- tests/test_service_flows.py
- tests/test_chat_completions.py
- tests/test_response_headers.py
- tests/test_governance_api.py
- tests/support.py
