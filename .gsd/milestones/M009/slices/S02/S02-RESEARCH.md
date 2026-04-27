# S02 — Research

**Date:** 2026-04-27

## Summary

S02 is a targeted backend integration slice that should deepen the existing calibrated-routing seam rather than introduce a new routing subsystem. The code already has the right skeleton: `RouterService` owns additive route scoring, `PolicyService` is the only live-routing orchestration seam, `ChatService` already persists request-level `route_signals` into the usage ledger, and `GovernanceStore.summarize_calibration_evidence()` now exposes the shared tenant-scoped outcome-evidence contract from S01. The missing piece is wiring that summary into live request-time routing and persisting the exact outcome-grounded factors on the same request row.

The key implementation constraint is parity discipline from D049 and S01’s forward intelligence: do not hand-roll a second evidence classifier or a second score vocabulary. Live routing should consume `calibration_summary` once, convert it into additional bounded score components in `RouterService`, and persist those factors through the already-existing `RouteDecision.signals -> CompletionMetadata.route_signals -> UsageLedgerRecord.route_signals` path. This satisfies R073 and R075 while preserving S03’s replay seam. The `verify-before-complete` skill is relevant here as process discipline: planner/executor should treat backend test evidence as mandatory before claiming the slice is done.

## Recommendation

Implement S02 in three moves:

1. **Extend the router contract first** so `RouterService` accepts an optional outcome-evidence input for live routing and emits typed additive score factors plus an explicit per-request route mode/state explanation. Keep the score bounded and additive; do not branch into a new rule tree.
2. **Resolve and inject tenant evidence in `PolicyService.evaluate()`** immediately before live route choice. `PolicyService` already has the tenant context and is the narrowest runtime seam that can fetch `GovernanceStore.summarize_calibration_evidence()` without leaking store concerns into `ChatService`.
3. **Prove persistence through existing request/ledger seams** with request-level tests (`POST /v1/chat/completions` + ledger fetch) and service-level tests that a real request can route differently because of recent tenant evidence, and that the correlated ledger row records the actual factors used.

This approach follows the existing codebase pattern from earlier calibrated routing work (see memory MEM035/MEM034): shared router contract first, then policy/runtime wiring, then persistence proof. It also preserves R078’s anti-sprawl guardrail by keeping everything on the current `route_signals`/usage-ledger/public-header seams instead of inventing a new API family.

## Implementation Landscape

### Key Files

- `src/nebula/services/router_service.py` — authoritative additive routing contract today. `CalibratedScoreBreakdown` and `_signals_from_breakdown()` are the natural extension points for outcome-grounded factors. `choose_target_with_reason()` currently only uses prompt heuristics; this is where live outcome evidence must influence the decision.
- `src/nebula/services/policy_service.py` — central runtime decision seam. `evaluate()` is where live requests become `RouteDecision`s and where tenant policy, budget checks, and gating already apply. Best place to fetch `GovernanceStore.summarize_calibration_evidence()` for live requests and pass the result to the router.
- `src/nebula/services/governance_store.py` — already owns `summarize_calibration_evidence()` and `record_usage()`. No second summarizer should be created. If route-factor persistence needs no schema change, only consume existing summary output here; if new lookup helpers are needed, they belong here, not in router code.
- `src/nebula/models/governance.py` — `CalibrationEvidenceSummary` / `OutcomeEvidenceState` already define the shared vocabulary from S01. If S02 needs structured request-level factor typing beyond ad-hoc dicts, this is the place to add serializable literals/helpers without widening public APIs.
- `src/nebula/services/chat_service.py` — persistence seam is already in place. `_metadata()` copies `PolicyResolution.route_decision.signals`, and `_record_usage()` writes them to `UsageLedgerRecord.route_signals`. This means S02 should mostly ride existing plumbing rather than change chat orchestration heavily.
- `src/nebula/db/models.py` — `UsageLedgerModel.route_signals` is JSON already. Good news: request-level factor persistence can likely ship without a migration unless the team decides it needs top-level dedicated columns.
- `src/nebula/api/routes/chat.py` — currently emits `X-Nebula-Route-Mode` from `route_signals.route_mode` only. If S02 wants headers for grounded/thin/stale/degraded request evidence, this is the existing public metadata seam, but avoid widening unless necessary for proof.
- `src/nebula/services/policy_simulation_service.py` — not owned by S02, but extremely important downstream constraint. It reconstructs parity from persisted `route_signals` today, including `score_components.total_score`, `route_mode`, token_count, keyword_match, and model_constraint. Any new live-only factor must be serializable here or S03 will drift.
- `tests/test_service_flows.py` — main service-level proof seam. Already has patterns for asserting route score/signals persistence, hard-budget route changes, and simulation parity. Add S02’s routing-diff and persisted-factor coverage here first.
- `tests/test_chat_completions.py` — best end-to-end public request → ledger row proof seam for R075. Existing tests already fetch `/v1/admin/usage/ledger?request_id=...` after live requests.
- `tests/test_reference_migration.py` — existing public headers ↔ ledger correlation contract. If S02 changes visible route behavior or public evidence semantics, update this proof carefully so request/ledger correlation remains authoritative.
- `tests/test_response_headers.py` — header contract guardrail for `X-Nebula-Route-Mode` and route metadata; useful if S02 changes request-time routing metadata exposure.
- `tests/support.py` — `configured_app()` runs migrations into temp sqlite DBs; integration tests can seed realistic tenant policies/ledger history without custom harness work.

