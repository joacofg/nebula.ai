# S05 — Research

**Date:** 2026-04-27

## Summary

S05 is a targeted close-out slice for requirement **R078**. The missing work is not new product behavior; it is the canonical integrated proof artifact plus the smallest set of verification seams needed to prove the already-shipped M009 runtime, replay, and request-first UI surfaces tell one consistent story for **both** a happy path and a degraded path. The safest approach is to follow the existing integrated-proof pattern from `docs/m006-integrated-proof.md`, `docs/m007-integrated-proof.md`, and `docs/m008-integrated-proof.md`: create one pointer-first review document that assembles canonical seams in order rather than restating contracts or inventing a new dashboard/workflow.

The hard constraint from prior slices is parity discipline. MEM049/MEM056/MEM059 and the S02/S03 summaries all point to the same rule: `GovernanceStore.summarize_calibration_evidence()` remains the single evidence-classification seam, persisted `route_signals.outcome_evidence` remains the live truth seam, and `calibration_summary` on replay/admin responses remains compatibility naming for the same shared contract. S05 should therefore prove integration by reusing existing artifacts and tests, not by adding a second evidence model, a summary-first operator surface, or replay-only vocabulary.

## Recommendation

Write a new integrated-proof doc, likely `docs/m009-integrated-proof.md`, that mirrors the structure and tone of prior milestone close-out docs. Start from `docs/route-decision-vocabulary.md`, then point to one real `POST /v1/chat/completions` happy-path request, the correlated `GET /v1/admin/usage/ledger?request_id=...` row, `POST /v1/admin/tenants/{tenant_id}/policy/simulate` parity, and the selected-request-first Observability/request-detail surfaces. Then repeat the same review logic for a degraded-path request/replay story, keeping the selected ledger row authoritative and all tenant summaries subordinate. This directly satisfies R078 without widening scope.

Back the doc with focused verification in existing backend and console suites rather than broad new test files. The natural proof seam is to extend current tests so one happy-path scenario and one degraded-path scenario each assert the full chain: public headers → persisted ledger row → replay/admin payload → request-first operator wording. The `verify-before-complete` skill is relevant here as execution discipline: the slice should close only after the integrated verification commands run in this slice, not by relying on earlier slice claims. For docs/process shape, the installed `write-docs` skill is the closest fit; for console assertions, `react-best-practices` is relevant but optional.

## Implementation Landscape

### Key Files

- `docs/m006-integrated-proof.md` — Best structural template for S05. Already assembles request → ledger → replay → Observability in pointer-only form; M009 should extend this pattern with outcome-grounded happy/degraded semantics.
- `docs/m007-integrated-proof.md` — Canonical request-first operator-hierarchy language. Reuse its framing to keep Observability/request detail primary and supporting cards subordinate.
- `docs/m008-integrated-proof.md` — Shows the close-out doc style Nebula prefers: canonical sources, minimal operator walkthrough, explicit failure modes, and anti-scope-drift wording.
- `docs/route-decision-vocabulary.md` — Stable vocabulary reference, but currently only documents pre-M009 additive components (`token_score`, `keyword_bonus`, `policy_bonus`, `budget_penalty`, `total_score`). S05 likely needs this doc updated additively to mention M009 outcome-grounded fields (`score_components.outcome_bonus`, `score_components.evidence_penalty`, `route_signals.outcome_evidence.*`) because the integrated proof should point at a stable vocabulary source rather than inventing new wording inline.
- `src/nebula/models/governance.py` — Defines the shared external shapes S05 is proving, especially `UsageLedgerRecord.route_signals`, `CalibrationEvidenceSummary`, and `PolicySimulationChangedRequest`. Note that `PolicySimulationChangedRequest` does **not** carry baseline/simulated `outcome_evidence` objects directly; replay proof must stay anchored to existing fields like `simulated_policy_outcome`, `simulated_route_mode`, `simulated_route_score`, and top-level `calibration_summary`.
- `src/nebula/api/routes/admin.py` — Canonical admin seams already used in prior integrated proofs: `GET /v1/admin/usage/ledger`, `GET /v1/admin/tenants/{tenant_id}/recommendations`, and `POST /v1/admin/tenants/{tenant_id}/policy/simulate`. S05 should reference these seams rather than adding a new integrated API.
- `src/nebula/services/policy_simulation_service.py` — Confirms replay computes one tenant-window `calibration_summary` once, injects it into all evaluations, and returns bounded approximation notes. Useful source when writing the replay section of the integrated proof and when deciding what backend parity tests can assert.
- `tests/test_chat_completions.py` — Best happy/degraded request-path seam. Already contains:
  - `test_chat_completions_outcome_grounded_request_persists_matching_route_signals()` for the happy path (premium flip from sufficient evidence, exact `route_signals.outcome_evidence`, exact additive score components).
  - `test_chat_completions_outcome_grounded_policy_denial_persists_evidence_state_without_route_signals()` for a degraded/guarded request-adjacent path (policy denial keeps `outcome_evidence=sufficient` in `policy_outcome` while persisting `route_signals=None`).
  These are the closest existing public-request proof seams.
