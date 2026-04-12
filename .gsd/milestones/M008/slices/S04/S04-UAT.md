# S04: Operator evidence-boundary surfaces — UAT

**Milestone:** M008
**Written:** 2026-04-12T17:20:54.932Z

# UAT — S04 Operator evidence-boundary surfaces

## Preconditions
- Nebula console dependencies are installed (`npm --prefix console install` already satisfied in the working environment).
- Python virtualenv is available at `./.venv` with backend test dependencies installed.
- Use the current assembled worktree for Milestone M008/S04.

## Test Case 1 — Policy page explains the effective evidence boundary from runtime controls
1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Open the policy form test expectations or render the policy page in local dev if desired.
3. Confirm the policy surface shows an **Effective evidence boundary** panel inside the runtime-enforced controls section.
4. Confirm the panel states:
   - governed request metadata remains inspectable only for the configured retention window,
   - strict minimization suppresses route signals and similar metadata at write time,
   - hosted export still excludes raw usage-ledger rows.
5. Switch the form state between `metadata_minimization_level=standard` and `strict` in the test fixtures or local UI.

Expected outcome:
- The boundary summary changes with the retention/minimization settings.
- The panel remains subordinate to runtime-enforced controls and does not read like a second dashboard or advisory capture feature.
- The focused Vitest suite passes.

## Test Case 2 — Request detail explains retained, suppressed, deleted, and not-hosted semantics from the persisted row
1. Run `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`.
2. Inspect the rendered request-detail component fixture or local UI for a selected ledger row.
3. Confirm the request detail introduction identifies the persisted ledger row as the authoritative evidence seam **while the row still exists**.
4. Confirm the **Effective evidence boundary** panel states:
   - retained detail stays local to the persisted row,
   - suppressed metadata is no longer available from the ledger later,
   - deleted means governed retention removed the whole row at expiration,
   - hosted does not receive raw usage-ledger rows and cannot replace local request evidence.
5. Check that the copy does **not** imply archive recovery, soft-delete, or hosted raw export.

Expected outcome:
- Operators can read one selected row and understand exactly what evidence is still present, what was never retained, and what disappears after cleanup.
- The focused Vitest suite passes without any wording drift.

## Test Case 3 — Hosted trust boundary stays metadata-only while using the same evidence vocabulary
1. Run `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx`.
2. Run `./.venv/bin/pytest tests/test_hosted_contract.py`.
3. Inspect the hosted trust-boundary card/page fixtures or local UI.
4. Confirm the hosted surfaces reuse the retained/suppressed/deleted/not-hosted vocabulary and the hosted raw-ledger exclusion sentence.
5. Confirm the hosted surfaces still present the contract as metadata-only, descriptive, and non-authoritative for local runtime enforcement.

Expected outcome:
- Hosted wording matches the shared evidence vocabulary without implying raw usage-ledger export, tenant-policy enforcement, or request-serving authority.
- Both the focused Vitest suite and the backend hosted-contract regression pass.

## Edge Case 1 — Strict minimization removes route-signal detail
1. In the policy form fixture or local UI, set `metadata_minimization_level` to `strict`.
2. Re-check the policy evidence-boundary panel.

Expected outcome:
- The copy explicitly says strict minimization suppresses route signals and similar metadata at write time, so that detail is not available later from the ledger.

## Edge Case 2 — Expired evidence should not imply recoverability
1. Review the request-detail tests for deletion language and the hosted-contract tests for prohibited wording.
2. Confirm no surface uses phrases that suggest soft-delete, archives, recovery, or hosted substitution after expiration.

Expected outcome:
- Deletion is described as full row removal at retention expiry.
- Hosted remains unable to replace local request-level evidence after deletion.

