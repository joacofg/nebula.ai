---
estimated_steps: 1
estimated_files: 6
skills_used: []
---

# T01: Write the M009 integrated proof and discoverability links

Write the M009 close-out proof in the same pointer-first style as M006-M008 and make the shared vocabulary/discoverability references sufficient so the doc does not need to define outcome-grounded fields inline. Keep the doc anchored to the existing seams only: route vocabulary, one live `POST /v1/chat/completions` request, correlated `GET /v1/admin/usage/ledger?request_id=...` row, `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, and selected-request-first Observability/request detail. Additive doc changes only; do not invent a new API, dashboard, or hosted role.

## Inputs

- ``docs/m006-integrated-proof.md``
- ``docs/m007-integrated-proof.md``
- ``docs/m008-integrated-proof.md``
- ``docs/route-decision-vocabulary.md``
- ``docs/architecture.md``

## Expected Output

- ``docs/m009-integrated-proof.md``
- ``docs/route-decision-vocabulary.md``
- ``docs/architecture.md``

## Verification

python - <<'PY'
from pathlib import Path
proof = Path('docs/m009-integrated-proof.md')
text = proof.read_text()
assert proof.exists()
assert text.count('## ') >= 6
for needle in [
    'POST /v1/chat/completions',
    'GET /v1/admin/usage/ledger?request_id=...',
    'POST /v1/admin/tenants/{tenant_id}/policy/simulate',
    'happy path',
    'degraded path',
    'selected-request-first',
]:
    assert needle in text, needle
vocab = Path('docs/route-decision-vocabulary.md').read_text()
for needle in ['outcome_bonus', 'evidence_penalty', 'outcome_evidence']:
    assert needle in vocab, needle
arch = Path('docs/architecture.md').read_text()
assert 'docs/m009-integrated-proof.md' in arch
assert 'TODO' not in text and 'TBD' not in text
PY

## Observability Impact

Keeps failure diagnosis anchored to the existing request-first seams by documenting where runtime headers, ledger rows, replay output, and request detail remain authoritative.
