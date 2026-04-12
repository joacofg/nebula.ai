# M008/S05 — Research

**Date:** 2026-04-12

## Summary

S05 is a targeted research slice, not a new subsystem build. The milestone seams already exist across S01–S04: typed tenant evidence-governance policy (`TenantPolicy`), write-time governed ledger persistence (`GovernanceStore.record_usage()` and row markers on `UsageLedgerRecord`), explicit retention cleanup (`GovernanceStore.delete_expired_usage_records()` and `RetentionLifecycleService`), request-detail/policy/hosted operator vocabulary (`console/src/lib/hosted-contract.ts`), and bounded operator composition (`console/src/app/(console)/observability/page.tsx`). What is missing for R062/R063/R064 is the integrated proof artifact that joins those seams into one canonical, reviewable path without restating contracts or inventing new APIs, dashboards, or hosted authority.

The strongest pattern in this repo is already established by prior integrated proof docs like `docs/m006-integrated-proof.md`, `docs/m007-integrated-proof.md`, and `docs/hosted-integrated-adoption-proof.md`: keep the walkthrough pointer-only, start from the canonical evidence seam, delegate detailed contracts back to their owning files/docs, and make scope drift explicit in “failure modes.” S05 should follow that exact documentation pattern, but for evidence governance: tenant policy → persisted row/governance markers → runtime retention execution and health visibility → hosted metadata-only boundary. Because the product work is already landed, the likely implementation is mostly a new integrated proof doc plus focused regression tests if any proof-order or wording seam is currently unguarded.

## Recommendation

Create a canonical integrated proof document under `docs/` for M008, modeled closely on `docs/m007-integrated-proof.md` and `docs/m006-integrated-proof.md`, and only add tests where the current code lacks executable guards for proof ordering or anti-drift wording. The document should treat existing seams as authoritative: `console/src/components/policy/policy-form.tsx` for effective evidence-boundary policy explanation, `src/nebula/api/routes/admin.py` + `GET /v1/admin/usage/ledger` for durable request evidence, `console/src/components/ledger/ledger-request-detail.tsx` for historical request explanation while a row exists, `src/nebula/services/retention_lifecycle_service.py` + health surfaces for real deletion/runtime truth, and `console/src/app/trust-boundary/page.tsx` / `src/nebula/models/hosted_contract.py` for the hosted metadata-only boundary.

Use the same anti-sprawl rules as the earlier integrated proof docs and the installed skills most relevant here: `react-best-practices` / `web-design-guidelines` reinforce reusing existing UI seams instead of inventing new presentation surfaces, and the available `github-workflows`/`test` style patterns in-repo show proof should be executable where possible. Do **not** add a new admin endpoint, retention dashboard, export mode, or compliance-style summary. S05 succeeds by making the already-built governance chain legible and reviewable, not by expanding product scope.

## Implementation Landscape

### Key Files

- `docs/m007-integrated-proof.md` — Best local template for structure and tone. It shows the canonical pattern for “What this establishes,” “Canonical proof order,” “Minimal walkthrough,” “What this intentionally does not duplicate,” and “Failure modes.”
- `docs/m006-integrated-proof.md` — Best local example for joining public/runtime evidence with admin/operator corroboration while refusing new authority claims.
- `docs/hosted-integrated-adoption-proof.md` — Best local example for hosted trust-boundary language and for keeping public trust-boundary review as a first-class proof step without implying hosted runtime authority.
- `src/nebula/models/governance.py` — Canonical typed model for S05’s chain. `TenantPolicy` owns `evidence_retention_window` and `metadata_minimization_level`; `UsageLedgerRecord` owns `message_type`, `evidence_expires_at`, `metadata_fields_suppressed`, and `governance_source`.
- `src/nebula/api/routes/admin.py` — Canonical admin seams for the proof. `/v1/admin/policy/options` exposes runtime-enforced vs advisory governance fields; `/v1/admin/usage/ledger` is the durable request evidence read path.
- `src/nebula/services/governance_store.py` — Canonical backend write/delete seam. S01/S02 established that governed markers are stamped here and expired rows are deleted here.
- `src/nebula/services/retention_lifecycle_service.py` — Canonical operational retention seam. `run_cleanup_once()` and `health_status()` are the proofable runtime lifecycle hooks; use them as the runtime leg in the integrated story.
- `src/nebula/models/hosted_contract.py` — Canonical backend hosted allowlist/exclusion contract. S05 must point to this rather than restating hosted export fields.
- `console/src/lib/hosted-contract.ts` — Canonical shared vocabulary for retained/suppressed/deleted/not-hosted evidence semantics. Any S05 UI/document copy should reuse these phrases, not fork them.
- `console/src/components/policy/policy-form.tsx` — Canonical policy-side “effective evidence boundary” seam. It already derives operator-facing retention/minimization explanations from policy fields.
- `console/src/components/ledger/ledger-request-detail.tsx` — Canonical request-level explanation seam. It is where persisted row truth stays authoritative while the row exists.
- `console/src/app/(console)/observability/page.tsx` — Canonical page hierarchy proving “selected request evidence first” and that runtime-health/recommendation cards are subordinate context, not replacements for the row.
- `console/src/components/health/runtime-health-cards.tsx` — Existing operator runtime-health seam for retention lifecycle visibility; use this in the proof order instead of creating a retention-specific UI.
- `console/src/components/hosted/trust-boundary-card.tsx` and `console/src/app/trust-boundary/page.tsx` — Canonical hosted metadata-only explanation seams; these already reuse the shared evidence vocabulary.
- `tests/test_governance_api.py` — Main backend integration proof bank. It already covers policy options, governed ledger rows, and before/after deletion through `/v1/admin/usage/ledger`.
- `tests/test_retention_lifecycle_service.py` — Canonical runtime proof that cleanup deletes only expired rows and that health surfaces reflect lifecycle state.
- `tests/test_health.py` — Confirms the retention lifecycle dependency is present on readiness/dependency health seams.
- `tests/test_hosted_contract.py` — Canonical hosted-boundary regression suite, including the rule that retention lifecycle appears only as coarse dependency membership in heartbeat export.
- `console/src/components/policy/policy-form.test.tsx` — Guards policy evidence-boundary wording.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Guards retained/suppressed/deleted/not-hosted wording on request detail.
- `console/src/components/health/runtime-health-cards.test.tsx` and `console/src/app/(console)/observability/page.test.tsx` — Guard the existing health/observability proof surfaces.
- `console/src/app/trust-boundary/page.test.tsx` and `console/src/components/hosted/trust-boundary-card.test.tsx` — Guard hosted trust-boundary wording and proof order.

