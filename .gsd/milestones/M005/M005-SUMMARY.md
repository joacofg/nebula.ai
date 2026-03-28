---
id: M005
title: "Adaptive Decisioning Control Plane"
status: complete
completed_at: 2026-03-28T04:27:01.923Z
key_decisions:
  - Focused v4 on decisioning quality and operator actionability rather than API-parity or hosted-authority expansion.
  - Rendered route-decision evidence as stable labeled operator fields plus an additive route-score header while keeping override routes signal-free.
  - Reused production routing and policy-evaluation seams for replay-only simulation instead of building separate simulation logic.
  - Centralized hard cumulative budget guardrail enforcement in PolicyService and reused that path for simulation to keep runtime/replay behavior aligned.
  - Shipped recommendation feedback as a bounded typed read model grounded in usage-ledger evidence plus coarse cache health, while keeping cache editing inside the existing policy preview/save workflow.
  - Composed the final v4 proof as a pointer-only integrated walkthrough with top-level discoverability links instead of duplicating detailed contracts.
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/chat_service.py
  - src/nebula/services/policy_simulation_service.py
  - src/nebula/services/recommendation_service.py
  - src/nebula/services/governance_store.py
  - src/nebula/api/routes/admin.py
  - src/nebula/api/routes/chat.py
  - src/nebula/models/governance.py
  - src/nebula/db/models.py
  - src/nebula/core/container.py
  - migrations/versions/20260326_0006_route_signals.py
  - migrations/versions/20260328_0007_hard_budget_guardrails.py
  - migrations/versions/20260328_0008_cache_policy_controls.py
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/lib/admin-api.ts
  - docs/route-decision-vocabulary.md
  - docs/policy-guardrails.md
  - docs/v4-integrated-proof.md
  - README.md
  - docs/architecture.md
  - tests/test_router_signals.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - tests/test_governance_runtime_hardening.py
lessons_learned:
  - Milestone close-out must verify the assembled worktree, not just task-local output; that process caught real integration gaps such as missing ledger hydration for route_signals and a missing migration for cache-policy controls.
  - Decisioning features stay trustworthy when they reuse existing runtime semantics and evidence paths rather than introducing parallel engines or free-form analytics payloads.
  - Operator-facing control-plane surfaces are strongest when they use stable labeled contracts, bounded read models, and explicit non-mutation wording instead of raw JSON or opaque optimization claims.
  - Scope-discipline requirements like R044 need explicit end-to-end proof, not just intent; the final pointer-only integrated walkthrough plus focused runtime/UI verification provided that proof.
---

# M005: Adaptive Decisioning Control Plane

**M005 turned Nebula’s existing routing, policy, ledger, and semantic-cache seams into a tighter operator decisioning control plane with interpretable routing evidence, replay-before-save policy simulation, enforceable hard budget guardrails, bounded recommendations, semantic-cache tuning, and a final integrated proof that stayed within the intended v4 scope.**

## What Happened

M005 assembled five slices into one coherent v4 decisioning milestone. S01 replaced the older shallow routing posture with an interpretable route-decision vocabulary, normalized route score exposure, ledger persistence for route signals, and operator-visible route-decision evidence in Observability. S02 reused that route vocabulary to build a replay-only policy simulation loop that lets operators preview candidate routing or policy changes against recent tenant traffic before saving, with explicit non-mutation semantics across backend, admin API, and console. S03 then added explicit hard cumulative budget guardrails enforced centrally through PolicyService so runtime requests and simulation replays share the same downgrade-versus-deny semantics, with operator-readable budget evidence rendered in existing admin and console surfaces. S04 added a deterministic, bounded RecommendationBundle and explicit semantic-cache tuning controls, grounding next-best-action guidance in recent usage-ledger traffic plus coarse runtime cache health while keeping editing inside the existing policy save/preview flow. S05 closed the milestone by assembling those shipped seams into docs/v4-integrated-proof.md, adding discoverability links from README.md and docs/architecture.md, and revalidating the assembled backend, admin API, console, and documentation proof path. Across the milestone, close-out verification also caught and fixed real assembled-worktree integration gaps—ledger hydration for route_signals in S01 and the missing Alembic migration for cache-policy controls in S04—so the final milestone record reflects the verified assembled state rather than task-local assumptions.