- `tests/test_response_headers.py` — Best public-header correlation seam. `test_response_headers_expose_outcome_grounded_route_mode_and_header_ledger_parity()` already proves happy-path header ↔ ledger parity. Important pitfall from S02: use lowercase `-k "route_mode or route_signals"`; the mixed-case selector in old planning artifacts deselects everything.
- `tests/test_governance_api.py` — Best replay/admin seam. `test_admin_policy_simulation_returns_summary_and_preserves_saved_policy()` already proves unchanged-policy parity, a degraded replay row (`missing_route_signals`), and non-mutating simulation in one scenario. This is likely the main place to add/clarify integrated proof assertions for S05 rather than starting a new suite.
- `tests/test_service_flows.py` — Lower-level parity/degraded coverage for `summarize_calibration_evidence()` and replay injection. Probably doesn’t need new integrated-proof assertions unless planner wants a narrower contract guardrail around evidence-state vocabulary.
- `console/src/components/ledger/ledger-request-detail.tsx` — Authoritative request-detail seam for selected-request explanation. Already maps grounded/thin/stale/degraded/rollout-disabled/unscored states from persisted `route_signals` plus optional `calibrationSummary`.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Focused request-detail operator wording proof. Good place to add/strengthen assertions if the integrated proof doc needs exact UI language to stay locked.
- `console/src/app/(console)/observability/page.tsx` — Selected-request-first composition that S05 should cite in the final walkthrough. It already describes “Selected request evidence first” and keeps follow-up recommendation/calibration/cache/dependency cards subordinate.
- `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` — Existing page-level request-first hierarchy proof seams. Likely enough for S05 unless integrated close-out needs one more explicit assertion tying degraded calibration wording to selected-request authority.
- `console/src/lib/admin-api.ts` — Shared TS contract. Confirms current frontend vocabulary includes `CalibrationEvidenceSummary.state: "sufficient" | "thin" | "stale" | "degraded"`; no replay-only or analytics-only type expansion is needed.
- `docs/architecture.md` — Contains the growing index of integrated proof docs. If `docs/m009-integrated-proof.md` is added, this index should link it alongside M006–M008 so the proof is discoverable.

### Build Order

1. **Lock the canonical documentation seam first.**
   - Create `docs/m009-integrated-proof.md` using M006/M007/M008 as templates.
   - Reuse existing source hierarchy: vocabulary → one public request → correlated ledger row → replay parity → request-first Observability/request detail.
   - Make the happy-path and degraded-path sections explicit and keep them pointer-based, not screenshot- or payload-dump-heavy.
   - This unblocks the rest of the slice because planner/executor then know what exact seams the tests must prove.

2. **Update shared vocabulary only if the doc currently lacks a stable reference for M009 fields.**
   - Additive update to `docs/route-decision-vocabulary.md` for `outcome_bonus`, `evidence_penalty`, and `route_signals.outcome_evidence` if the integrated proof would otherwise need to define them inline.
   - Keep this as a bounded edit; do not rewrite the whole route-vocabulary doc.

3. **Tighten backend integrated-proof assertions in existing suites.**
   - Prefer extending `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and especially `tests/test_governance_api.py` so one happy path and one degraded path each have an explicit end-to-end proof chain.
   - The strongest existing degraded seam is the replay scenario with a suppressed ledger clone (`missing_route_signals`) inside `test_admin_policy_simulation_returns_summary_and_preserves_saved_policy()`; planner can either strengthen that test or extract a focused close-out test from the same fixture pattern.
   - Avoid new provider-calling flows or a new admin endpoint.

4. **Only then adjust console tests if wording drift is still possible.**
   - If the integrated proof doc depends on exact grounded/degraded wording already present, existing S04 tests may be enough.
   - If not, add minimal assertions to `ledger-request-detail.test.tsx` / `observability-page.test.tsx` that the degraded path still leaves the selected request row authoritative while calibration summary is supporting context only.

5. **Update doc indexing/discoverability last.**
   - Add the new integrated proof to `docs/architecture.md` once the doc exists so future reviewers can find it without re-exploring milestone history.

### Verification Approach

Run proof-oriented suites that map directly to the final walkthrough:

- `./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or policy_denied"`
  - Confirms the public request seam for both the happy path and the denied/degraded-adjacent path.
