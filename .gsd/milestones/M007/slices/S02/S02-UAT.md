# S02: Tighten supporting evidence and preview contracts — UAT

**Milestone:** M007
**Written:** 2026-04-03T02:21:31.245Z

# S02: Tighten supporting evidence and preview contracts — UAT

**Milestone:** M007
**Written:** 2026-04-01

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice tightened bounded admin contracts and focused console wording/test seams rather than introducing a new runtime workflow. The strongest proof is the assembled backend and Vitest coverage against the exact supporting seams S03 and S04 depend on.

## Preconditions

- Python virtualenv dependencies are installed in `./.venv`.
- Console test dependencies are installed under `console/node_modules`.
- Worktree contains the S02 backend and console changes.

## Smoke Test

Run the full slice verification set and confirm all targeted suites pass:

1. `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x`
2. `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x`
3. `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
4. **Expected:** All tests pass, proving the bounded admin contract and request-first / comparison-first console seams hold together in the assembled slice.

## Test Cases

### 1. Admin policy options expose live cache tuning controls

1. Run `./.venv/bin/pytest tests/test_governance_api.py -k policy_options -x`.
2. Inspect the passing assertions for `/v1/admin/policy/options`.
3. **Expected:** The response classifies `semantic_cache_similarity_threshold` and `semantic_cache_max_entry_age_hours` as runtime-enforced policy inputs rather than omitting them or treating them as documentation-only controls.

### 2. Policy simulation stays comparison-first and bounded

1. Run `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x`.
2. Run `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x`.
3. **Expected:** Simulation output remains bounded to baseline-versus-simulated route/status/policy/cost evidence with capped changed-request samples and valid non-negative cost fields; no analytics-style unbounded samples or unrelated aggregates appear.

### 3. Policy preview reads as baseline-versus-draft decision evidence

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Review the assertions around preview copy and save behavior.
3. **Expected:** The policy UI describes preview as comparison evidence over recent persisted requests, keeps save as a separate explicit action, and rejects dashboard, routing-studio, or analytics wording.

### 4. Observability supporting cards remain subordinate to the selected request

1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`.
2. Review the DOM-order and scoped `within(...)` assertions.
3. **Expected:** The selected request investigation and ledger request detail remain authoritative, while recommendation, calibration, cache, and dependency cards are framed as supporting context for follow-up interpretation rather than parallel authorities.

## Edge Cases

### Inverted simulation time window is rejected cleanly

1. Run `./.venv/bin/pytest tests/test_governance_api.py -k inverted_time_windows -x`.
2. **Expected:** The admin simulation endpoint rejects inverted windows instead of producing ambiguous replay output.

### Duplicate labels across supporting cards do not break tests

1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/observability-page.test.tsx`.
2. **Expected:** Scoped `within(...)` assertions pass even when similar labels appear in multiple bounded cards, proving the page can use repeated support labels without losing hierarchy guarantees.

## Failure Signals

- `policy_options` tests fail because semantic-cache controls disappear from the admin options payload or change classification.
- `simulation` tests fail because replay output widens into new aggregate payloads, uncapped samples, invalid cost fields, or stale route/policy expectations.
- Policy-form/page tests fail because preview copy starts reading like an analytics dashboard, routing studio, or auto-save workflow.
- Observability/page/request-detail tests fail because supporting cards appear as equal or primary evidence, or because authoritative request-detail wording regresses.

## Requirements Proved By This UAT

- R052 — Policy preview remains a clear save / don’t-save comparison seam rather than a blended analytics/editor surface.
- R053 — Supporting context stays subordinate to the primary evidence on each page.
- R054 — Next operator action is clearer from bounded preview and request-first supporting-card structure.
- R055 — The slice preserved scope discipline by tightening seams without creating a dashboard, routing studio, or parallel workflow.

## Not Proven By This UAT

- Full end-to-end Observability page-flow redesign from S03.
- Full comparison-and-decision policy workflow from S04.
- Live browser ergonomics beyond what the focused backend and Vitest seams prove.

## Notes for Tester

This slice is intentionally seam-tightening work. Treat unexpected new aggregates, dashboard summaries, routing-studio language, or any copy that promotes supporting cards to equal authority as regressions even if the UI still renders.