## Success Criteria Results

- ✅ **Adaptive routing quality and interpretability improved beyond prompt-length heuristics alone.** S01 introduced explicit route signals (`token_count`, `complexity_tier`, `keyword_match`, `model_constraint`, `budget_proximity`), a normalized route score, `X-Nebula-Route-Score`, persisted `route_signals` in the usage ledger, and labeled operator-visible route-decision fields in the console. Evidence: S01 summary plus passing focused backend verification in `tests/test_router_signals.py` and broader chat/admin/governance suites cited there.
- ✅ **Operators can simulate candidate routing/policy changes against recent real traffic before saving.** S02 added `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, a replay-only `PolicySimulationService`, and preview-before-save console UX with aggregate deltas and changed-request samples. Evidence: passing `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x`, `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x`, and `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
- ✅ **Tenant policy can enforce hard spend limits with explicit downgrade or denial behavior and explainable outcomes.** S03 added `hard_budget_limit_usd` and `hard_budget_enforcement`, centralized guardrail enforcement in `PolicyService.evaluate()`, reused the same path from simulation, and surfaced budget evidence through policy options, ledger detail, simulation output, and docs. Evidence: S03 summary plus focused backend/API/UI verification cited there.
- ✅ **Operators receive grounded recommendation-grade feedback and can intentionally tune semantic-cache behavior.** S04 delivered deterministic, tenant-scoped recommendations via `GET /v1/admin/tenants/{tenant_id}/recommendations`, Observability recommendation cards, runtime cache summaries, and explicit policy knobs for `semantic_cache_similarity_threshold` and `semantic_cache_max_entry_age_hours`. Evidence: S04 summary plus passing `./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x`, `./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x`, and related Vitest coverage.
- ✅ **The full v4 decisioning story is assembled end-to-end and remains narrow, interpretable, and operator-driven.** S05 added `docs/v4-integrated-proof.md`, top-level links in `README.md` and `docs/architecture.md`, and revalidated the joined behavior with passing integrated backend/admin/console tests and explicit file/link checks. I also reran those final milestone-level checks during close-out: `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x` (11 passed), `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x` (13 passed), `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx` (5 files / 22 tests passed), and `test -f docs/v4-integrated-proof.md && rg -n "v4-integrated-proof\.md" README.md docs/architecture.md`.
- ✅ **Code-change verification passed.** `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` showed non-`.gsd` code/docs changes, so the milestone produced real product artifacts beyond planning state.

## Definition of Done Results

- ✅ **All roadmap slices are complete.** The inlined roadmap marks S01-S05 as done, and the milestone-completion tool also validates that all slices are complete before marking the milestone finished.
- ✅ **All slice summaries exist.** Verified by listing `.gsd/milestones/M005` contents: S01-S05 each have corresponding `S##-SUMMARY.md` files.
- ✅ **Cross-slice integration holds in the assembled worktree.** S02 reuses S01’s persisted route-signal vocabulary for simulation replay; S03 shares `PolicyService.evaluate()` semantics across runtime and simulation; S04 builds recommendations and cache controls on top of S02/S03 evidence; S05 composes those seams without redefining them. Final close-out reran integrated backend/admin/console verification proving those seams still work together.
- ✅ **Documentation/discoverability closure is in place.** `docs/v4-integrated-proof.md` exists and is linked from both `README.md` and `docs/architecture.md`, satisfying the final proof/discoverability contract.
- ℹ️ **Horizontal checklist.** The roadmap excerpt available during close-out contained no separate Horizontal Checklist section, so there were no additional unchecked horizontal items to record.