### Build Order

1. **Design the request-level factor vocabulary in `router_service.py`.** Decide the minimal extra `score_components` / top-level signal fields needed to explain outcome-grounded routing (for example: evidence state, evidence counts, bounded bonuses/penalties, and whether the live route used grounded vs degraded evidence). Do this first because every downstream seam persists or replays these fields.
2. **Wire live summary lookup in `policy_service.py`.** Fetch `summarize_calibration_evidence()` for the current tenant only in live evaluation (not replay path yet), pass it into the router, and ensure explicit overrides / policy gating still short-circuit as they do today.
3. **Prove route-difference behavior in `tests/test_service_flows.py`.** Add tests where the same prompt routes one way without supporting evidence and another way with bounded recent tenant evidence. This is the core R073 proof and the highest-risk behavior change.
4. **Prove persisted-factor truth in `tests/test_chat_completions.py` (and possibly `tests/test_reference_migration.py`).** Assert the correlated ledger row records the actual new outcome-grounded factors used by the request. This closes R075 and protects the request-first evidence story.
5. **Only then adjust headers/contracts if needed.** If the persisted ledger row is sufficient for S02 proof, avoid extra header surface. If a header is needed for integrated proof, keep it additive and bounded on the existing `X-Nebula-*` seam.

### Verification Approach

- Service-level routing proof:
  - `./.venv/bin/pytest tests/test_service_flows.py -k "route_evidence or outcome_grounded or hard_budget or calibrated"`
- Public request + ledger correlation proof:
  - `./.venv/bin/pytest tests/test_chat_completions.py -k "ledger or governed or route"`
  - `./.venv/bin/pytest tests/test_reference_migration.py -k "usage_ledger or headers"`
- Header contract guardrail if metadata changes:
  - `./.venv/bin/pytest tests/test_response_headers.py -k "Route-Mode or route_signals"`
- Final backend sanity:
  - `./.venv/bin/pytest tests/test_service_flows.py tests/test_chat_completions.py tests/test_reference_migration.py tests/test_response_headers.py`
- After edits, run diagnostics on at least:
  - `src/nebula/services/router_service.py`
  - `src/nebula/services/policy_service.py`
  - `src/nebula/services/chat_service.py`
  - touched test files

## Constraints

- S01 established `GovernanceStore.summarize_calibration_evidence()` as the single authoritative summary seam; S02 should consume it, not duplicate or partially reinterpret it.
- `PolicySimulationService` already replays from persisted `route_signals`; any new runtime factor that influences live routing must be persisted in serializable form or S03 parity work will be blocked.
- `UsageLedgerModel.route_signals` is a JSON blob and governance minimization can suppress it entirely under strict policy. S02 must preserve honest degraded behavior when signals are absent later.
- `PolicyService.evaluate()` currently uses the same router path for live and replay, with replay distinguished by `ReplayRouteContext`. S02 should avoid forking completely separate scoring semantics in that method.
- Public API widening is out of scope for this milestone. Prefer internal signal enrichment plus existing headers/ledger surfaces.

## Common Pitfalls

- **Re-deriving outcome state inside the router** — Avoid duplicating S01’s summary classification logic. Consume `CalibrationEvidenceSummary.state` and counts directly.
- **Persisting only the final route, not the influencing factors** — R075 requires the actual factors used, not just the changed target/reason. Ensure the enriched `route_signals` survives `ChatService._metadata()` and ledger writes.
- **Breaking replay before S03** — If new live score math depends on non-persisted data, replay parity will become impossible. Keep factors bounded and serializable now.
- **Letting evidence summary override explicit policy/model decisions** — Existing explicit-model and policy-routing overrides in `RouterService._explicit_override_decision()` and `PolicyService` must remain authoritative.

## Open Risks

- The exact additive weights for outcome evidence are still an implementation choice. If they are too strong, S02 may route too aggressively; if too weak, tests may not prove a meaningful route change.
- There is no typed request-level route-factor model yet — only `dict[str, Any]`. The planner may choose to stay with dicts for speed or introduce small typed helpers in `models/governance.py` for safer vocabulary reuse.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| FastAPI | `wshobson/agents@fastapi-templates` | available |
| SQLAlchemy | `bobmatnyc/claude-mpm-skills@sqlalchemy-orm` | available |
| pytest | `github/awesome-copilot@pytest-coverage` | available |
| Verification discipline | `verify-before-complete` | installed |
