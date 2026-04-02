---
estimated_steps: 6
estimated_files: 6
skills_used: []
---

# T01: Assemble the pointer-only M006 integrated proof and discoverability links

Create the final calibrated-routing close-out artifact that joins the canonical M006 proof seams without redefining their contracts. Follow the structure of `docs/v4-integrated-proof.md` and `docs/embeddings-integrated-adoption-proof.md`, keep the document composition-first, and add only pointer-level discoverability updates in `README.md` and `docs/architecture.md`.

Steps:
1. Add a new M006 integrated proof doc in `docs/` that states what the assembled proof establishes, the strict proof order, how canonical sources fit together, a minimal operator walkthrough, what the document intentionally does not duplicate, and the failure modes that would reveal scope or proof drift.
2. Keep the proof order explicit and grounded in shipped seams: `docs/route-decision-vocabulary.md`, the public `POST /v1/chat/completions` path and calibrated `X-Nebula-*` / `X-Request-ID` headers, `GET /v1/admin/usage/ledger?request_id=...`, `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, the selected-request-first Observability/request-detail surfaces, and bounded degraded or rollout-disabled semantics.
3. Update `README.md` and `docs/architecture.md` only to add discoverability pointers to the new integrated proof artifact while preserving the existing rule that detailed routing, replay, and operator-surface semantics stay in their canonical docs and code-backed seams.
4. Verify the artifact and links mechanically so the document is present, non-empty, and references the required proof seams without introducing TODO or TBD placeholders.

## Inputs

- `docs/v4-integrated-proof.md`
- `docs/embeddings-integrated-adoption-proof.md`
- `docs/route-decision-vocabulary.md`
- `README.md`
- `docs/architecture.md`
- `.gsd/milestones/M006/slices/S05/S05-RESEARCH.md`

## Expected Output

- `docs/m006-integrated-proof.md`
- `README.md`
- `docs/architecture.md`

## Verification

python - <<'PY'
from pathlib import Path
paths = [Path('docs/m006-integrated-proof.md'), Path('README.md'), Path('docs/architecture.md')]
for path in paths:
    assert path.exists(), f'missing {path}'
    assert path.read_text().strip(), f'empty {path}'
proof = Path('docs/m006-integrated-proof.md').read_text()
required = [
    'route-decision-vocabulary',
    'POST /v1/chat/completions',
    'X-Request-ID',
    'X-Nebula-',
    '/v1/admin/usage/ledger',
    'policy/simulate',
    'Observability',
    'does not duplicate',
    'failure modes',
]
for token in required:
    assert token in proof, f'missing {token}'
assert 'TODO' not in proof and 'TBD' not in proof
PY
rg -n "m006-integrated-proof|route-decision-vocabulary|X-Request-ID|X-Nebula-|/v1/admin/usage/ledger|policy/simulate|Observability|does not duplicate|failure modes" README.md docs/architecture.md docs/m006-integrated-proof.md

## Observability Impact

This task does not add new telemetry. It improves how a future agent or reviewer locates the existing runtime and operator proof surfaces by making the public-header, request-id, ledger, replay, and Observability seams discoverable in one canonical review order.
