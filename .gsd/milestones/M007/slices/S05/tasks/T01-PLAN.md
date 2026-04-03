---
estimated_steps: 6
estimated_files: 5
skills_used: []
---

# T01: Author the M007 integrated proof and wire discoverability

Create the pointer-only M007 close-out walkthrough and link it from the repo’s main discoverability docs so reviewers can follow one strict operator proof order without treating the new doc as a second spec.

Steps:
1. Read `docs/m006-integrated-proof.md` and `docs/v4-integrated-proof.md` as the canonical pointer-only pattern, then draft `docs/m007-integrated-proof.md` around the M007 review order: selected-request-first Observability, authoritative request detail, compare-before-save policy preview, and explicit anti-drift scope conclusion.
2. Keep the new doc composition-first and pointer-only: point to `console/src/app/(console)/observability/page.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-table.tsx`, `console/src/components/policy/policy-form.tsx`, `console/src/app/(console)/policy/page.tsx`, and the focused Vitest files instead of restating contracts or long UI copy.
3. Update `README.md` and `docs/architecture.md` to include discoverability links to `docs/m007-integrated-proof.md` in the same style as prior integrated proof entries, without expanding those docs into another explanation surface.
4. Sanity-check the new wording against M007 scope boundaries: no dashboard, routing studio, analytics product, redesign-sprawl, or parallel workflow framing should appear as positive product claims.

## Inputs

- ``docs/m006-integrated-proof.md``
- ``docs/v4-integrated-proof.md``
- ``README.md``
- ``docs/architecture.md``
- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-table.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/app/(console)/policy/page.tsx``

## Expected Output

- ``docs/m007-integrated-proof.md``
- ``README.md``
- ``docs/architecture.md``

## Verification

python - <<'PY'
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

## Observability Impact

Signals added/changed: a new pointer-only proof artifact that names the authoritative code and test seams for future investigation.
How a future agent inspects this: read `docs/m007-integrated-proof.md` first, then open the linked page/component/test files in the stated order.
Failure state exposed: proof-order drift, duplicated contract prose, or scope-language regressions become explicit in one discoverable doc instead of being inferred across scattered files.
