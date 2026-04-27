# M009/S03 — Research

**Date:** 2026-04-27

## Summary

S03 is a targeted backend+policy-console parity slice centered on **R074**: the admin replay path must reuse the same outcome-grounded semantics as live runtime for the same tenant traffic class, and must degrade honestly when replay inputs are incomplete. The core implementation seam already exists: `PolicySimulationService.simulate()` replays each persisted ledger row by calling `PolicyService.evaluate()`, and S02 already taught `PolicyService.evaluate()` + `RouterService` how to consume `CalibrationEvidenceSummary` for live requests. The main gap is that replay currently does **not** pass tenant outcome evidence into `PolicyService.evaluate()` at all because `PolicyService.evaluate()` only fetches `summarize_calibration_evidence()` when `replay_context is None`. As written, replay decisions ignore the same outcome bonus / evidence penalty that runtime now applies.

The safest approach is to keep D049/D050 intact: one shared backend contract, bounded additive scoring, no replay-only scoring branch. Concretely, S03 should make `PolicySimulationService` compute the tenant/window `calibration_summary` once per simulation window and pass that same summary into every replayed `PolicyService.evaluate()` call, while preserving existing degraded replay signaling from `ReplayRouteContext` when persisted route signals are incomplete. This keeps runtime/replay semantics aligned without inventing a second classifier or reading tenant evidence separately inside the router.

## Recommendation

Implement S03 by extending `PolicyService.evaluate()` with an **optional explicit replay evidence summary override** and have `PolicySimulationService.simulate()` pass the window-scoped `GovernanceStore.summarize_calibration_evidence(...)` result into each replayed evaluation.

Why this approach:
- It preserves the single authoritative summarization seam from S01/S02 (`GovernanceStore.summarize_calibration_evidence()`), matching MEM056/MEM059.
- It keeps the router contract unchanged at the scoring layer: `RouterService.choose_target_for_replay(..., evidence_summary=...)` already accepts summary input; the missing issue is propagation, not router design.
- It supports honest degraded behavior: replay can still mark `route_mode="degraded"` when persisted `complexity_tier` / `keyword_match` are missing, while also reflecting tenant evidence state through the same `outcome_evidence` and `policy_outcome` vocabulary used by runtime.
- It minimizes surface-area drift: the existing admin API response and console preview already render `changed_requests`, `approximation_notes`, and routing parity details. Most UI work is likely narrow type/test alignment rather than new UI design.

## Implementation Landscape

### Key Files

- `src/nebula/services/policy_simulation_service.py` — Main S03 seam. Replays stored ledger rows by rebuilding a narrow `ChatCompletionRequest`, calling `PolicyService.evaluate()`, collecting changed-request parity fields, and returning `calibration_summary` + `approximation_notes`. Today it computes `calibration_summary` only **after** the replay loop and never injects it into replay evaluation.
- `src/nebula/services/policy_service.py` — Shared runtime/replay evaluation seam. Currently only fetches `summarize_calibration_evidence()` when `replay_context is None`, so replay misses outcome-grounded scoring. Best natural seam is an optional parameter like `evidence_summary_override` or similar, with precedence over the runtime fetch.
- `src/nebula/services/router_service.py` — Already ready for S03. `choose_target_for_replay()` accepts `evidence_summary`; `_build_breakdown()` persists `outcome_bonus`, `evidence_penalty`, and `outcome_evidence.*`; replay degraded mode is already encoded via `route_mode="degraded"`, `replay=True` when replay inputs are incomplete.
- `src/nebula/services/governance_store.py` — Authoritative summary classifier. `summarize_calibration_evidence()` supports `from_timestamp`, `to_timestamp`, and `limit`, returns `scope="tenant_window"` for replay windows, and enforces thin/degraded/stale precedence. Do not duplicate any of this logic in simulation.
- `src/nebula/models/governance.py` — Typed replay/admin payloads. `PolicySimulationResponse` already includes `calibration_summary`; `PolicySimulationChangedRequest` currently carries parity fields for route mode/score but **does not carry simulated baseline route signals or explicit outcome evidence fields**, so any richer changed-request explanation must either be encoded through existing `simulated_policy_outcome` / `simulated_route_mode` / `simulated_route_score` or by extending this model additively.
- `src/nebula/api/routes/admin.py` — Thin route wrapper around `PolicySimulationService.simulate()`. Likely unchanged except for tests.
- `tests/test_service_flows.py` — Best unit/integration seam for simulation service behavior. Already covers no-mutation guarantees, tenant/window scoping, changed request ordering, calibrated-routing-disabled parity, and empty-window handling. Add the first direct proof that replay consumes outcome evidence and degrades honestly when route signals are incomplete.
- `tests/test_governance_api.py` — End-to-end admin API proof. Already contains policy simulation assertions for `calibration_summary`, changed requests, newly denied, and route-mode parity. This is where to prove `POST /v1/admin/tenants/{tenant_id}/policy/simulate` now reflects live outcome-grounded semantics in `simulated_policy_outcome` / simulated score / route changes.
- `tests/test_router_signals.py` — Existing router-level replay assertions already prove `choose_target_for_replay()` can emit `route_mode="degraded"` and apply evidence summary fields. Useful as guardrail; probably no broad change required beyond additive assertions if semantics shift.
- `console/src/lib/admin-api.ts` — Type mirror for admin responses. Drift exists here: `CalibrationEvidenceSummary.state` is typed as `"sufficient" | "thin" | "stale"`, missing `"degraded"` even though backend S01 introduced it. This will matter once S03 makes degraded replay semantics more visible.
- `console/src/components/policy/policy-form.tsx` — Existing request-first simulation preview. It already renders changed-request parity, no-save messaging, and approximation notes. If S03 adds richer replay honesty copy or if parity states become more explicit, this is the UI seam.
- `console/src/components/policy/policy-form.test.tsx` — Existing preview contract tests. Contains parity rendering expectations, including malformed / rollout-disabled cases, and should be updated if backend parity semantics or types expand.

