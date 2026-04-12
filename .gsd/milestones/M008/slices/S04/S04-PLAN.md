# S04: Operator evidence-boundary surfaces

**Goal:** Make the policy and request-detail console surfaces explain Nebula’s effective evidence boundary using the already-persisted governance fields, while keeping hosted trust-boundary wording visibly aligned with the metadata-only contract.
**Demo:** The policy page and request-detail surface clearly show the effective evidence boundary, including what is retained, suppressed, or no longer available due to policy.

## Must-Haves

- The policy surface presents an explicit effective evidence boundary summary derived from `evidence_retention_window` and `metadata_minimization_level`, including what is retained while a row exists, what strict minimization suppresses today, and that hosted export stays metadata-only.
- The request-detail surface explains the selected row’s retained, suppressed, and deletion semantics using persisted row-level governance markers without implying soft-delete, archive recovery, or hosted raw export.
- Hosted trust-boundary wording remains schema-backed and visibly consistent with the operator evidence vocabulary introduced on the policy and request-detail seams.
- Focused console tests and hosted-contract regression prove the copy matches real runtime behavior and does not widen scope into a dashboard, archive system, or hosted authority surface.

## Proof Level

- This slice proves: integration

## Integration Closure

This slice composes existing tenant-policy controls, persisted usage-ledger markers, and hosted trust-boundary copy into one operator-readable evidence story. After it lands, S05 can use the already-running policy → persistence → deletion → operator surface → hosted boundary chain without adding new API surface.

## Verification

- Runtime signals: operator-visible boundary summaries on the policy page, request-detail panel, and hosted trust page.
- Inspection surfaces: `console/src/components/policy/policy-form.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/hosted/trust-boundary-card.tsx`, and their focused tests.
- Failure visibility: wording drift shows up as failing Vitest assertions or mismatched hosted-contract regression rather than latent ambiguity.
- Redaction constraints: copy must stay bounded to persisted governance markers and schema-backed hosted metadata; no raw prompt/response or secret-bearing surfaces may be introduced.

## Tasks

- [x] **T01: Add policy-side effective evidence boundary guidance** `est:45m`
  Add a bounded operator-facing explanation to the policy surface that synthesizes the runtime-enforced governance controls already present in `console/src/components/policy/policy-form.tsx`. Reuse the existing `evidence_retention_window` and `metadata_minimization_level` values plus the shared hosted contract copy from `console/src/lib/hosted-contract.ts` to explain, in explicit operator language, what evidence remains inspectable while a row exists, what strict minimization suppresses today, and that hosted export still excludes raw usage-ledger rows. Keep this explanatory surface subordinate to the existing runtime-enforced controls rather than turning the page into a second observability/dashboard seam. Update focused policy tests to lock the new boundary vocabulary and verify that the page still distinguishes runtime-enforced controls from advisory capture settings.
  - Files: `console/src/components/policy/policy-form.tsx`, `console/src/components/policy/policy-form.test.tsx`, `console/src/components/policy/policy-page.test.tsx`, `console/src/lib/hosted-contract.ts`
  - Verify: npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

- [x] **T02: Align request-detail and hosted trust-boundary copy with the same evidence vocabulary** `est:45m`
  Extend the request-detail evidence surface so a selected persisted row explains the effective evidence boundary with the same retained/suppressed/deleted/not-hosted vocabulary introduced on the policy page. Keep the selected ledger row authoritative while it exists, explicitly distinguish row-level persisted truth from broader hosted-boundary guidance, and do not imply recovery, soft-delete, or hosted raw export. If the existing trust-boundary card/page needs reinforcement, make only small shared-copy updates through `console/src/lib/hosted-contract.ts` and the existing hosted components/tests so hosted wording remains metadata-only and schema-backed. Add or update request-detail and hosted tests to prove row-level governance markers remain legible while present and that hosted surfaces still exclude raw usage-ledger export or runtime authority claims.
  - Files: `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/components/hosted/trust-boundary-card.tsx`, `console/src/components/hosted/trust-boundary-card.test.tsx`, `console/src/app/trust-boundary/page.tsx`, `console/src/app/trust-boundary/page.test.tsx`, `console/src/lib/hosted-contract.ts`
  - Verify: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx && ./.venv/bin/pytest tests/test_hosted_contract.py

## Files Likely Touched

- console/src/components/policy/policy-form.tsx
- console/src/components/policy/policy-form.test.tsx
- console/src/components/policy/policy-page.test.tsx
- console/src/lib/hosted-contract.ts
- console/src/components/ledger/ledger-request-detail.tsx
- console/src/components/ledger/ledger-request-detail.test.tsx
- console/src/components/hosted/trust-boundary-card.tsx
- console/src/components/hosted/trust-boundary-card.test.tsx
- console/src/app/trust-boundary/page.tsx
- console/src/app/trust-boundary/page.test.tsx
