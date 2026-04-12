# S04 — Research

**Date:** 2026-04-12

## Summary

S04 is targeted console/documentation work built on seams that already exist from S02 and S03. The slice directly owns R060 and R061: operators must be able to inspect the effective evidence boundary in the policy surface and the request-detail surface, and hosted export must remain visibly aligned with the metadata-only contract. The backend types and runtime behavior needed for that explanation are already in place: `TenantPolicy` exposes `evidence_retention_window` and `metadata_minimization_level`, usage-ledger rows persist `evidence_expires_at`, `metadata_fields_suppressed`, and `governance_source`, and S03 already surfaces retention lifecycle health without widening the contract.

The remaining gap is mostly explanatory composition rather than new persistence logic. The policy form currently renders the two runtime-enforced governance controls, but it does not yet synthesize them into an explicit “effective evidence boundary” explanation that tells operators what is retained, what strict minimization suppresses, how long request evidence remains inspectable, and that hosted export still excludes raw ledger rows. Request detail already shows row-level governance markers and deletion semantics, but it does not yet clearly separate row-specific persisted truth from broader boundary guidance. The hosted trust-boundary copy already exists in a shared module and is schema-backed, which gives S04 a low-risk way to reinforce R061 without introducing a second hand-maintained contract.

## Recommendation

Treat S04 as a two-seam slice: (1) policy-page/operator copy that synthesizes the configured boundary from `TenantPolicy` + `PolicyOptionsResponse`, and (2) request-detail/operator copy that explains the effective boundary for the selected persisted row while explicitly aligning with the hosted metadata-only contract. Reuse the existing shared hosted copy from `console/src/lib/hosted-contract.ts` instead of inventing new hosted wording. Keep this slice UI-only unless a test reveals a missing type field; backend persistence and hosted schema should remain unchanged.

Follow the established patterns from the installed skills `react-best-practices`, `accessibility`, and `web-design-guidelines`: derive display state from canonical typed data, keep explanatory cards subordinate to the primary evidence seam, and prefer explicit headings/text over clever interactions. This slice should not add a governance dashboard, new admin endpoint, or hosted export field. If more information is needed than the current policy/read models expose, that is a scope warning for S05 rather than a reason to widen S04.

## Implementation Landscape

### Key Files

- `console/src/components/policy/policy-form.tsx` — Main policy editor. Already renders `evidence_retention_window` and `metadata_minimization_level` as runtime-enforced controls, but currently only field-level helper text exists. Best seam for an additional synthesized “effective evidence boundary” card that explains retained vs suppressed metadata and retention/deletion semantics.
- `console/src/app/(console)/policy/page.tsx` — Page-level framing around preview-before-save. Useful if S04 needs one top-level explanatory paragraph tying policy preview to evidence boundary inspection without overloading the form body.
- `console/src/components/policy/policy-form.test.tsx` — Focused component tests for field rendering and preview semantics. Natural place to lock new boundary summary copy and branching behavior for standard vs strict minimization / retention windows.
- `console/src/components/policy/policy-page.test.tsx` — Page-level expectations for grouped policy sections. Update if new operator-facing policy guidance is added at page scope.
- `console/src/components/ledger/ledger-request-detail.tsx` — Authoritative selected-row evidence seam. Already shows row-level governance fields (`Evidence retention`, `Evidence expires at`, `Metadata minimization`, `Suppressed metadata fields`, `Governance source`) and deletion semantics. Best place for a bounded explanatory section/card that interprets those persisted fields as an effective evidence boundary for this row.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Existing tests already lock truthful deletion semantics and absence of dashboard drift. Extend with assertions for whichever new boundary explanation/card is added.
- `console/src/lib/admin-api.ts` — Canonical console types. Already includes governance fields on `TenantPolicy` and `UsageLedgerRecord`. No obvious change needed unless tests reveal a missing literal/type mismatch.
- `src/nebula/models/governance.py` — Backend source of truth for governance types. Confirms the only operator-facing runtime governance controls in scope are `evidence_retention_window` and `metadata_minimization_level`; minimization currently suppresses `route_signals` only.
- `src/nebula/services/governance_store.py` — Confirms effective runtime semantics. `_apply_usage_governance()` sets `evidence_expires_at`, `metadata_minimization_level`, `metadata_fields_suppressed`, and `governance_source`, and strict minimization suppresses `route_signals`. This is the exact behavioral truth S04 copy should reflect.
- `console/src/lib/hosted-contract.ts` — Shared schema-backed trust-boundary copy. Use this for any hosted-alignment reinforcement; it already encodes “metadata-only by default”, excluded classes, and operator reading guidance.
- `console/src/components/hosted/trust-boundary-card.tsx` and `console/src/app/trust-boundary/page.tsx` — Existing hosted trust-boundary surfaces. Probably do not need new structure, but are the right places if S04 needs a small copy update to explicitly mention governed evidence boundary staying inside the same metadata-only contract.
- `tests/test_hosted_contract.py` — Backend contract lock. Use as regression proof that S04 did not widen hosted export.
- `console/src/components/hosted/trust-boundary-card.test.tsx` — UI lock for shared hosted wording if hosted-alignment copy changes.
- `console/src/app/(console)/observability/page.tsx` and `console/src/app/(console)/observability/page.test.tsx` — Context for how request detail is framed under “selected request evidence first.” Useful guardrail: any new request-detail boundary copy must remain subordinate to the selected-row-first pattern.