### Build Order

1. **Fix backend propagation first** in `PolicyService.evaluate()` + `PolicySimulationService.simulate()`.
   - Add an explicit evidence-summary override parameter to `PolicyService.evaluate()`.
   - In simulation, compute the window-scoped `calibration_summary` once before replaying rows and pass it into every replay evaluation.
   - This is the slice’s real contract closure; everything else depends on it.
2. **Prove replay scoring parity at service level** in `tests/test_service_flows.py`.
   - Add a focused test where a replayed low-token request flips because the tenant-window summary is `sufficient`, matching the live semantics introduced in S02.
   - Add/extend a degraded replay case showing missing replay signals still produce degraded route mode while preserving outcome evidence metadata/policy outcome honesty.
3. **Prove the public admin API path** in `tests/test_governance_api.py`.
   - Assert `POST /policy/simulate` returns changed-request output whose simulated route/score/policy outcome reflect outcome-grounded semantics, not just prompt heuristics.
   - Preserve the non-mutating contract and bounded changed sample behavior.
4. **Repair console type/test drift last** in `console/src/lib/admin-api.ts` and `console/src/components/policy/policy-form.test.tsx` if needed.
   - At minimum, include `degraded` in `CalibrationEvidenceSummary.state` to match backend reality.
   - Only adjust UI rendering if changed-request parity or approximation messaging becomes more explicit.

### Verification Approach

Backend-first verification:
- `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity)"`
- `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity)"`
- `./.venv/bin/pytest tests/test_router_signals.py -k "replay or outcome_evidence"`

If console types/tests change:
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`

Observable proof the planner should demand:
- a replayed request can change for the **same reason** live runtime now changes (tenant-window outcome evidence)
- `simulated_policy_outcome` includes the same `outcome_evidence=...` vocabulary as runtime
- degraded replay still reports degraded parity when stored route signals are incomplete instead of pretending a fully grounded replay
- no provider execution, no policy writes, and no ledger mutation during simulation remain true

## Constraints

- `GovernanceStore.summarize_calibration_evidence()` is the only allowed evidence classifier; S01/S02 explicitly established this seam and prior memories reinforce not duplicating it.
- Replay is intentionally bounded to persisted request metadata and route signals; raw prompts are unavailable, so `PolicySimulationService` must continue to rely on synthetic prompt reconstruction plus persisted signals.
- `PolicySimulationResponse.approximation_notes` is capped at 3 items in `src/nebula/models/governance.py`; if S03 needs sharper degraded-language, reuse or replace existing notes instead of appending unbounded copy.
- Request-first scope still applies (D051 / R078): do not widen the simulation UI into a dashboard or tenant-summary-first analytics surface.

## Common Pitfalls

- **Passing no evidence summary during replay** — this is the current parity bug. If replay keeps calling `PolicyService.evaluate()` without an override, simulation will stay heuristic-only while runtime is outcome-grounded.
- **Recomputing evidence per row using `before_timestamp`** — tempting, but this would create a different semantic contract than the API’s returned `calibration_summary` window and may introduce drift. The existing response shape suggests one bounded tenant-window summary per preview.
- **Assuming degraded state lives only in `calibration_summary`** — replay also has request-level degradation via `route_mode="degraded"` when persisted complexity hints are missing. S03 needs both summary-level and request-level honesty.
- **Missing frontend type drift** — `console/src/lib/admin-api.ts` still omits `degraded` from `CalibrationEvidenceSummary.state`; once replay degraded semantics are surfaced more often, TS/tests can drift even if backend passes.

## Open Risks

- There is an unresolved semantic choice the executor should check while implementing: whether replay should use **one simulation-window summary for all rows** or a per-row historical summary bounded by each record timestamp. The current API shape, S01 summary contract, and existing implementation all point to the former, but tests should lock this in explicitly so future refactors do not “improve” it into a different replay story.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| FastAPI | `wshobson/agents@fastapi-templates` | available |
| Next.js | `vercel-labs/vercel-plugin@nextjs` | available |
| React Query | `mindrally/skills@react-query` | available |
| Vitest | `onmax/nuxt-skills@vitest` | available |

