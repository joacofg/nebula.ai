# S02: Tighten supporting evidence and preview contracts

**Goal:** Tighten the supporting data and UI contracts behind Observability and policy preview so later M007 investigation and comparison flows can rely on explicit, bounded operator evidence without introducing dashboard or analytics drift.
**Demo:** After this: After this: the supporting data and UI seams needed for clearer page roles exist without introducing a new dashboard or routing-research scope.

## Tasks
- [x] **T01: Aligned admin policy options with cache tuning controls and tightened bounded simulation contract coverage.** — Update the admin policy contract so runtime-enforced fields truthfully include the semantic-cache tuning controls already edited in the console, then tighten backend/shared types and focused tests around bounded simulation comparison output. Use the existing admin route/model seams; do not widen the contract into analytics payloads or unbounded samples.

Steps:
1. Confirm and align `PolicyOptionsResponse` / `/v1/admin/policy/options` so runtime-enforced fields include the semantic-cache similarity-threshold and max-entry-age controls when they are live policy inputs.
2. Keep `PolicySimulationResponse` bounded and comparison-first by strengthening any shared type/test expectations needed for baseline-vs-simulated route/status/policy/cost evidence without adding dashboard-style aggregates.
3. Add or tighten focused pytest coverage around policy options and simulation so contract drift is caught at the admin boundary before console work lands.
  - Estimate: 1h
  - Files: src/nebula/api/routes/admin.py, src/nebula/models/governance.py, src/nebula/services/policy_simulation_service.py, tests/test_governance_api.py, tests/test_service_flows.py, console/src/lib/admin-api.ts
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x && ./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x
- [ ] **T02: Tighten policy preview and Observability supporting seams** — Consume the aligned contracts in the console by making policy preview and Observability more explicit about the operator’s next comparison or follow-up action while preserving the S01 authority hierarchy. Extend existing components locally; do not add a new surface, summary dashboard, or alternate request authority path.

Steps:
1. Refine `PolicyForm` / policy page rendering so preview reads as baseline-vs-simulated decision evidence with explicit bounded samples, save-explicit semantics, and cache-control/runtime wording grounded in the aligned policy-options contract.
2. Refine Observability supporting-context seams so recommendation, calibration, cache, and dependency cards point more clearly back to the selected request investigation while keeping `LedgerRequestDetail` authoritative and avoiding tenant-summary takeover.
3. Tighten focused Vitest coverage with DOM-order and scoped assertions (`within(...)`) for duplicate labels, comparison-first preview semantics, and negative checks against dashboard/routing-studio/analytics drift.
  - Estimate: 1h30m
  - Files: console/src/app/(console)/policy/page.tsx, console/src/components/policy/policy-form.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx, console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/components/ledger/ledger-request-detail.tsx
  - Verify: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