### Decision Re-evaluation
| Decision | Re-evaluation | Status |
|---|---|---|
| D022 | Still valid. The delivered work stayed focused on decisioning quality, simulation, hard guardrails, recommendation-grade feedback, and cache tuning visibility; no evidence of API-parity, SDK, or hosted-authority sprawl appeared in the assembled milestone. | Keep |
| D023 | Still valid. Route metadata appears as stable labeled fields in the ledger detail drawer and route score is additive via `X-Nebula-Route-Score`, while override routes remain signal-free. | Keep |
| D024 | Still valid. R039 is materially advanced but not fully validated because scoring still relies on heuristic signals rather than broader outcome-aware calibration. | Keep / revisit in future milestone if outcome-aware scoring is added |
| D025 | Still valid. The replay-only simulation contract, admin endpoint, and console preview-before-save flow all shipped and passed focused verification. | Keep |
| D026 | Still valid. Hard-budget enforcement centralized in `PolicyService` kept runtime and replay semantics aligned and avoided a second budget engine. | Keep |
| D027 | Still valid. R041 remains supported by shipped runtime, API, console, and docs evidence. | Keep |
| D028 | Still valid. Recommendation feedback shipped as a bounded, typed, read-only tenant-scoped surface grounded in ledger-backed evidence and runtime cache health. | Keep |
| D029 | Still valid. Semantic-cache tuning stayed intentionally narrow and inspectable through explicit policy knobs and bounded summaries. | Keep |
| D030 | Still valid. The final proof stayed narrow and operator-driven, with no new public API family, autonomous optimizer, hosted authority expansion, or SDK/app-platform work. | Keep |
| D031 | Still valid. The pointer-only integrated proof plus discoverability links avoided duplicating contracts and the final verification relied on focused tests and file/link checks rather than brittle prose snapshots. | Keep |

## Requirement Outcomes

- **R040: active → validated.** Supported by S02’s replay-only simulation loop using recent tenant usage-ledger traffic, the non-mutating admin simulation endpoint, and preview-before-save console UX. Revalidated by milestone close-out evidence and already reflected in `.gsd/REQUIREMENTS.md`.
- **R041: active → validated.** Supported by S03’s explicit hard-budget policy controls, centralized downgrade-versus-deny enforcement in `PolicyService`, simulation/runtime alignment, and operator-visible budget evidence. Already reflected in `.gsd/REQUIREMENTS.md` with focused verification proof.
- **R042: active → validated.** Supported by S04’s deterministic `RecommendationBundle`, tenant-scoped recommendations endpoint, and bounded recommendation rendering in Observability. Already reflected in `.gsd/REQUIREMENTS.md` with focused verification proof.
- **R043: active → validated.** Supported by S04’s explicit semantic-cache tuning controls, persistence and migration coverage, bounded cache summaries, and policy preview/save plus observability integration. Already reflected in `.gsd/REQUIREMENTS.md` with focused verification proof.
- **R044: active → validated.** Supported by S05’s pointer-only integrated proof, discoverability links, and milestone-level integrated verification showing that M005 improved operator decision quality/control without widening scope. This requirement now has sufficient milestone-close evidence to move to validated.
- **R039: remains active.** S01 materially advanced it through explicit routing signals, score/header exposure, ledger persistence, and operator-visible route-decision evidence, but the assembled router is still heuristic-first rather than fully outcome-aware. Keeping it active remains consistent with D024 and the current evidence.

## Deviations

The roadmap target was met without scope widening. The main execution deviations were integration-hygiene fixes discovered during slice close-out: S01 required a governance-store hydration fix so persisted `route_signals` surfaced back through admin ledger reads, and S04 required the missing Alembic migration for new semantic-cache policy fields so the assembled API contract matched the database schema.

## Follow-ups

Future decisioning work should revisit R039 with broader outcome-aware scoring inputs and calibration beyond heuristic complexity/policy cues. Also consider cleaning up the FastAPI deprecation warning around `HTTP_422_UNPROCESSABLE_ENTITY` surfaced during governance API verification.
