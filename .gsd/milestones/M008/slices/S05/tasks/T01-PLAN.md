---
estimated_steps: 2
estimated_files: 6
skills_used: []
---

# T01: Author the M008 integrated governance proof and wire doc discoverability

Create the canonical M008 integrated proof document as a pointer-only walkthrough that joins the shipped S01–S04 seams in the exact proof order this slice owns: policy/options and policy form, one persisted request row and request detail, retention lifecycle cleanup plus health visibility, and the hosted metadata-only trust boundary. Follow the established pattern in `docs/m006-integrated-proof.md` and `docs/m007-integrated-proof.md`: keep each seam in its canonical role, avoid restating backend/UI contracts, and make scope-drift failure modes explicit. Add only minimal discoverability links in `README.md` and `docs/architecture.md` so reviewers can find the new proof without turning those docs into a second explanation surface. Reuse the shared evidence vocabulary from `console/src/lib/hosted-contract.ts` and explicitly preserve the bounded story from requirements R062/R063/R064: request-led proof stays primary, deletion is driven by persisted `evidence_expires_at`, and hosted remains metadata-only rather than a recovery or authority layer.

If any wording or ordering in the current docs conflicts with the shipped seams, fix the integrated-proof framing in the new doc rather than expanding product scope. Keep the task implementation narrow and pointer-based.

## Inputs

- ``docs/m006-integrated-proof.md``
- ``docs/m007-integrated-proof.md``
- ``README.md``
- ``docs/architecture.md``
- ``console/src/lib/hosted-contract.ts``
- ``.gsd/milestones/M008/slices/S05/S05-RESEARCH.md``

## Expected Output

- ``docs/m008-integrated-proof.md``
- ``README.md``
- ``docs/architecture.md``

## Verification

python3 - <<'PY'
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

## Observability Impact

Future agents inspect `docs/m008-integrated-proof.md` first to follow the canonical review order, then open the linked runtime and UI seams in sequence. Failure is visible as missing proof-order sections, missing discoverability links, or wording that stops matching the shared hosted/evidence vocabulary.