### Build Order

1. **Write the integrated proof doc first.** This is the core deliverable for R062/R063/R064 and the least risky way to bind the completed seams together. Follow the existing integrated-proof doc pattern exactly.
2. **Anchor the proof order to canonical seams.** Recommended sequence: policy/options and policy form → issue or inspect one request via `/v1/admin/usage/ledger` / request detail → retention lifecycle health and before/after deletion proof via runtime health + ledger disappearance → hosted trust-boundary confirmation. This mirrors M008 acceptance criteria and avoids turning Observability or hosted pages into substitutes for the ledger.
3. **Add or tighten tests only where the integrated proof introduces new ordering/copy expectations.** Current suites already cover most seams. If a new doc references proof order on a page that is not tested yet, add focused assertions rather than broad UI tests.
4. **Finish with targeted verification only.** No need for broad full-suite runs unless a touched file forces it.

### Verification Approach

- Backend governance/runtime proof: `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or usage_ledger or retention or expired"`
- Retention lifecycle/runtime health proof: `./.venv/bin/pytest tests/test_retention_lifecycle_service.py tests/test_health.py -k "retention or lifecycle or health"`
- Hosted metadata-only boundary proof: `./.venv/bin/pytest tests/test_hosted_contract.py`
- Console operator-surface proof: `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx`
- Manual artifact review: read the new integrated proof doc next to `docs/m006-integrated-proof.md` / `docs/m007-integrated-proof.md` and confirm it delegates details back to canonical seams instead of duplicating contracts.

## Constraints

- R062/R063/R064 are the active requirements S05 owns; all research points back to proving one end-to-end governance chain without weakening request-led debugging or widening scope.
- Keep the selected persisted ledger row authoritative while it exists. S04 established that policy summaries, health cards, and hosted summaries are supporting context only.
- Do not add a retention-specific admin endpoint, dashboard, archive semantics, or hosted raw export. S02/S03 explicitly rejected those paths.
- Hosted export remains metadata-only by the allowlist in `src/nebula/models/hosted_contract.py`; any S05 proof must delegate to that canonical contract and shared `console/src/lib/hosted-contract.ts` vocabulary.
- For tests proving historical expiration behavior, seed exact rows directly when needed. S03 learned that `GovernanceStore.record_usage()` intentionally reapplies current policy and can overwrite handcrafted historical expiration markers.
- Follow the integrated-doc pattern in existing Nebula docs: pointer-only, canonical proof order, minimal duplication, and explicit failure modes.

## Common Pitfalls

- **Turning the proof doc into a second contract** — Follow `docs/m007-integrated-proof.md` and delegate detailed field/API semantics back to owning files/docs instead of restating them.
- **Letting hosted or observability surfaces replace the ledger row** — Keep `GET /v1/admin/usage/ledger` and `ledger-request-detail` as the request-level truth seam; Observability and hosted pages are corroboration and boundary explanation only.
- **Proving deletion from current tenant policy instead of persisted row markers** — The integrated story must say cleanup uses persisted `evidence_expires_at`, not current-policy inference.
- **Accidentally implying soft-delete or recovery semantics** — Reuse `console/src/lib/hosted-contract.ts` vocabulary, especially the `deleted` string that explicitly rejects recovery/archive implications.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js operator surfaces | `react-best-practices` | available |
| UI / trust-boundary wording review | `web-design-guidelines` | available |
| FastAPI backend patterns | `wshobson/agents@fastapi-templates` | none found locally; suggested via `npx skills find` |
| Next.js App Router patterns | `wshobson/agents@nextjs-app-router-patterns` | none found locally; suggested via `npx skills find` |
| PostgreSQL schema / table review | `wshobson/agents@postgresql-table-design` | none found locally; suggested via `npx skills find` |
