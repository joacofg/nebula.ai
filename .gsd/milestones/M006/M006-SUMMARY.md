---
id: M006
title: "Outcome-Aware Routing Calibration — Context"
status: complete
completed_at: 2026-04-02T13:34:10.125Z
key_decisions:
  - Kept calibrated routing bounded to one shared live/replay scoring contract with additive evidence layered onto a stable replay-critical subset instead of replacing the existing routing vocabulary.
  - Added only a small tenant-scoped `calibrated_routing_enabled` rollout valve rather than introducing a broader calibration tuning surface.
  - Derived tenant-scoped calibration evidence strictly from existing usage-ledger metadata and reused one typed summary contract across runtime, replay, and operator surfaces instead of creating new persistence or analytics subsystems.
  - Used the usage ledger as the parity seam between live runtime and simulation by correlating public `X-Request-ID` and persisted route evidence before asserting replay behavior.
  - Kept the selected persisted ledger row authoritative in operator inspection and treated calibration, recommendation, cache, and dependency cards as supporting context rather than creating a separate routing-inspection or analytics surface.
  - Assembled milestone close-out as a pointer-only integrated proof with discoverability links rather than duplicating calibrated-routing, replay, or operator-surface contracts.
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/chat_service.py
  - src/nebula/services/governance_store.py
  - src/nebula/services/policy_simulation_service.py
  - src/nebula/services/recommendation_service.py
  - src/nebula/api/routes/chat.py
  - src/nebula/api/routes/admin.py
  - src/nebula/models/governance.py
  - src/nebula/db/models.py
  - migrations/versions/20260401_0009_calibrated_routing_rollout.py
  - tests/test_router_signals.py
  - tests/test_response_headers.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-page.test.tsx
  - docs/route-decision-vocabulary.md
  - docs/m006-integrated-proof.md
  - README.md
  - docs/architecture.md
lessons_learned:
  - A diff against `main` can become a false negative once a milestone branch has already been merged; close-out needs the actual integration base or, failing that, explicit branch-history evidence that non-.gsd code shipped.
  - Calibration semantics stay explainable only when explicit overrides and policy-forced routes remain intentionally unscored and signal-free instead of synthesizing fake calibrated evidence.
  - Replay parity proof is strongest when it starts from a real runtime request plus the correlated usage-ledger row rather than synthetic replay fixtures alone.
  - When the same calibration labels appear intentionally in multiple bounded cards, test scoping is the right fix; forcing page-wide uniqueness weakens the real operator contract.
  - Pointer-only integrated proof docs remain maintainable when they join canonical seams in strict order and rely on focused executable tests for the actual behavior proof.
---

# M006: Outcome-Aware Routing Calibration — Context

**M006 turned Nebula’s heuristic-first router into a bounded, interpretable calibrated-routing system with ledger-backed tenant evidence, runtime/replay parity, request-first operator inspection, and a pointer-only integrated proof that preserved scope discipline.**

## What Happened

M006 closed the routing-quality gap left after M005 by building one coherent calibrated-routing story across runtime, persistence, replay, operator inspection, and documentation. S01 replaced duplicated heuristic branches with a shared calibrated scoring contract and propagated calibrated-versus-degraded route evidence through response headers, policy enforcement, and usage-ledger rows while adding only a bounded tenant rollout valve. S02 derived tenant-scoped calibration readiness from existing ledger metadata using a typed sufficient/thin/stale/gated/degraded summary instead of widening persistence or inventing an analytics subsystem, then reused that summary in simulation and operator surfaces. S03 proved replay parity from real runtime requests and correlated ledger rows so policy simulation changed-request samples report the same calibrated, degraded, and rollout-disabled semantics as live routing for the same tenant traffic class. S04 kept the selected persisted request authoritative by extending existing request-detail and Observability surfaces with calibrated routing inspection while leaving calibration, recommendation, cache, and dependency panels as supporting context. S05 then assembled the milestone close-out as a pointer-only integrated proof in docs/m006-integrated-proof.md, added discoverability links in README.md and docs/architecture.md, and re-ran focused backend and console seams to show the public request, X-Request-ID / X-Nebula-* headers, usage-ledger correlation, replay parity, and selected-request-first Observability all agree without widening Nebula into a black-box optimizer, analytics product, hosted-authority expansion, or new public API program. During milestone close-out, the direct diff-vs-main check returned empty because the M006 branch had already been merged onto main; verification therefore used the actual assembled branch history and non-.gsd file set in the worktree to confirm the milestone shipped real code, tests, and docs rather than planning artifacts alone.

## Success Criteria Results

