# S05: Integrated proof and close-out

**Goal:** Close M009 with one pointer-first integrated proof and executable happy/degraded verification seams that show public request -> persisted request evidence -> replay parity -> request-first operator inspection without widening scope beyond existing runtime, admin, and console surfaces.
**Demo:** After this: one review path proves public request → persisted request evidence → replay parity → request-first operator inspection for both a happy path and a degraded path, with anti-drift boundaries locked in docs and tests.

## Must-Haves

- `docs/m009-integrated-proof.md` exists and mirrors Nebula's pointer-first close-out style for one happy path and one degraded review path.
- `docs/route-decision-vocabulary.md` and `docs/architecture.md` reference the M009 outcome-grounded proof and vocabulary without duplicating contracts inline.
- Backend tests explicitly prove a happy-path chain from public request headers to persisted ledger evidence to unchanged-policy replay parity using existing request/ledger/admin seams.
- Backend and console tests explicitly prove the degraded path stays honest and selected-request-first rather than inventing a new analytics or replay-only story.
- No new API surface, dashboard, hosted-authority behavior, or replay-only vocabulary is introduced.

## Proof Level

- This slice proves: - This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Integration Closure

Upstream surfaces consumed: `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_governance_api.py`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, `docs/m006-integrated-proof.md`, `docs/m007-integrated-proof.md`, `docs/m008-integrated-proof.md`, `docs/route-decision-vocabulary.md`, `docs/architecture.md`. New wiring introduced in this slice: a new discoverable integrated-proof document for M009 plus additive documentation/test assertions that explicitly bind the happy-path and degraded-path review order to the already-shipped runtime, replay, and selected-request-first seams. What remains before the milestone is truly usable end-to-end: nothing once the integrated proof doc, vocabulary discoverability updates, and focused backend/console verification all pass.

## Verification

- Failure diagnosis remains request-first. The selected request row, response headers, replay payloads, and existing Observability request detail stay the canonical inspection surfaces; this slice only tightens tests and docs so future drift is caught where operators already look.

## Tasks

- [x] **T01: Write the M009 integrated proof and discoverability links** `est:45m`
  Write the M009 close-out proof in the same pointer-first style as M006-M008 and make the shared vocabulary/discoverability references sufficient so the doc does not need to define outcome-grounded fields inline. Keep the doc anchored to the existing seams only: route vocabulary, one live `POST /v1/chat/completions` request, correlated `GET /v1/admin/usage/ledger?request_id=...` row, `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, and selected-request-first Observability/request detail. Additive doc changes only; do not invent a new API, dashboard, or hosted role.
  - Files: `docs/m009-integrated-proof.md`, `docs/route-decision-vocabulary.md`, `docs/architecture.md`, `docs/m006-integrated-proof.md`, `docs/m007-integrated-proof.md`, `docs/m008-integrated-proof.md`
  - Verify: python - <<'PY'
from pathlib import Path
proof = Path('docs/m009-integrated-proof.md')
text = proof.read_text()
assert proof.exists()
assert text.count('## ') >= 6
for needle in [
    'POST /v1/chat/completions',
    'GET /v1/admin/usage/ledger?request_id=...',
    'POST /v1/admin/tenants/{tenant_id}/policy/simulate',
    'happy path',
    'degraded path',
    'selected-request-first',
]:
    assert needle in text, needle
vocab = Path('docs/route-decision-vocabulary.md').read_text()
for needle in ['outcome_bonus', 'evidence_penalty', 'outcome_evidence']:
    assert needle in vocab, needle
arch = Path('docs/architecture.md').read_text()
assert 'docs/m009-integrated-proof.md' in arch
assert 'TODO' not in text and 'TBD' not in text
PY

- [x] **T02: Lock the happy-path and degraded backend proof chain** `est:1h`
  Tighten the backend proof seams so one happy-path scenario and one degraded-path scenario each explicitly support the final integrated walkthrough. Reuse the existing request, header, ledger, and simulation tests rather than adding a new orchestration API or synthetic proof harness. Happy-path assertions should bind live response headers, persisted `route_signals.outcome_evidence`, and unchanged-policy replay parity for the same request shape. Degraded-path assertions should keep replay honesty explicit when persisted route signals are incomplete and preserve the anti-sprawl boundary by proving missing-route-signal handling rather than adding a replay-only contract.
  - Files: `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_governance_api.py`
  - Verify: ./.venv/bin/pytest tests/test_chat_completions.py -k "outcome_grounded or ledger or policy_denied" && ./.venv/bin/pytest tests/test_response_headers.py -k "route_mode or route_signals" && ./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or usage_ledger)"

- [x] **T03: Harden request-first console proof for degraded inspection** `est:45m`
  Tighten the request-first console proof so the final walkthrough can point to exact operator seams for both grounded and degraded review paths. Reuse the current request-detail and Observability suites; add only the assertions needed to prove the degraded path still keeps the selected request row authoritative while tenant calibration summary remains supporting context. Do not add a new dashboard/workflow or browser-only proof path.
  - Files: `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`
  - Verify: npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx' && npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' && npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'

## Files Likely Touched

- docs/m009-integrated-proof.md
- docs/route-decision-vocabulary.md
- docs/architecture.md
- docs/m006-integrated-proof.md
- docs/m007-integrated-proof.md
- docs/m008-integrated-proof.md
- tests/test_chat_completions.py
- tests/test_response_headers.py
- tests/test_governance_api.py
- console/src/components/ledger/ledger-request-detail.test.tsx
- console/src/app/(console)/observability/page.test.tsx
- console/src/app/(console)/observability/observability-page.test.tsx
