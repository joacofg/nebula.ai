# S05: Integrated proof and close-out — UAT

**Milestone:** M006
**Written:** 2026-04-02T13:26:08.438Z

# S05 UAT — Integrated proof and close-out

## Preconditions
- The assembled M006 worktree is available with backend and console dependencies installed.
- Python virtualenv exists at `./.venv`.
- Console test runner dependencies are installed under `console/node_modules`.
- The reviewer can read repository docs and run the focused verification commands from the repo root.

## Test Case 1 — Discover the integrated M006 proof from repo entry points
1. Open `README.md`.
   - Expected: the documentation map includes `docs/m006-integrated-proof.md` and describes it as the pointer-only calibrated-routing close-out review path.
2. Open `docs/architecture.md`.
   - Expected: the request-flow overview links to `docs/m006-integrated-proof.md` alongside other canonical proof docs, without restating calibrated-routing contract details inline.
3. Open `docs/m006-integrated-proof.md`.
   - Expected: the document is non-empty, contains no `TODO` or `TBD`, and presents the proof as an integrated walkthrough rather than a second contract.

## Test Case 2 — Verify the proof order is explicit and bounded
1. In `docs/m006-integrated-proof.md`, inspect the `Canonical proof order` and `Minimal operator walkthrough` sections.
   - Expected: the order is explicit and preserved as `docs/route-decision-vocabulary.md` → public `POST /v1/chat/completions` → calibrated `X-Nebula-*` plus `X-Request-ID` → `GET /v1/admin/usage/ledger?request_id=...` → `POST /v1/admin/tenants/{tenant_id}/policy/simulate` → selected-request-first Observability.
2. Inspect the `What this walkthrough intentionally does not duplicate` section.
   - Expected: the doc says it does not duplicate detailed contracts, route implementations, full UI behavior, or full executable assertions.
3. Inspect the `Failure modes this integrated proof makes obvious` section.
   - Expected: scope drift is called out explicitly, including analytics-product drift, hidden tuning authority, hosted/public scope expansion, or Observability becoming more authoritative than selected request evidence.

## Test Case 3 — Mechanical proof integrity check
1. Run:
   ```bash
   ./.venv/bin/python - <<'PY'
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
   ```
   - Expected: command exits 0.
2. Run:
   ```bash
   rg -n "m006-integrated-proof|route-decision-vocabulary|X-Request-ID|X-Nebula-|/v1/admin/usage/ledger|policy/simulate|Observability|does not duplicate|failure modes" README.md docs/architecture.md docs/m006-integrated-proof.md
   ```
   - Expected: matches appear in all three files, confirming proof discoverability and required seams.

## Test Case 4 — Backend close-out proof remains executable
1. Run:
   ```bash
   ./.venv/bin/pytest tests/test_response_headers.py -x
   ```
   - Expected: the suite passes and proves the public response still exposes calibrated routing metadata through `X-Nebula-*` headers.
2. Run:
   ```bash
   ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x
   ```
   - Expected: the targeted governance test passes and proves one calibrated runtime request can be correlated from `X-Request-ID` through the persisted usage-ledger row into replay changed-request parity, including the bounded rollout-disabled case after policy flip.

## Test Case 5 — Operator-surface framing stays selected-request-first and bounded
1. Run:
   ```bash
   npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx
   ```
   - Expected: all three test files pass.
2. Review the passing assertions in the targeted test files.
   - Expected: Observability keeps the selected persisted request primary, duplicate calibration labels are only tolerated when scoped to bounded cards, and policy replay preview remains a compact changed-request sample rather than a broader analytics or tuning surface.

## Edge Cases
- If the mechanical Python check fails because `python` is not available on PATH, rerun it with `./.venv/bin/python`; this is an environment-path issue, not product drift.
- If the governance test fails because header values or replay changed-request fields no longer align to the persisted runtime row, treat that as integrated-proof regression rather than a documentation issue.
- If the console tests fail because Observability wording becomes page-global, analytics-like, or more authoritative than the selected request evidence, treat that as M006 scope drift.
- If README or architecture links exist but `docs/m006-integrated-proof.md` starts restating detailed request or UI contracts, treat that as a duplication regression even if the tests still pass.

