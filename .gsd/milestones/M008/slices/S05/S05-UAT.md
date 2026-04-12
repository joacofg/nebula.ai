# S05: S05 — UAT

**Milestone:** M008
**Written:** 2026-04-12T17:31:48.790Z

# UAT — M008 / S05 Integrated governance proof

## Preconditions

1. The assembled worktree includes `docs/m008-integrated-proof.md`, `README.md`, and `docs/architecture.md` from S05.
2. Backend and console dependencies are installed (`./.venv` available; `console/node_modules` installed).
3. A local reviewer can inspect docs and run the focused verification commands from the repository root.

## Test Case 1 — Reviewer can discover the canonical M008 proof from top-level docs

1. Open `README.md`.
   - Expected: It links to `docs/m008-integrated-proof.md` as the M008 close-out proof surface rather than duplicating the full governance explanation inline.
2. Open `docs/architecture.md`.
   - Expected: It also links to `docs/m008-integrated-proof.md` so architecture readers can find the integrated governance proof.
3. Open `docs/m008-integrated-proof.md`.
   - Expected: The document exists and includes the sections `What this integrated proof establishes`, `Canonical proof order`, `Minimal operator walkthrough`, and `Failure modes this integrated proof makes obvious`.

## Test Case 2 — The integrated proof preserves the required end-to-end order

1. Read the `Canonical proof order` section in `docs/m008-integrated-proof.md`.
   - Expected: The order is explicitly tenant policy/options and policy form first.
2. Continue through the next proof steps.
   - Expected: The second stage is one persisted usage-ledger row plus request detail as the primary historical evidence while the row exists.
3. Continue through the retention section.
   - Expected: The document states that deletion is driven by persisted `evidence_expires_at` and that `retention_lifecycle` health is supporting runtime context rather than the primary proof seam.
4. Continue to the final hosted section.
   - Expected: Hosted is described as metadata-only, not a recovery path, not a raw-ledger export, and not a runtime authority layer.

## Test Case 3 — Focused backend verification proves persistence, deletion, health, and hosted boundaries together

1. Run:
   `./.venv/bin/pytest tests/test_governance_api.py tests/test_retention_lifecycle_service.py tests/test_health.py tests/test_hosted_contract.py -k "usage_ledger or retention or lifecycle or health or heartbeat"`
   - Expected: The command passes.
2. Inspect the test names/results.
   - Expected: Coverage includes governed usage-ledger persistence, retention lifecycle deletion behavior, health/dependency reporting including `retention_lifecycle`, and hosted contract heartbeat/trust-boundary behavior.
3. Review `tests/test_health.py`.
   - Expected: `governance_store` is asserted before `retention_lifecycle`, reinforcing the integrated-proof ordering that request-led persistence truth precedes supporting runtime health context.

## Test Case 4 — Console verification proves request evidence stays primary over supporting context

1. Run:
   `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx`
   - Expected: All five test files pass.
2. Review `console/src/app/(console)/observability/page.test.tsx`.
   - Expected: The selected request evidence section is asserted before the follow-up context section, and request-row content appears before the `retention_lifecycle` dependency-health surface.
3. Review `console/src/components/ledger/ledger-request-detail.test.tsx` and hosted trust-boundary tests.
   - Expected: Request detail continues to use historically truthful retained/suppressed/deleted semantics while a row exists, and hosted surfaces continue using the shared metadata-only vocabulary without implying raw export or hosted recovery.

## Test Case 5 — Edge case: the proof must reject governance-story drift

1. Inspect the `Failure modes this integrated proof makes obvious` section in `docs/m008-integrated-proof.md`.
   - Expected: It explicitly calls out drift such as soft-delete recovery, current-policy-only deletion inference, health becoming more authoritative than the selected request row, hosted raw-ledger export, or hosted authority.
2. Inspect `console/src/lib/hosted-contract.ts` references from request-detail and trust-boundary surfaces.
   - Expected: The shared retained/suppressed/deleted/not-hosted vocabulary is reused rather than rephrased independently.
3. Confirm no new retention-specific dashboard, hosted archive, or exported raw evidence surface was introduced in this slice.
   - Expected: The slice stays bounded to docs/discoverability plus focused regression assertions only.

## Operational Readiness (Q8)

- **Health signal:** `/health/ready` and `/health/dependencies` expose `retention_lifecycle` status, required flag, last run/attempt metadata, and failure detail as bounded runtime context.
- **Failure signal:** Focused pytest/Vitest failures localize drift in request-evidence ordering, deletion semantics, retention lifecycle visibility, or hosted metadata-only wording; runtime degradation surfaces through `retention_lifecycle` dependency status and error fields.
- **Recovery procedure:** First inspect the selected request row and request detail to confirm whether evidence still exists, then inspect retention lifecycle dependency health and recent cleanup diagnostics, then compare the impacted seam against `docs/m008-integrated-proof.md` and the shared hosted contract before making targeted fixes.
- **Monitoring gaps:** Health surfaces are intentionally supportive and coarse; they do not preserve deleted-row recovery data, and hosted remains intentionally non-authoritative. Investigations still depend on the local ledger row while it exists and on focused test coverage to catch wording/order drift.

