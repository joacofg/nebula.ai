# S05: Integrated proof and close-out

**Goal:** Assemble one pointer-only integrated M006 proof path and focused close-out verification that show calibrated live routing, request-id-to-ledger correlation, replay parity, bounded degraded or rollout-disabled semantics, and selected-request-first operator inspection all agree without widening Nebula beyond the existing calibrated-routing scope.
**Demo:** After this: After this: one integrated proof path demonstrates calibrated live routing, replay parity, degraded fallback, operator inspection, and milestone scope discipline end-to-end.

## Tasks
- [x] **T01: Added the pointer-only M006 integrated proof and linked it from README and architecture.** — Create the final calibrated-routing close-out artifact that joins the canonical M006 proof seams without redefining their contracts. Follow the structure of `docs/v4-integrated-proof.md` and `docs/embeddings-integrated-adoption-proof.md`, keep the document composition-first, and add only pointer-level discoverability updates in `README.md` and `docs/architecture.md`.

Steps:
1. Add a new M006 integrated proof doc in `docs/` that states what the assembled proof establishes, the strict proof order, how canonical sources fit together, a minimal operator walkthrough, what the document intentionally does not duplicate, and the failure modes that would reveal scope or proof drift.
2. Keep the proof order explicit and grounded in shipped seams: `docs/route-decision-vocabulary.md`, the public `POST /v1/chat/completions` path and calibrated `X-Nebula-*` / `X-Request-ID` headers, `GET /v1/admin/usage/ledger?request_id=...`, `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, the selected-request-first Observability/request-detail surfaces, and bounded degraded or rollout-disabled semantics.
3. Update `README.md` and `docs/architecture.md` only to add discoverability pointers to the new integrated proof artifact while preserving the existing rule that detailed routing, replay, and operator-surface semantics stay in their canonical docs and code-backed seams.
4. Verify the artifact and links mechanically so the document is present, non-empty, and references the required proof seams without introducing TODO or TBD placeholders.
  - Estimate: 45m
  - Files: docs/m006-integrated-proof.md, README.md, docs/architecture.md, docs/v4-integrated-proof.md, docs/embeddings-integrated-adoption-proof.md, docs/route-decision-vocabulary.md
  - Verify: python - <<'PY'
from pathlib import Path
paths = [Path('docs/m006-integrated-proof.md'), Path('README.md'), Path('docs/architecture.md')]
for path in paths:
    assert path.exists(), f'missing {path}'
    assert path.read_text().strip(), f'empty {path}'
proof = Path('docs/m006-integrated-proof.md').read_text()
required = [
    'route-decision-vocabulary',
    'POST /v1/chat/completions',
    'X-Request-ID',
    'X-Nebula-',
    '/v1/admin/usage/ledger',
    'policy/simulate',
    'Observability',
    'does not duplicate',
    'failure modes',
]
for token in required:
    assert token in proof, f'missing {token}'
assert 'TODO' not in proof and 'TBD' not in proof
PY
rg -n "m006-integrated-proof|route-decision-vocabulary|X-Request-ID|X-Nebula-|/v1/admin/usage/ledger|policy/simulate|Observability|does not duplicate|failure modes" README.md docs/architecture.md docs/m006-integrated-proof.md
- [x] **T02: Locked the assembled M006 proof path with focused backend and console verification.** — Tighten the strongest existing proof seams so the current worktree explicitly proves the assembled M006 story instead of relying on slice summaries alone. Prefer extending the existing targeted tests over adding a new harness, and keep assertions grounded in the same public-request-to-ledger-to-replay-to-operator order used by the new integrated proof doc.

Steps:
1. Extend the strongest backend seam in `tests/test_governance_api.py` and, only if needed, `tests/test_response_headers.py` so a calibrated runtime request is correlated through `X-Request-ID`, calibrated `X-Nebula-*` headers, the persisted usage-ledger row, and simulation parity or rollout-disabled/degraded semantics in one close-out-focused assertion path.
2. Inspect existing console tests in `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, and `console/src/components/policy/policy-page.test.tsx`; tighten only the assertions needed to preserve the integrated order and bounded roles if the new proof doc exposes wording drift or discoverability gaps.
3. Re-run the focused backend and console suites named by this slice so the integrated proof is executable in the assembled worktree, including at least one observability-sensitive assertion that the selected request remains primary while supporting context stays bounded.
4. Keep the proof bounded: no new admin routes, no broad integration harness, and no UI expansion beyond wording or assertions needed to lock the already-shipped calibrated-routing story.
  - Estimate: 1h
  - Files: tests/test_governance_api.py, tests/test_response_headers.py, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/components/policy/policy-page.test.tsx, docs/m006-integrated-proof.md
  - Verify: ./.venv/bin/pytest tests/test_response_headers.py -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x && npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx
