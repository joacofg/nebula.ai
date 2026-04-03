# S05: Integrated operator proof and close-out

**Goal:** Assemble and verify one pointer-only operator proof path that shows selected-request-first Observability, authoritative request detail, and compare-before-save policy preview work together as a coherent decision system without drifting into dashboard, routing-studio, or analytics-product scope.
**Demo:** After this: After this: one integrated proof path shows the clarified operator surfaces work together as a coherent decision system without dashboard drift or redesign sprawl.

## Tasks
- [x] **T01: Added the pointer-only M007 integrated proof and linked it from README and architecture docs.** — Create the pointer-only M007 close-out walkthrough and link it from the repo’s main discoverability docs so reviewers can follow one strict operator proof order without treating the new doc as a second spec.

Steps:
1. Read `docs/m006-integrated-proof.md` and `docs/v4-integrated-proof.md` as the canonical pointer-only pattern, then draft `docs/m007-integrated-proof.md` around the M007 review order: selected-request-first Observability, authoritative request detail, compare-before-save policy preview, and explicit anti-drift scope conclusion.
2. Keep the new doc composition-first and pointer-only: point to `console/src/app/(console)/observability/page.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-table.tsx`, `console/src/components/policy/policy-form.tsx`, `console/src/app/(console)/policy/page.tsx`, and the focused Vitest files instead of restating contracts or long UI copy.
3. Update `README.md` and `docs/architecture.md` to include discoverability links to `docs/m007-integrated-proof.md` in the same style as prior integrated proof entries, without expanding those docs into another explanation surface.
4. Sanity-check the new wording against M007 scope boundaries: no dashboard, routing studio, analytics product, redesign-sprawl, or parallel workflow framing should appear as positive product claims.
  - Estimate: 45m
  - Files: docs/m007-integrated-proof.md, README.md, docs/architecture.md, docs/m006-integrated-proof.md, docs/v4-integrated-proof.md
  - Verify: python - <<'PY'
from pathlib import Path
proof = Path('docs/m007-integrated-proof.md')
assert proof.exists() and proof.stat().st_size > 0
text = proof.read_text()
for needle in [
    'What this integrated proof establishes',
    'Canonical proof order',
    'Minimal operator walkthrough',
    'What this walkthrough intentionally does not duplicate',
    'Failure modes this integrated proof makes obvious',
]:
    assert needle in text, needle
for path in ['README.md', 'docs/architecture.md']:
    assert 'docs/m007-integrated-proof.md' in Path(path).read_text(), path
PY
- [ ] **T02: Run assembled close-out verification and tighten cross-surface guards only if needed** — Use the integrated proof order to re-run the focused console verification bundle and only touch tests if the assembled story reveals a real missing guard across Observability, request detail, ledger selection, and policy preview/page seams.

Steps:
1. Run the focused Vitest bundle covering `page.test.tsx`, `observability-page.test.tsx`, `ledger-request-detail.test.tsx`, `ledger-table.test.tsx`, `policy-form.test.tsx`, and `policy-page.test.tsx` to prove the assembled operator story in the shipped worktree.
2. Compare any failure or uncovered gap against the new integrated proof doc and prior slice summaries before editing: only add or tighten assertions when the gap is real integrated-proof drift, not because the slice needs extra churn.
3. If changes are required, keep them scoped to the relevant test file and assert the specific cross-surface boundary at risk: request-first ordering, request-detail authority, policy-preview next-step guidance, bounded selector semantics, or anti-drift language.
4. Re-run the same focused Vitest bundle until it passes cleanly and leaves a narrow, code-backed close-out proof for M007.
  - Estimate: 45m
  - Files: console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/components/ledger/ledger-request-detail.test.tsx, console/src/components/ledger/ledger-table.test.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx, docs/m007-integrated-proof.md
  - Verify: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/ledger/ledger-table.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
