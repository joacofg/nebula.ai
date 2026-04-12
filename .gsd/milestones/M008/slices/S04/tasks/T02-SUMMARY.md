---
id: T02
parent: S04
milestone: M008
key_files:
  - console/src/lib/hosted-contract.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/components/hosted/trust-boundary-card.tsx
  - console/src/components/hosted/trust-boundary-card.test.tsx
  - console/src/app/trust-boundary/page.tsx
  - console/src/app/trust-boundary/page.test.tsx
  - console/src/lib/hosted-contract.test.ts
key_decisions:
  - Centralized retained/suppressed/deleted/not-hosted wording in `console/src/lib/hosted-contract.ts` so request-detail and hosted trust-boundary surfaces stay aligned to one metadata-only contract instead of duplicating strings.
duration: 
verification_result: passed
completed_at: 2026-04-12T17:18:19.717Z
blocker_discovered: false
---

# T02: Aligned request-detail and hosted trust-boundary surfaces to the same retained/suppressed/deleted/not-hosted evidence vocabulary.

**Aligned request-detail and hosted trust-boundary surfaces to the same retained/suppressed/deleted/not-hosted evidence vocabulary.**

## What Happened

Updated `console/src/lib/hosted-contract.ts` to add a shared `evidenceBoundaryVocabulary` contract alongside the existing metadata-only hosted guidance, with validation that the retained/suppressed/deleted/not-hosted phrases continue to reject soft-delete, raw usage-ledger export, and hosted runtime-authority drift. Used that shared vocabulary in `console/src/components/ledger/ledger-request-detail.tsx` to add an explicit “Effective evidence boundary” panel that keeps the selected persisted ledger row authoritative while it exists, explains suppressed metadata as no longer available from the ledger, explains deletion as full row removal at expiration, and states that hosted cannot replace local row-level evidence. Reinforced the same vocabulary on hosted surfaces by rendering it in `console/src/components/hosted/trust-boundary-card.tsx` and the public `console/src/app/trust-boundary/page.tsx`, keeping the hosted message metadata-only and schema-backed rather than introducing ad hoc copy. Expanded the focused console tests plus the shared hosted-contract unit test so wording drift, duplicate-vocabulary regressions, and hosted raw-export/runtime-authority claims fail fast in Vitest, while the existing Python hosted contract checks continue guarding schema-backed exclusions.

## Verification

Ran the focused verification command from the task plan, expanded to include the shared hosted-contract unit test that now guards the new shared vocabulary: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/lib/hosted-contract.test.ts && ./.venv/bin/pytest tests/test_hosted_contract.py`. Vitest passed all 44 assertions across the request-detail, hosted card, trust-boundary page, and contract module; pytest passed all 11 hosted-contract backend checks. This directly verifies the two operator inspection surfaces called out in the slice observability contract and confirms hosted surfaces still exclude raw usage-ledger export or runtime authority claims.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/lib/hosted-contract.test.ts` | 0 | ✅ pass | 639ms |
| 2 | `./.venv/bin/pytest tests/test_hosted_contract.py` | 0 | ✅ pass | 760ms |

## Deviations

Expanded the console-side verification set to include `console/src/lib/hosted-contract.test.ts` because the shared copy contract became the enforcement point for the new vocabulary and is the most direct place to catch hosted wording drift. No product-scope deviation beyond that.

## Known Issues

None.

## Files Created/Modified

- `console/src/lib/hosted-contract.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/hosted/trust-boundary-card.tsx`
- `console/src/components/hosted/trust-boundary-card.test.tsx`
- `console/src/app/trust-boundary/page.tsx`
- `console/src/app/trust-boundary/page.test.tsx`
- `console/src/lib/hosted-contract.test.ts`