- `./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals"`
  - Lowercase selector required; proves public header ↔ ledger parity.
- `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or usage_ledger)"`
  - Confirms replay parity, degraded honesty, non-mutation, and correlated ledger/admin evidence.
- `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'`
  - Confirms the selected request remains authoritative and grounded/degraded wording is preserved.
- `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`
- `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'`
  - Confirm request-first page hierarchy and subordinate supporting context.

Observable proof targets for the final slice:

- Happy path: a real `POST /v1/chat/completions` request flips to premium because of sufficient tenant evidence, returns `X-Nebula-Route-Mode=calibrated`, persists `route_signals.outcome_evidence.state == "sufficient"`, and replay preserves route target/reason/mode/score parity under unchanged policy.
- Degraded path: a persisted or replayed request with incomplete signals surfaces honest degraded semantics (`calibration_summary.state == "degraded"` or replay row with `missing_route_signals` / null route-mode fields as appropriate), while request-first UI and docs still anchor operators to the selected request row rather than the tenant summary.
- Scope guardrail: no new API surface, no new dashboard/reporting surface, no hosted-authority language, and no replay-only evidence vocabulary.

## Constraints

- **R078 is the slice owner and anti-sprawl guardrail.** S05 must prove integration without widening into analytics-product work, black-box optimization, or hosted authority.
- **Shared evidence seam only.** Per MEM056/MEM059, do not re-classify evidence outside `GovernanceStore.summarize_calibration_evidence()`.
- **Replay stays additive and compatibility-shaped.** `calibration_summary` naming must remain on admin/replay payloads; do not rename public/admin fields just for the proof doc.
- **Selected-request-first hierarchy is already a project decision (D051/MEM051).** Any S05 UI/test edits must preserve that the selected ledger row is primary and tenant summary is supporting only.
- **No new integrated endpoint.** Existing close-out docs point to canonical seams; they do not add orchestration APIs or synthetic proof payloads.

## Common Pitfalls

- **Using the old mixed-case pytest selector** — `tests/test_response_headers.py -k "Route-Mode or route_signals"` deselects everything because `-k` is case-sensitive. Use lowercase `route_mode`.
- **Treating `calibration_summary` as a second evidence model** — S03 intentionally kept the field name for compatibility, but its `state` now carries the shared outcome-evidence semantics. The doc should explain this once and then point back to canonical sources.
- **Assuming degraded proof must come from live headers only** — the strongest degraded seam currently lives in replay/admin and selected-request UI handling of incomplete persisted signals. The integrated proof can cover a degraded *review path* without inventing a new degraded public API contract.
- **Over-documenting internals inside the integrated proof** — prior Nebula integrated-proof docs are pointer-first. Restating full payload shapes, UI copy, or service logic will drift faster than the canonical sources.
- **Adding replay-only UI wording** — S03/S04 deliberately widened existing vocabulary to include `degraded`; don’t introduce a new preview-only term for S05.

## Open Risks

- The current shared vocabulary doc may still under-document M009-specific additive fields (`outcome_bonus`, `evidence_penalty`, `outcome_evidence`). If left unaddressed, the integrated proof doc may be forced to define terminology inline, which is contrary to the established pattern.
- The best degraded path today is split across backend replay assertions and UI wording tests rather than one single browser-style walkthrough. Planner may need one small additional assertion seam to make the degraded proof path feel as discoverable as the happy path.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Documentation / close-out narrative | `write-docs` | installed |
| Completion evidence discipline | `verify-before-complete` | installed |
| React / Next.js console surfaces | `react-best-practices` | installed |
| FastAPI backend | `wshobson/agents@fastapi-templates` | available |
| FastAPI backend | `mindrally/skills@fastapi-python` | available |
| Next.js | `vercel-labs/vercel-plugin@nextjs` | available |
| Playwright / browser verification | `currents-dev/playwright-best-practices-skill@playwright-best-practices` | available |
