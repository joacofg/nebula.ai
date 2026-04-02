# S01: Calibrated routing core

**Goal:** Replace the heuristic-first routing center with an explicit calibrated routing contract that stays interpretable, preserves runtime/replay parity, exposes calibrated-versus-heuristic state plus additive score breakdown in runtime evidence, and introduces only the bounded tenant-scoped rollout valve needed for safe adoption.
**Demo:** After this: After this: a routed request can show calibrated-versus-heuristic routing mode and an explicit additive score breakdown in runtime evidence.

## Tasks
- [x] **T01: Replaced duplicated router branches with a shared calibrated scoring contract and locked the additive route-signal vocabulary in tests and docs.** — Move `RouterService` from duplicated heuristic branches to a shared calibrated scoring helper used by both live routing and replay. Keep the replay-critical signal subset stable (`token_count`, `keyword_match`, `complexity_tier`) while adding explicit routing mode markers and additive breakdown fields that later slices can consume without guessing. Update the route vocabulary doc and focused router tests in the same task so the contract is nailed down before policy or persistence work builds on it.

Steps:
1. Extract shared router helpers in `src/nebula/services/router_service.py` that derive calibrated score components, route mode markers, reason codes, and target selection for both live and replay paths.
2. Expand the `signals` payload additively so it includes calibrated-versus-heuristic/degraded state plus named score components, while preserving existing keys consumed by `PolicySimulationService` and current ledger/detail surfaces.
3. Update `tests/test_router_signals.py` to assert the new score breakdown, route reason vocabulary, replay compatibility, and degraded/heuristic fallback branches; update `docs/route-decision-vocabulary.md` to match the shipped contract exactly.
  - Estimate: 90m
  - Files: src/nebula/services/router_service.py, tests/test_router_signals.py, docs/route-decision-vocabulary.md
  - Verify: ./.venv/bin/pytest tests/test_router_signals.py -x
- [ ] **T02: Wire calibrated routing through policy resolution and runtime evidence** — Make policy evaluation and runtime propagation consume the new router contract without drifting. Preserve hard-budget downgrade/deny behavior over calibrated route decisions, keep replay reconstruction compatible with the stable subset of persisted signals, and prove that request headers plus usage-ledger rows carry the same calibrated story for a real request.

Steps:
1. Update `src/nebula/services/policy_service.py` and any small supporting code in `src/nebula/services/chat_service.py` or `src/nebula/api/routes/chat.py` so calibrated route reasons, scores, and signal payloads propagate unchanged through policy resolution, downgrade/fallback paths, headers, and ledger writes.
2. Extend focused backend tests in `tests/test_governance_runtime_hardening.py`, `tests/test_service_flows.py`, and `tests/test_response_headers.py` so they assert runtime/replay compatibility, hard-budget interaction, and outward header/ledger evidence for calibrated versus degraded routing.
3. Run Python diagnostics after edits and keep any contract-sensitive expectations aligned across runtime, replay, and persisted metadata.
  - Estimate: 90m
  - Files: src/nebula/services/policy_service.py, src/nebula/services/chat_service.py, src/nebula/api/routes/chat.py, tests/test_governance_runtime_hardening.py, tests/test_service_flows.py, tests/test_response_headers.py
  - Verify: ./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "simulation or runtime_policy" tests/test_response_headers.py -x
- [ ] **T03: Add the bounded tenant calibrated-routing rollout control** — Ship the small tenant-scoped control from D032/D033 as a rollout and safety valve, but keep it narrow: an explicit calibrated-routing enable/disable control, not a tuning surface. Persist it through governance models and admin APIs, keep simulation/runtime semantics aligned, and prove the new field works without widening console scope in this slice.

Steps:
1. Add a single bounded calibrated-routing control field to `TenantPolicy` plus its persistence path in `src/nebula/db/models.py`, `src/nebula/services/governance_store.py`, and a new Alembic revision under `migrations/versions/`.
2. Surface the field through admin policy options and policy read/write APIs in `src/nebula/api/routes/admin.py`, then update focused governance tests to prove runtime and simulation both respect the same on/off semantics.
3. Update the policy form/admin client types and focused console tests only as needed to keep the existing tenant policy surface truthful and writable, without adding new calibration analytics UI.
  - Estimate: 2h
  - Files: src/nebula/models/governance.py, src/nebula/db/models.py, src/nebula/services/governance_store.py, src/nebula/api/routes/admin.py, migrations/versions/, tests/test_governance_api.py, console/src/lib/admin-api.ts, console/src/components/policy/policy-form.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx
  - Verify: ./.venv/bin/alembic upgrade head && ./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation or route_reason" -x && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
