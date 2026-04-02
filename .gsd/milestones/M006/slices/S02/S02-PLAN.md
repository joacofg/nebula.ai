# S02: Ledger-backed calibration evidence

**Goal:** Derive a bounded tenant-scoped calibration evidence summary from existing usage-ledger metadata, classify when calibration evidence is sufficient, stale, or thin without widening persistence, and expose that shared contract to replay and operator surfaces so later parity and inspection slices build on one vocabulary.
**Demo:** After this: After this: the router can derive tenant-scoped calibration summaries from existing ledger metadata and report when evidence is sufficient, stale, or thin.

## Tasks
- [x] **T01: Added tenant-scoped calibration evidence summaries backed by existing ledger metadata and verified sufficient, thin, stale, gated, and degraded classification rules.** — Add the typed calibration-evidence summary models and deterministic ledger aggregation rules that S02 needs before simulation or UI wiring can proceed.

Steps:
1. Extend `src/nebula/models/governance.py` with a bounded tenant-scoped calibration summary contract that can express evidence state, recency, eligibility scope, gated/disabled counts, degraded counts, and operator-readable reason fields without widening persistence.
2. Implement the summary derivation seam in `src/nebula/services/governance_store.py` or a narrowly focused companion service, using only existing `UsageLedgerRecord` metadata and explicitly excluding override/policy-forced traffic from calibration sufficiency math while keeping `calibrated_routing_disabled` traffic visible as operator-controlled gating.
3. Add focused backend tests in `tests/test_service_flows.py` that prove sufficient, thin, and stale classification, plus the guardrails that override traffic does not poison the summary and gated rows are reported distinctly from accidental missing evidence.
4. Keep the contract bounded and deterministic so S03 and S04 can reuse it directly; do not add raw payload capture, new ledger columns, or analytics-style aggregate sprawl.
  - Estimate: 1h
  - Files: src/nebula/models/governance.py, src/nebula/services/governance_store.py, tests/test_service_flows.py
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x
- [x] **T02: Added shared calibration evidence summaries to admin policy simulation responses and aligned backend/console typing around the replay-window contract.** — Reuse the new summary contract in the replay path so policy simulation describes calibration evidence with the same ledger-backed semantics as runtime-facing admin data.

Steps:
1. Extend `src/nebula/services/policy_simulation_service.py` and `src/nebula/api/routes/admin.py` so simulation responses include or reference the shared calibration summary/evidence state for the replay window instead of inventing separate replay-only logic.
2. Mirror the backend contract in `console/src/lib/admin-api.ts` so the console can consume the same summary shape without ad hoc typing.
3. Add focused backend API coverage in `tests/test_governance_api.py` and service-level coverage in `tests/test_service_flows.py` proving simulation reports the same sufficient/thin/stale semantics, preserves oldest-first replay determinism, and surfaces rollout-disabled calibration evidence distinctly from missing-data degradation.
4. Keep the admin surface narrow: extend existing simulation/admin payloads only as needed, and avoid creating a broad new API family or analytics endpoint unless the shared contract cannot fit the current seams.
  - Estimate: 1h
  - Files: src/nebula/services/policy_simulation_service.py, src/nebula/api/routes/admin.py, console/src/lib/admin-api.ts, tests/test_service_flows.py, tests/test_governance_api.py
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x
- [ ] **T03: Render bounded calibration evidence in Observability and request detail** — Expose the new summary to operators through existing console surfaces without turning them into analytics dashboards.

Steps:
1. Update `console/src/components/ledger/ledger-request-detail.tsx` to render a compact calibration-evidence block that explains sufficient, stale, thin, or rollout-disabled state in request-adjacent operator language while preserving the per-request ledger story as primary.
2. Update `console/src/app/(console)/observability/page.tsx` to show tenant-scoped calibration evidence as bounded supporting context alongside persisted ledger evidence and recommendations, not as a separate analytics destination.
3. Add focused Vitest coverage in `console/src/components/ledger/ledger-request-detail.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` for sufficient/stale/thin/disabled messaging, graceful handling when summaries are absent, and the guardrail that Observability remains the persisted explanation surface rather than a replacement for ledger proof.
4. Keep copy derived from runtime/admin truth: calibration evidence should explain ledger-backed state, gated rollout, and replay readiness without inventing new runtime entities or promising raw-outcome analytics.
  - Estimate: 1h
  - Files: console/src/lib/admin-api.ts, console/src/components/ledger/ledger-request-detail.tsx, console/src/components/ledger/ledger-request-detail.test.tsx, console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/observability-page.test.tsx
  - Verify: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx
