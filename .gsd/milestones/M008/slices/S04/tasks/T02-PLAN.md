---
estimated_steps: 1
estimated_files: 7
skills_used: []
---

# T02: Align request-detail and hosted trust-boundary copy with the same evidence vocabulary

Extend the request-detail evidence surface so a selected persisted row explains the effective evidence boundary with the same retained/suppressed/deleted/not-hosted vocabulary introduced on the policy page. Keep the selected ledger row authoritative while it exists, explicitly distinguish row-level persisted truth from broader hosted-boundary guidance, and do not imply recovery, soft-delete, or hosted raw export. If the existing trust-boundary card/page needs reinforcement, make only small shared-copy updates through `console/src/lib/hosted-contract.ts` and the existing hosted components/tests so hosted wording remains metadata-only and schema-backed. Add or update request-detail and hosted tests to prove row-level governance markers remain legible while present and that hosted surfaces still exclude raw usage-ledger export or runtime authority claims.

## Inputs

- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/components/hosted/trust-boundary-card.tsx``
- ``console/src/components/hosted/trust-boundary-card.test.tsx``
- ``console/src/app/trust-boundary/page.tsx``
- ``console/src/app/trust-boundary/page.test.tsx``
- ``console/src/lib/hosted-contract.ts``
- ``tests/test_hosted_contract.py``

## Expected Output

- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/components/hosted/trust-boundary-card.test.tsx``
- ``console/src/app/trust-boundary/page.test.tsx``
- ``console/src/lib/hosted-contract.ts``

## Verification

npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx && ./.venv/bin/pytest tests/test_hosted_contract.py

## Observability Impact

Keeps the selected request-detail panel and hosted trust page as the two bounded inspection surfaces for runtime-evidence-vs-hosted-boundary diagnosis, with tests catching wording drift.
