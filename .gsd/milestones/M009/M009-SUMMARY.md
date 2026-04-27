---
id: M009
title: "Outcome-Grounded Routing Quality"
status: complete
completed_at: 2026-04-27T21:54:35.468Z
key_decisions:
  - Use one shared backend contract for recent tenant-scoped outcome evidence and route-score factors across runtime routing, replay, persistence, and operator evidence.
  - Extend routing with a bounded additive scoring model rather than a branch-heavy or opaque optimization approach.
  - Keep request detail and selected-request Observability as the primary operator surfaces for richer routing evidence, with tenant summary context supporting only.
  - Keep hosted and fleet-level state out of live route choice and outcome-evidence truth so M009 preserves Nebula’s local-authority boundary.
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/governance_store.py
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/policy_simulation_service.py
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/lib/admin-api.ts
  - docs/m009-integrated-proof.md
  - docs/route-decision-vocabulary.md
  - docs/architecture.md
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - tests/test_chat_completions.py
  - tests/test_response_headers.py
  - tests/test_router_signals.py
lessons_learned:
  - Pytest `-k` selectors are case-sensitive; mixed-case selectors in planning artifacts can falsely deselect intended tests and should match actual test naming.
  - Replay parity is easiest to trust when unchanged-policy parity and changed-policy drift are asserted separately within the same simulation coverage.
  - Close-out proof is more stable when it strengthens focused existing seams and deterministic request-detail coverage rather than adding broad new one-off integration harnesses.
---

# M009: Outcome-Grounded Routing Quality

**Improved Nebula’s live routing using bounded recent tenant-scoped outcome evidence while preserving replay parity, request-level evidence integrity, request-first operator explanation, and anti-sprawl product boundaries.**

## What Happened

M009 upgraded Nebula’s routing core from prompt-heuristic-only behavior to outcome-grounded decisioning anchored in bounded recent tenant-scoped evidence, while keeping the system explainable, replayable, and operator-controlled. S01 established the shared `calibration_summary` outcome-evidence contract and authoritative GovernanceStore summarization seam with explicit sufficient/thin/stale/degraded states. S02 wired that contract into live policy evaluation and router scoring so real chat-completions requests can route differently because of recent tenant evidence, while persisting exact route factors and additive score components onto the correlated usage-ledger row. S03 closed the replay credibility gap by reusing the same tenant-window summary and shared policy-evaluation semantics in admin simulation, proving unchanged-policy parity where evidence exists and degraded replay honesty where persisted signals are incomplete. S04 aligned selected-request Observability and request detail to the same grounded/thin/stale/degraded vocabulary without adding a new dashboard surface, keeping the selected request row authoritative and supporting context subordinate. S05 then assembled the final integrated proof through pointer-first docs and focused anti-drift tests that trace both a happy path and a degraded path across public request, persisted request evidence, replay parity, and request-first operator inspection, all without drifting into analytics-product sprawl, black-box optimization, or hosted-authoritative routing.

## Success Criteria Results