### Build Order

1. **Define the policy-side effective boundary explanation first** in `policy-form.tsx`, because it establishes the shared operator vocabulary for “retained / suppressed / deleted / not hosted.” This also clarifies what the request-detail surface should mirror.
2. **Then update request detail** in `ledger-request-detail.tsx` to interpret row-level persisted markers using the same vocabulary, while keeping the selected ledger row authoritative.
3. **Only after both UI seams are clear, decide whether hosted trust-boundary copy needs a small reinforcement**. Prefer no change unless the existing shared wording cannot naturally support the new policy/request-detail copy.
4. **Finish with focused tests**, then backend hosted-contract regression tests to prove no schema drift.

### Verification Approach

- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`
- `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`
- If hosted copy changes: `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx`
- Backend regression for contract alignment: `./.venv/bin/pytest tests/test_hosted_contract.py`

Planner should also preserve these observable behaviors in tests:
- Policy surface makes the effective evidence boundary explicit from runtime-enforced fields, not advisory capture toggles.
- Request detail explains retained vs suppressed evidence for the selected persisted row and still states that deleted rows disappear rather than becoming a soft-delete/archive/hosted export.
- Hosted wording remains metadata-only and does not imply raw usage-ledger export or hosted runtime authority.

## Constraints

- S04 must satisfy **R060** and **R061** without widening into a new governance dashboard, admin endpoint, archive system, or hosted authority surface.
- Copy must match actual runtime semantics from `GovernanceStore._apply_usage_governance()`: today strict minimization suppresses `route_signals` only; do not imply broader payload capture/redaction behavior.
- Request detail remains the authoritative persisted evidence seam while the row exists; new explanatory UI must stay subordinate to that selected-row-first pattern already enforced on the Observability page.
- Hosted alignment should reuse `console/src/lib/hosted-contract.ts` / `src/nebula/models/hosted_contract.py` language so console copy does not drift from the schema-backed contract.

## Common Pitfalls

- **Overstating minimization scope** — The implementation currently suppresses `route_signals`, not arbitrary request content. Keep policy/request-detail copy tied to `metadata_fields_suppressed` and current governed fields.
- **Turning policy into a second observability surface** — The policy page should explain configured boundaries and preview consequences, not reproduce request-detail evidence or runtime-health dashboards.
- **Implying hosted recovery of deleted data** — Existing request-detail copy correctly says deleted evidence disappears. Any new boundary summary must preserve that same explicit absence.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js console UI | installed: `react-best-practices` | available |
| Accessibility for explanatory UI cards and labels | installed: `accessibility` | available |
| UI wording / bounded operator surfaces | installed: `web-design-guidelines` | available |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | discoverable via `npx skills add wshobson/agents@nextjs-app-router-patterns` |
| FastAPI | `wshobson/agents@fastapi-templates` | discoverable via `npx skills add wshobson/agents@fastapi-templates` |
| React accessibility patterns | `react-aria.adobe.com@react-aria` | discoverable via `npx skills add react-aria.adobe.com@react-aria` |
