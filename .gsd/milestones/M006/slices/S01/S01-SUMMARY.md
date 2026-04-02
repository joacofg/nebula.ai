---
id: S01
parent: M006
milestone: M006
provides:
  - A stable calibrated routing contract that live runtime and replay can share, plus tenant-scoped rollout control and correlated header/ledger evidence for calibrated versus degraded routing decisions.
requires:
  []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/chat_service.py
  - src/nebula/api/routes/chat.py
  - src/nebula/api/routes/admin.py
  - src/nebula/services/governance_store.py
  - src/nebula/db/models.py
  - src/nebula/models/governance.py
  - migrations/versions/20260401_0009_calibrated_routing_rollout.py
  - tests/test_router_signals.py
  - tests/test_governance_runtime_hardening.py
  - tests/test_service_flows.py
  - tests/test_response_headers.py
  - tests/test_governance_api.py
  - docs/route-decision-vocabulary.md
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Kept the replay-critical signal subset stable while adding calibrated/degraded mode markers and additive score breakdown fields instead of replacing existing route signals.
  - Preserved empty `route_signals` and `route_score=0.0` for explicit override and policy-forced routes so calibrated evidence appears only for token-complexity decisions.
  - Implemented calibrated-routing rollout as one bounded tenant policy boolean that gates token-complexity auto routing only, leaving explicit overrides and policy-forced routes unchanged.
  - Aligned policy-denial response headers with the normal/error metadata path by emitting `X-Nebula-Route-Score` and conditional `X-Nebula-Route-Mode` on denied routes too.
patterns_established:
  - Use one shared router scoring helper for both live routing and replay reconstruction, with additive evidence fields layered on top of a stable replay-critical subset.
  - When route metadata becomes part of operator proof, verify header and usage-ledger parity together so denial and provider-error paths cannot silently drift from the success path.
  - Add new operator controls for decisioning as bounded rollout valves in the existing governance surface before considering any broader tuning UI.
observability_surfaces:
  - `X-Nebula-Route-Score` and conditional `X-Nebula-Route-Mode` response headers on successful, denied, and fallback-blocked paths.
  - Usage-ledger `route_reason`, `policy_outcome`, and `route_signals` rows correlated by `X-Request-ID` for routed and provider-error requests.
  - Focused backend header/ledger verification in `tests/test_response_headers.py` plus runtime/policy verification in `tests/test_governance_runtime_hardening.py` and `tests/test_service_flows.py`.
drill_down_paths:
  - .gsd/milestones/M006/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:09:02.837Z
blocker_discovered: false
---

# S01: Calibrated routing core

**Shipped a shared calibrated routing contract, propagated calibrated route evidence through runtime headers and usage-ledger rows, and added a bounded tenant rollout valve for calibrated routing in governance APIs and the policy editor.**

## What Happened

S01 replaced the router’s duplicated heuristic branches with one calibrated scoring contract used by both live routing and replay reconstruction. The shared path keeps the replay-critical subset (`token_count`, `keyword_match`, `complexity_tier`) stable while adding interpretable calibrated/degraded state, `route_mode`, and additive `score_components` so downstream slices can reason about route evidence without inventing new vocabulary. The slice then wired that contract through policy resolution, chat runtime propagation, error headers, and usage-ledger persistence so routed responses, denied paths, fallback-blocked failures, and persisted request evidence all tell the same calibrated story. To keep the rollout bounded, S01 added a single tenant policy field, `calibrated_routing_enabled`, with persistence, migration, admin API exposure, runtime/simulation enforcement, and an existing-policy-editor checkbox rather than a broader tuning surface. During close-out verification, the stronger backend header check exposed two real contract drifts: policy-denied responses were not emitting the same route-score/route-mode header semantics as the normal metadata path, and one focused response-header test still carried stale expected calibrated scores after fixture text changed. Both were corrected before slice completion, leaving the assembled worktree aligned across router docs, runtime behavior, governance APIs, and console controls.

## Verification

Passed the full slice verification set after fixes: `./.venv/bin/pytest tests/test_router_signals.py -x`, `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py tests/test_response_headers.py -k "simulation or runtime_policy or response_headers or denied or fallback or hard_budget" -x`, `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "simulation or runtime_policy" tests/test_response_headers.py -x`, `./.venv/bin/alembic upgrade head && ./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation or route_reason" -x`, and `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`. Observability-sensitive checks were included in the stronger backend verification by asserting denied and fallback-blocked responses expose calibrated metadata headers that correlate with persisted usage-ledger route evidence.

