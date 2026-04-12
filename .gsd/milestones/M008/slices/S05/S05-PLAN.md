# S05: Integrated governance proof

**Goal:** Assemble one canonical, reviewable proof path that shows tenant evidence policy governs persistence and deletion, request detail remains historically truthful while a row exists, and the hosted metadata-only boundary stays intact without new governance product scope.
**Demo:** Nebula proves end to end that tenant policy governs persistence and deletion, request detail explains historical evidence truthfully, and the hosted metadata-only boundary remains intact without payload-capture or hosted-authority drift.

## Must-Haves

- `docs/m008-integrated-proof.md` exists and follows the established pointer-only integrated-proof pattern without duplicating backend or UI contracts.
- The proof order is explicit and bounded: policy/options and policy form → persisted ledger row and request detail → retention lifecycle cleanup and health visibility → hosted metadata-only trust boundary.
- Discoverability links to the new proof exist in `README.md` and `docs/architecture.md`.
- Focused backend and console verification mechanically prove the assembled governance story and catch drift in deletion semantics, request-detail authority, observability support role, and hosted metadata-only wording.

## Proof Level

- This slice proves: final-assembly

## Integration Closure

This slice closes milestone assembly by reusing the shipped S01–S04 seams without adding new APIs or dashboards. After these tasks, nothing should remain before M008 is reviewable end-to-end beyond executing the planned verification and milestone validation.

## Verification

- Runtime signals: usage-ledger row presence/disappearance, `retention_lifecycle` dependency status, and shared hosted evidence vocabulary remain the diagnostic signals for integrated-governance drift.
- Inspection surfaces: `docs/m008-integrated-proof.md`, `/v1/admin/usage/ledger`, `/health/ready`, `/health/dependencies`, `console/src/components/ledger/ledger-request-detail.tsx`, and hosted trust-boundary surfaces.
- Failure visibility: focused pytest/Vitest failures should localize whether drift is in persistence truth, deletion runtime health, supporting-context ordering, or hosted metadata-only wording.
- Redaction constraints: no task may introduce raw prompt/response capture, hosted raw-ledger export, or wording that implies recovery/authority beyond the existing metadata-only contract.

## Tasks

- [x] **T01: Author the M008 integrated governance proof and wire doc discoverability** `est:45m`
  Create the canonical M008 integrated proof document as a pointer-only walkthrough that joins the shipped S01–S04 seams in the exact proof order this slice owns: policy/options and policy form, one persisted request row and request detail, retention lifecycle cleanup plus health visibility, and the hosted metadata-only trust boundary. Follow the established pattern in `docs/m006-integrated-proof.md` and `docs/m007-integrated-proof.md`: keep each seam in its canonical role, avoid restating backend/UI contracts, and make scope-drift failure modes explicit. Add only minimal discoverability links in `README.md` and `docs/architecture.md` so reviewers can find the new proof without turning those docs into a second explanation surface. Reuse the shared evidence vocabulary from `console/src/lib/hosted-contract.ts` and explicitly preserve the bounded story from requirements R062/R063/R064: request-led proof stays primary, deletion is driven by persisted `evidence_expires_at`, and hosted remains metadata-only rather than a recovery or authority layer.

If any wording or ordering in the current docs conflicts with the shipped seams, fix the integrated-proof framing in the new doc rather than expanding product scope. Keep the task implementation narrow and pointer-based.
  - Files: `docs/m006-integrated-proof.md`, `docs/m007-integrated-proof.md`, `docs/m008-integrated-proof.md`, `README.md`, `docs/architecture.md`, `console/src/lib/hosted-contract.ts`
  - Verify: python3 - <<'PY'
from pathlib import Path
proof = Path('docs/m008-integrated-proof.md')
assert proof.exists(), 'missing docs/m008-integrated-proof.md'
text = proof.read_text()
for heading in [
    '# M008 integrated governance proof',
    '## What this integrated proof establishes',
    '## Canonical proof order',
    '## Minimal operator walkthrough',
    '## Failure modes this integrated proof makes obvious',
]:
    assert heading in text, heading
for phrase in [
    'tenant policy',
    'evidence_expires_at',
    'request detail',
    'retention_lifecycle',
    'metadata-only',
]:
    assert phrase in text, phrase
for path in ['README.md', 'docs/architecture.md']:
    assert 'docs/m008-integrated-proof.md' in Path(path).read_text(), path
assert 'TBD' not in text and 'TODO' not in text
PY

- [x] **T02: Tighten executable proof seams for integrated governance ordering** `est:1h`
  Use the new integrated proof doc to drive focused regression coverage across the shipped seams instead of broad feature churn. Run the targeted backend and console suites that already encode the M008 governance story, then only add or tighten assertions where integrated-proof drift is currently unguarded. Priority checks: request detail remains authoritative while a row exists; deletion semantics continue to reject soft-delete/recovery implications; observability/runtime-health stays supporting context rather than replacing ledger proof; and hosted trust-boundary surfaces keep the metadata-only evidence wording aligned with the shared contract. If the existing tests already cover a seam, keep it stable; if a missing order/copy expectation is needed to make the integrated proof executable, add the smallest focused assertion in the relevant test file.

Do not add new endpoints, dashboards, or exported data. This task closes R062/R063/R064 by ensuring the assembled story is mechanically verifiable from the real backend, health, and console seams the doc points to.
  - Files: `docs/m008-integrated-proof.md`, `tests/test_governance_api.py`, `tests/test_retention_lifecycle_service.py`, `tests/test_health.py`, `tests/test_hosted_contract.py`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/components/health/runtime-health-cards.test.tsx`, `console/src/app/(console)/observability/page.test.tsx`, `console/src/components/hosted/trust-boundary-card.test.tsx`, `console/src/app/trust-boundary/page.test.tsx`
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py tests/test_retention_lifecycle_service.py tests/test_health.py tests/test_hosted_contract.py -k "usage_ledger or retention or lifecycle or health or heartbeat" && npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx

## Files Likely Touched

- docs/m006-integrated-proof.md
- docs/m007-integrated-proof.md
- docs/m008-integrated-proof.md
- README.md
- docs/architecture.md
- console/src/lib/hosted-contract.ts
- tests/test_governance_api.py
- tests/test_retention_lifecycle_service.py
- tests/test_health.py
- tests/test_hosted_contract.py
- console/src/components/ledger/ledger-request-detail.test.tsx
- console/src/components/health/runtime-health-cards.test.tsx
- console/src/app/(console)/observability/page.test.tsx
- console/src/components/hosted/trust-boundary-card.test.tsx
- console/src/app/trust-boundary/page.test.tsx
