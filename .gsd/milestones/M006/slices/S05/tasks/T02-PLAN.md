---
estimated_steps: 6
estimated_files: 6
skills_used: []
---

# T02: Lock the assembled M006 proof path with focused backend and console verification

Tighten the strongest existing proof seams so the current worktree explicitly proves the assembled M006 story instead of relying on slice summaries alone. Prefer extending the existing targeted tests over adding a new harness, and keep assertions grounded in the same public-request-to-ledger-to-replay-to-operator order used by the new integrated proof doc.

Steps:
1. Extend the strongest backend seam in `tests/test_governance_api.py` and, only if needed, `tests/test_response_headers.py` so a calibrated runtime request is correlated through `X-Request-ID`, calibrated `X-Nebula-*` headers, the persisted usage-ledger row, and simulation parity or rollout-disabled/degraded semantics in one close-out-focused assertion path.
2. Inspect existing console tests in `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, and `console/src/components/policy/policy-page.test.tsx`; tighten only the assertions needed to preserve the integrated order and bounded roles if the new proof doc exposes wording drift or discoverability gaps.
3. Re-run the focused backend and console suites named by this slice so the integrated proof is executable in the assembled worktree, including at least one observability-sensitive assertion that the selected request remains primary while supporting context stays bounded.
4. Keep the proof bounded: no new admin routes, no broad integration harness, and no UI expansion beyond wording or assertions needed to lock the already-shipped calibrated-routing story.

## Inputs

- `tests/test_governance_api.py`
- `tests/test_response_headers.py`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `docs/m006-integrated-proof.md`

## Expected Output

- `tests/test_governance_api.py`
- `tests/test_response_headers.py`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

## Verification

./.venv/bin/pytest tests/test_response_headers.py -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x && npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

This task strengthens the proof that future agents can inspect failures or drift through existing surfaces: public request headers, request-id ledger lookup, replay changed-request fields, and selected-request-first Observability rendering. The assertions should catch if those surfaces drift out of order or start claiming broader authority.