## Requirements Advanced

- R039 — Established the calibrated routing core: shared live/replay scoring contract, additive calibrated/degraded route evidence, runtime/policy/header/ledger propagation, and a bounded tenant rollout valve for calibrated auto routing.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

The written T02 task-plan pytest command under-selected `tests/test_response_headers.py` because of pytest argument ordering, so slice verification also ran a stronger focused backend command that explicitly covered the touched response-header contract. Close-out verification additionally fixed stale focused tests and aligned policy-denial headers with the shipped metadata contract before completing the slice.

## Known Limitations

Outcome-aware calibration is not complete yet. The router now exposes an interpretable calibrated contract and bounded rollout control, but later slices still need tenant-scoped ledger-backed calibration summaries, explicit runtime/simulation parity at replay time, richer operator inspection surfaces, and the final integrated proof before R039 can be validated. The stronger backend suite still emits a FastAPI deprecation warning around `HTTP_422_UNPROCESSABLE_ENTITY`, but it does not block slice behavior.

## Follow-ups

S02 should derive tenant-scoped calibration summaries from usage-ledger evidence using the stable replay-critical signal subset and the new calibrated/degraded markers rather than widening the persisted signal contract. S03 should preserve the policy-denial and fallback-blocked header parity established here when replay starts surfacing calibrated/degraded semantics, so live runtime and simulation stay correlated. S04 should treat the existing route-mode/score/signals vocabulary as authoritative when building operator inspection surfaces instead of inventing alternate labels or analytics framing.

## Files Created/Modified

- `src/nebula/services/router_service.py` — Replaced duplicated heuristic branches with a shared calibrated scoring contract and additive route-signal vocabulary for live routing and replay.
- `src/nebula/services/policy_service.py` — Applied calibrated-routing rollout gating, preserved calibrated policy outcome semantics, and aligned policy-denial headers with route-score/route-mode metadata.
- `src/nebula/services/chat_service.py` — Preserved calibrated route score and signal payloads through runtime metadata, provider-error handling, and usage-ledger writes.
- `src/nebula/api/routes/chat.py` — Exposed calibrated route metadata consistently through response headers, including conditional route-mode emission.
- `src/nebula/api/routes/admin.py` — Surfaced the bounded calibrated-routing rollout field through admin policy reads/writes and policy options.
- `src/nebula/services/governance_store.py` — Persisted the new calibrated-routing policy field through governance storage.
- `src/nebula/db/models.py` — Added ORM support for the calibrated-routing rollout field on tenant policies.
- `src/nebula/models/governance.py` — Extended tenant policy models with `calibrated_routing_enabled`.
- `migrations/versions/20260401_0009_calibrated_routing_rollout.py` — Added the schema migration for the calibrated-routing rollout field.
- `tests/test_router_signals.py` — Locked the calibrated route-signal vocabulary, replay compatibility, degraded behavior, and additive score breakdown in focused router coverage.
- `tests/test_governance_runtime_hardening.py` — Verified hard-budget/runtime interactions remain aligned with calibrated routing behavior.
- `tests/test_service_flows.py` — Verified runtime policy flow behavior with calibrated route metadata and replay-sensitive paths.
- `tests/test_response_headers.py` — Asserted calibrated metadata parity across denied, fallback-blocked, and persisted usage-ledger evidence, and updated stale expected values to the shipped contract.
- `tests/test_governance_api.py` — Verified admin policy options, simulation behavior, and route-reason semantics for the new rollout control.
- `docs/route-decision-vocabulary.md` — Updated the route vocabulary doc to reflect the shipped calibrated/degraded signal contract.
- `console/src/lib/admin-api.ts` — Added the calibrated-routing policy field to console admin types.
- `console/src/components/policy/policy-form.tsx` — Added the bounded calibrated-routing rollout checkbox and ensured form-state serialization includes the new field.
- `console/src/components/policy/policy-form.test.tsx` — Verified the policy form submits and previews the calibrated-routing rollout field correctly.
- `console/src/components/policy/policy-page.test.tsx` — Verified the policy page exposes the bounded rollout control within the existing policy surface.
- `.gsd/KNOWLEDGE.md` — Recorded calibrated-routing contract and verification lessons that downstream slices should preserve.
- `.gsd/PROJECT.md` — Updated project current state to reflect that M006/S01 is complete and what remains for R039.