- **Interpretable calibrated routing core delivered — met.** S01 replaced duplicated heuristic branches with one shared calibrated scoring contract, preserved the replay-critical subset, added explicit `route_mode`, calibrated/degraded markers, and additive `score_components`, and propagated that contract through runtime headers and ledger persistence. Evidence: S01 summary plus passing `tests/test_router_signals.py`, `tests/test_service_flows.py`, `tests/test_response_headers.py`, and `tests/test_governance_runtime_hardening.py`.
- **Tenant-scoped ledger-backed calibration evidence delivered — met.** S02 derives `CalibrationEvidenceSummary` from existing usage-ledger metadata, reports sufficient/thin/stale/gated/degraded states, excludes override/policy-forced rows from sufficiency math, and reuses the same summary in policy simulation and operator surfaces. Evidence: S02 summary and passed backend/console verification recorded there.
- **Runtime and simulation parity delivered — met.** S03 proved replay uses the same calibrated/degraded/rollout-disabled semantics and route-decision vocabulary as live runtime for the same tenant traffic class, and S05 re-proved that parity in the final backend close-out seam. Evidence: S03 summary plus `tests/test_governance_api.py -k "simulation and calibrated" -x` in S05 verification.
- **Existing operator surfaces expose calibration state without product sprawl — met.** S04 extended existing request-detail and Observability surfaces so operators can inspect calibrated-versus-heuristic/degraded routing state and contributing evidence while keeping the selected persisted request authoritative. Evidence: S04 summary/UAT and passing focused Observability and request-detail tests.
- **Integrated end-to-end proof path delivered and remains bounded — met.** S05 added `docs/m006-integrated-proof.md` as a pointer-only close-out path, linked it from README and architecture docs, and tightened focused backend/console seams to prove public headers → `X-Request-ID` → usage-ledger correlation → replay parity → selected-request-first Observability. Evidence: S05 summary/UAT, mechanical doc checks, `tests/test_response_headers.py -x`, `tests/test_governance_api.py -k "simulation and calibrated" -x`, and focused console test runs.
- **Milestone anti-drift scope held — met.** Across S01-S05, the delivered work stayed within existing runtime, admin, and Observability seams: no new public API family, no analytics dashboard or routing studio, no hosted-authority expansion, and no raw prompt/response persistence widening. Evidence: S05 validation of R049, pointer-only proof composition, and requirement/out-of-scope constraints preserved in `.gsd/REQUIREMENTS.md`.
- **Code changes exist in the assembled worktree — met.** The literal `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` check returned empty because `HEAD` is already on `main` with M006 merged, so a main-base diff is no longer a valid milestone-origin signal. Verification therefore used the assembled branch history and current non-`.gsd` file set (`git log --oneline --max-count=25` and `git diff --name-only HEAD~30 HEAD -- ':!.gsd/'`) to confirm shipped code/doc/test changes in `src/nebula/...`, `console/src/...`, `docs/...`, `migrations/...`, and `tests/...` matching the slice summaries.

## Definition of Done Results

- **All roadmap slices complete — met.** `M006-ROADMAP.md` shows S01-S05 all marked complete.
- **All slice summaries exist — met.** Verified presence of `S01-SUMMARY.md` through `S05-SUMMARY.md` under `.gsd/milestones/M006/slices/`.
- **All slice UAT artifacts exist — met.** Verified presence of `S01-UAT.md` through `S05-UAT.md` under `.gsd/milestones/M006/slices/`.
- **Cross-slice integration works coherently — met.** S02 consumes S01’s calibrated routing vocabulary and bounded rollout valve; S03 consumes S01/S02 runtime and evidence contracts for replay parity; S04 reuses the shared calibrated/degraded/disabled vocabulary and keeps the selected ledger row authoritative; S05 composes those shipped seams in strict order without redefining them. The milestone validation found no contradictory or undocumented cross-slice seam.
- **Integrated proof artifacts remain present in the final worktree — met.** Verified `docs/m006-integrated-proof.md`, plus discoverability links in `README.md` and `docs/architecture.md`.
- **Horizontal checklist — no separate horizontal checklist block was present in `M006-ROADMAP.md`, so there were no additional checklist items to audit.**

## Requirement Outcomes

- **R039: active → validated.** The assembled milestone now proves the stronger outcome-aware-routing claim rather than only advancing it. Evidence spans S01’s shared calibrated runtime contract and header/ledger propagation, S02’s tenant-scoped ledger-backed calibration summary, S03’s runtime/replay parity proved from real request-plus-ledger correlation, S04’s request-first operator inspection surfaces, and S05’s integrated proof path joining public headers, `X-Request-ID`, usage-ledger correlation, replay parity, and Observability.
- **R045: active → validated.** S02 delivered calibration using recent tenant-scoped observed outcomes derived from existing usage-ledger metadata, with bounded sufficient/thin/stale/gated/degraded classification and no raw payload persistence widening. S03 confirmed replay consumes the same semantics.
- **R046: active → validated.** S04 made calibrated versus degraded/heuristic routing state and the influencing evidence inspectable in existing request-detail and Observability surfaces without adding a new analytics surface.
- **R047: active → validated.** S01-S04 established explicit degraded, stale, thin, rollout-disabled, and null-mode semantics across runtime headers, ledger evidence, replay, and operator surfaces, proving fail-safe heuristic fallback remains deterministic and visible.
- **R048: active → validated.** S03 proved policy simulation replay uses the same calibration semantics, degraded-mode rules, and route-decision vocabulary as live runtime, and S05 re-verified that seam in the final backend close-out checks.
- **R049: active → validated.** S05 already validated the anti-drift constraint with the pointer-only integrated proof, discoverability links, and focused backend/console verification showing routing-quality improvement without black-box optimization, analytics-product drift, hosted-authority expansion, or unrelated platform sprawl.

## Deviations

The milestone instructions call for `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` as the code-change existence check. In this assembled worktree, `HEAD` is already `main` and contains the merged M006 commits, so that literal command returns no diff even though the milestone clearly shipped code. Close-out therefore used the current branch history and non-.gsd changed-file set as the equivalent integration-base evidence. This affected verification method only, not product scope or delivered behavior.

## Follow-ups

Treat the pre-existing duplicate-test-name Ruff warning in `tests/test_governance_api.py` as separate cleanup. If future routing work extends calibration beyond the bounded M006 scope, keep R050 deferred unless there is concrete evidence that operators need more than the single rollout/safety valve shipped here.
