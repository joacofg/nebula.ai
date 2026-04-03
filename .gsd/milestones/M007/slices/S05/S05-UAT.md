# S05: Integrated operator proof and close-out — UAT

**Milestone:** M007
**Written:** 2026-04-03T02:59:12.438Z

# S05 UAT — Integrated operator proof and close-out

## Preconditions
- Repository checkout includes the assembled M007 worktree changes.
- Console test dependencies are installed (`console/node_modules` present).
- The files `docs/m007-integrated-proof.md`, `README.md`, and `docs/architecture.md` are available locally.

## Test Case 1 — Discover the integrated proof from repo entry docs
1. Open `README.md`.
   - Expected: the Documentation map includes a link to `docs/m007-integrated-proof.md` with wording that frames it as the M007 operator-surface close-out review order.
2. Open `docs/architecture.md`.
   - Expected: the request-flow overview links to `docs/m007-integrated-proof.md` in the existing integrated-proof cluster without restating the full M007 UI contract.
3. Open `docs/m007-integrated-proof.md`.
   - Expected: the document exists and is pointer-only rather than a second spec.

## Test Case 2 — Verify the integrated proof structure matches the intended review order
1. In `docs/m007-integrated-proof.md`, locate the section headings:
   - `What this integrated proof establishes`
   - `Canonical proof order`
   - `Minimal operator walkthrough`
   - `What this walkthrough intentionally does not duplicate`
   - `Failure modes this integrated proof makes obvious`
   - Expected: all five sections are present.
2. Read the `Canonical proof order` section.
   - Expected: the review path starts with selected-request-first Observability, then bounded ledger-table selection, then authoritative request detail, then compare-before-save policy preview, then policy page reset behavior, and ends with the focused Vitest seams.
3. Read the anti-drift language in the document.
   - Expected: dashboard, routing studio, analytics product, redesign-sprawl, and parallel workflow framing are called out only as scope drift or failure modes, not as product goals.

## Test Case 3 — Verify the assembled guard bundle for selected-request investigation and authoritative evidence
1. Run:
   - `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/ledger/ledger-table.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
2. Observe the Vitest result.
   - Expected: 6/6 test files pass and 39/39 tests pass.
3. Review the included test files conceptually.
   - Expected: Observability tests cover selected-request-first hierarchy and supporting-context boundaries; ledger tests cover bounded current-investigation selection plus authoritative request detail; policy tests cover compare-before-save, explicit non-save preview semantics, and stale-preview reset behavior.

## Test Case 4 — Edge-case verification: close-out proof stays pointer-only and does not duplicate contracts
1. Skim `docs/m007-integrated-proof.md` for long-form UI copy snapshots or redefined component contracts.
   - Expected: the doc points to `page.tsx`, `ledger-table.tsx`, `ledger-request-detail.tsx`, `policy-form.tsx`, `policy/page.tsx`, and the focused test files instead of duplicating their implementation details.
2. Check that the document still provides a usable review order.
   - Expected: a reviewer can follow the proof from top-level Observability composition through bounded selection, authoritative detail, policy decision flow, and focused tests without needing additional slice-history context.

## Test Case 5 — Edge-case verification: no extra guard churn was required to keep the story true
1. Compare the S05 result against the focused six-file bundle outcome.
   - Expected: the bundle passes without additional test edits in this slice.
2. Read the slice summary narrative for T02.
   - Expected: it states that tests were left unchanged because the existing assembled guard bundle already proved the operator-proof order without drift.

## Acceptance outcome
- Accept S05 only if the integrated proof doc is discoverable from both top-level docs, preserves the strict selected-request-first → authoritative-detail → compare-before-save review order, and the exact six-file focused Vitest bundle passes unchanged with all 39 tests green.
