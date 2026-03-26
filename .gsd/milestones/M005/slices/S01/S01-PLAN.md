# S01: Adaptive routing model

**Goal:** Nebula has an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current heuristic.
**Demo:** A real request routed through the gateway carries `route_signals` in the ledger, `X-Nebula-Route-Score` in the response headers, and the Observability drawer shows a "Route Decision" section with plain-language signal labels. Unit tests prove signal computation; an integration test proves end-to-end ledger persistence.

## Must-Haves

- R039 is addressed by enriching `RouteDecision` with `signals` and `score`, replacing the char-count heuristic with token-estimate-based complexity tiering, threading policy context (budget proximity, model constraints) through `PolicyService`, and persisting the signal payload to `usage_ledger.route_signals`.
- Every heuristic routing path (`"token_complexity"`) populates `signals` with `token_count`, `complexity_tier`, `budget_proximity`, `model_constraint`, and `keyword_match` keys, and `score` as a normalised float.
- The usage ledger has a new `route_signals JSON NULL` column added via an idempotent Alembic migration.
- `X-Nebula-Route-Score` header is emitted alongside the existing route headers on every response.
- The Observability request-detail drawer renders a "Route Decision" section when `route_signals` is non-null, using plain-language labels.
- `docs/route-decision-vocabulary.md` documents the stable signal vocabulary and reason codes so S02 simulation can reference them.

## Proof Level

- This slice proves: contract + integration
- Real runtime required: no (integration test uses configured_app() with StubProvider and in-memory DB)
- Human/UAT required: yes (visual inspection of the Observability drawer — see Manual Verifications below)

## Verification

```bash
# Unit and integration tests
pytest tests/test_router_signals.py -x

# Full suite (wave gate)
make test

# Console component
npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx

# Vocabulary doc present
test -f docs/route-decision-vocabulary.md

# Signals persisted through existing test paths
pytest tests/test_chat_completions.py tests/test_admin.py tests/test_governance.py -x
```

## Observability / Diagnostics

- Runtime signals: `pytest tests/test_router_signals.py -x` — fails fast on any signal computation or persistence regression
- Inspection surfaces: `src/nebula/services/router_service.py` (signal computation), `src/nebula/services/governance_store.py` (ledger write), `migrations/versions/20260326_0006_route_signals.py` (schema), `console/src/components/ledger/ledger-request-detail.tsx` (UI)
- Failure visibility: unit test names map directly to signal keys; integration tests assert on ledger column presence; console test asserts on rendered text
- Redaction constraints: none — route signals are routing metadata only, not request content

## Integration Closure

- Upstream surfaces consumed: `RouterService.choose_target_with_reason()`, `PolicyService.resolve()`, `GovernanceStore.record_usage()`, `_nebula_headers()`, `LedgerRequestDetail`
- New wiring introduced: `RouteDecision.signals + score` → `CompletionMetadata.route_signals + route_score` → `UsageLedgerRecord.route_signals` → `usage_ledger.route_signals` (DB) and `X-Nebula-Route-Score` header; `UsageLedgerRecord.route_signals` → TypeScript type → `LedgerRequestDetail` drawer section
- What remains before the milestone is truly usable end-to-end: S02 can now replay ledger-backed requests through candidate routing changes because `route_signals` provides a stable signal payload; S03 can reuse the `budget_proximity` signal for hard guardrail semantics

## Tasks

- [ ] **T01: Enrich RouteDecision and RouterService with signal model** `wave:1` `est:45m`
  - Why: The entire slice depends on `RouteDecision` carrying structured signal data. This is the root seam — all other seams consume what T01 produces.
  - Files: `src/nebula/services/router_service.py`, `src/nebula/services/policy_service.py`
  - Do: Add `signals: dict[str, Any]` and `score: float` to `RouteDecision` (frozen dataclass, use `field(default_factory=dict)`); add `_estimate_token_count()` module-level helper (`ceil(len(text) / 4)`); rewrite heuristic routing to compute token count, complexity tier (low/medium/high at 500/2000 thresholds), `model_constraint`, `keyword_match` signals and a normalised score; replace old reason codes `"simple_prompt"` and `"prompt_length"` with `"token_complexity"`; add optional `policy: TenantPolicy | None = None` parameter to `choose_target_with_reason()`; update `PolicyService.resolve()` to pass `policy=policy` in the router call. **Wave 0 first:** create `tests/test_router_signals.py` with stub test functions for all R039 test IDs listed in S01-VALIDATION.md — run them red before touching production code.
  - Verify: `pytest tests/test_router_signals.py::test_route_decision_carries_signals tests/test_router_signals.py::test_token_count_signal_from_prompt tests/test_router_signals.py::test_budget_proximity_signal tests/test_router_signals.py::test_model_constraint_signal tests/test_router_signals.py::test_score_by_complexity_tier -x`
  - Done when: All five unit tests pass; `RouteDecision` has `signals` and `score` with safe defaults; `"prompt_length"` and `"simple_prompt"` do not appear in `router_service.py`; existing test suite (`pytest tests/test_chat_completions.py -x`) stays green.