- **Live routing uses bounded recent tenant-scoped outcome evidence to improve local-vs-premium choices rather than prompt heuristics alone.** Met. S01 established the deterministic tenant-scoped evidence contract and S02 proved real `POST /v1/chat/completions` requests can route differently because of recent tenant evidence. Evidence: S02 verification passed in `tests/test_chat_completions.py -k "outcome_grounded or ledger or route"`, `tests/test_router_signals.py -k "outcome or evidence or route"`, `tests/test_service_flows.py -k "outcome_grounded or policy_service_live_evidence or hard_budget"`, and `tests/test_response_headers.py -k "route_mode or route_signals"`.
- **Policy simulation replay uses the same outcome-grounded routing semantics as live runtime and degrades honestly when evidence is incomplete.** Met. S03 injected a shared evidence summary into `PolicyService.evaluate()` and reused one tenant-window summary per simulation request, proving unchanged-policy replay parity and degraded replay honesty. Evidence: S03 verification passed in `tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"`, `tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)"`, and `console/src/components/policy/policy-form.test.tsx`.
- **Persisted request evidence records the actual outcome-grounded route factors that influenced the decision.** Met. S02 extended persisted `route_signals` additively with `outcome_evidence` state and score components and verified parity across headers, `policy_outcome`, and the correlated usage-ledger row. Evidence: S02 summary plus passing `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and `tests/test_governance_api.py` request-path assertions.
- **Existing request-first operator surfaces explain grounded vs thin/stale/degraded routing without widening into a dashboard-heavy analytics product.** Met. S04 aligned selected-request request-detail and Observability wording to grounded/thin/stale/degraded/rollout-disabled/unscored states while keeping summary cards subordinate to the selected request. Evidence: passing Vitest coverage in `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`, and `console/src/app/(console)/observability/observability-page.test.tsx`.
- **The final integrated proof covers both a happy-path request and a degraded-path request while preserving local authority and the metadata-only hosted boundary.** Met. S05 added `docs/m009-integrated-proof.md`, linked shared vocabulary and architecture docs, and hardened backend plus console anti-drift tests for the happy/degraded review chain. Evidence: passing `tests/test_chat_completions.py -k "outcome_grounded or ledger or policy_denied"`, `tests/test_response_headers.py -k "route_mode or route_signals"`, `tests/test_governance_api.py -k "returns_summary_and_preserves_saved_policy or supports_unchanged_and_empty_windows"`, and the focused console suites named in S05.

## Definition of Done Results

- **All slices complete:** Met. `gsd_milestone_status` reports S01-S05 all `complete`, with all tasks done in each slice.
- **All slice summaries exist:** Met. Verified presence of `.gsd/milestones/M009/slices/S01/S01-SUMMARY.md` through `S05-SUMMARY.md`, plus corresponding UAT artifacts.
- **Cross-slice integration points work correctly:** Met. Validation evidence shows S01’s shared evidence contract is consumed by S02 live routing, S03 replay parity, S04 operator rendering, and S05 integrated proof; S02 persisted request signals are consumed by S03/S04/S05; S03 replay semantics feed S04/S05; and S04 request-first operator proof feeds S05. `M009-VALIDATION.md` marks these boundaries honored.
- **Code changes exist beyond planning artifacts:** Met. Although `HEAD` is already on `main`, milestone-scoped commit evidence from `ca8b957..HEAD` shows non-`.gsd/` implementation changes across backend, console, docs, and tests, including `src/nebula/services/governance_store.py`, `src/nebula/services/policy_service.py`, `src/nebula/services/policy_simulation_service.py`, `console/src/components/ledger/ledger-request-detail.tsx`, `docs/m009-integrated-proof.md`, and multiple test files.
- **Horizontal checklist:** No separate Horizontal Checklist section was present in the roadmap, so there were no additional checklist items to audit.

## Requirement Outcomes

- **R073 → validated:** Supported by S02 live routing work. Evidence: bounded recent tenant-scoped outcome evidence now changes real runtime route choice and persists matching route factors on the correlated usage-ledger row, proven by `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_router_signals.py`, and `tests/test_service_flows.py`.
- **R074 → validated:** Supported by S03 replay parity work. Evidence: policy simulation reuses the same tenant-window evidence summary and scoring semantics as runtime, with unchanged-policy parity and honest degraded replay behavior proven by `tests/test_service_flows.py`, `tests/test_governance_api.py`, and `console/src/components/policy/policy-form.test.tsx`.
- **R075 → validated:** Supported by S02 request evidence persistence work. Evidence: correlated usage-ledger rows record the actual live outcome-grounded evidence state and additive score components, or honestly record policy-denied paths without fabricated route signals.
- **R076 → validated:** Supported by S04 operator-surface work. Evidence: selected-request Observability and request detail now explain grounded, thin, stale, degraded, rollout-disabled, and unscored routing states through focused console tests.
- **R077 → validated:** Supported by S01 evidence classification work. Evidence: deterministic GovernanceStore summarization covers no-evidence, thin, stale, degraded, sufficient, tenant/window scoping, and governance-suppressed route-signal cases with passing backend tests.
- **R078 → validated:** Supported by S05 close-out proof. Evidence: `docs/m009-integrated-proof.md` remains pointer-first on existing seams, backend proof covers happy/degraded request chains, console proof keeps request-first authority, and no new API surface, analytics flow, black-box optimizer, or hosted-authoritative decision layer was introduced.

## Deviations

Execution deviations were limited and did not change milestone outcomes: some planned verification commands required environment-specific adjustments (`./.venv/bin/pytest` instead of bare `pytest`, `python3.12` instead of `python`), the S02 response-header verification selector needed lowercase `-k` terms because pytest matching is case-sensitive, S03 implemented admin replay proof by restructuring existing simulation tests into unchanged-policy and changed-policy passes, and S05 retained deterministic request-detail degraded proof instead of a broader brittle Observability-only flow.

## Follow-ups

Milestone validation remained `needs-attention` because per-slice ASSESSMENT artifacts were absent even though slice summaries, UAT artifacts, and verification evidence were present. Future milestone workflows should either emit those artifacts explicitly or align validation criteria to the actual shipped artifact set. Also consider cleaning up the pre-existing FastAPI deprecation warning and normalizing pytest selector casing in planning templates.