- [ ] **T02: Add route_signals to ledger and wire through chat_service** `wave:1` `est:1h`
  - Why: Signal data is only useful if it persists. The ledger column enables S02 replay; the header enables client-side observability.
  - Files: `src/nebula/db/models.py`, `src/nebula/models/governance.py`, `src/nebula/services/governance_store.py`, `src/nebula/services/chat_service.py`, `src/nebula/api/routes/chat.py`, `migrations/versions/20260326_0006_route_signals.py`
  - Do: Add `route_signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)` to `UsageLedgerModel`; add `route_signals: dict[str, Any] | None = None` to `UsageLedgerRecord`; create idempotent Alembic migration `20260326_0006_route_signals.py` (revision chain `20260322_0005` → `20260326_0006`) using the `inspector.get_columns` guard pattern from prior migrations; add `route_signals: dict[str, Any] | None` and `route_score: float = 0.0` fields to `CompletionMetadata`; populate both from `policy_resolution.route_decision` in `_metadata()`; pass `route_signals=metadata.route_signals` in `_record_usage()`; update `GovernanceStore.record_usage()` and `_usage_from_model()` to handle the column; add `X-Nebula-Route-Score: f"{metadata.route_score:.4f}"` to `_nebula_headers()`.
  - Verify: `pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger tests/test_router_signals.py::test_route_score_header -x`
  - Done when: Both integration tests pass; migration file exists with idempotent guard and correct `down_revision`; `X-Nebula-Route-Score` header present in responses; existing test suite green.

- [ ] **T03: Observability drawer extension and route-decision vocabulary doc** `wave:2` `est:45m`
  - Why: Signal data recorded in T02 must surface to operators to close the interpretability goal. The vocabulary doc is required before S02 references the stable decision model.
  - Files: `console/src/lib/admin-api.ts`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `docs/route-decision-vocabulary.md`
  - Do: Add `route_signals: Record<string, unknown> | null` to the `UsageLedgerRecord` TypeScript type in `admin-api.ts`; extend `LedgerRequestDetail` with a conditional `<section>` rendered when `entry.route_signals !== null` showing token count, complexity tier, keyword match, model constraint, score, and reason code using plain-language labels via the existing `<DetailRow>` pattern; add a Vitest test case asserting the "Route Decision" section renders correctly and is absent when `route_signals` is null; write `docs/route-decision-vocabulary.md` documenting all signal keys, reason codes, and their plain-language meanings.
  - Verify: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx && test -f docs/route-decision-vocabulary.md`
  - Done when: Console test passes (section renders with labels; absent when null); TypeScript compiles without error; vocabulary doc exists and covers all signal keys and reason codes defined in T01.

## Files Likely Touched

- `src/nebula/services/router_service.py`
- `src/nebula/services/policy_service.py`
- `src/nebula/services/chat_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/db/models.py`
- `src/nebula/models/governance.py`
- `src/nebula/api/routes/chat.py`
- `migrations/versions/20260326_0006_route_signals.py`
- `tests/test_router_signals.py` (new)
- `console/src/lib/admin-api.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `docs/route-decision-vocabulary.md` (new)

## Manual Verifications

| Behavior | Why Manual |
|----------|------------|
| Observability drawer shows "Route Decision" section with plain-language labels (Token count: N, Complexity tier: low/medium/high, etc.) | UI rendering requires visual inspection in a running console |

To verify manually: run `make selfhost-up`, send a request to the gateway, open the Observability page, click a request row, expand the detail drawer, confirm the "Route Decision" section appears with labelled signal values.

## Wave Structure

| Wave | Tasks | Depends on |
|------|-------|------------|
| 0 | (Wave 0 step inside T01) Create `tests/test_router_signals.py` stub | — |
| 1 | T01, T02 | Wave 0 |
| 2 | T03 | T01 + T02 |
