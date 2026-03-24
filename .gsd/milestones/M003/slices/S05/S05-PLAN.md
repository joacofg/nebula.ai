# S05: Final adoption assembly

**Goal:** Assemble the embeddings adoption story into one narrow, end-to-end proof package that joins the canonical contract, realistic migration path, and durable evidence/corroboration flow without widening Nebula into broader embeddings parity, SDK sprawl, hosted-plane expansion, or unrelated infrastructure work.
**Demo:** A reviewer can open one embeddings assembly walkthrough, follow the proof order from public `POST /v1/embeddings` to `X-Request-ID`/`X-Nebula-*` headers to `GET /v1/admin/usage/ledger?request_id=...` to Observability corroboration, and confirm the linked docs and executable proofs agree while keeping `docs/embeddings-adoption-contract.md` as the only detailed public contract.

## Must-Haves

- Add a dedicated embeddings final-assembly walkthrough under `docs/` that assembles, but does not redefine, the existing contract, migration, and operator-corroboration artifacts.
- Keep `docs/embeddings-adoption-contract.md` as the single canonical detailed `POST /v1/embeddings` contract and keep other discoverability surfaces pointer-only.
- Re-check the assembled proof against the existing executable embeddings tests and source-level doc/discoverability assertions so active requirement `R024` is concretely advanced and can be validated.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- `test -f docs/embeddings-integrated-adoption-proof.md && ! grep -q "TBD\|TODO" docs/embeddings-integrated-adoption-proof.md && [ "$(rg -c "^## " docs/embeddings-integrated-adoption-proof.md)" -ge 6 ]`
- `python - <<'PY'
from pathlib import Path
text = Path('docs/embeddings-integrated-adoption-proof.md').read_text()
for needle in [
    'docs/embeddings-adoption-contract.md',
    'docs/embeddings-reference-migration.md',
    'POST /v1/embeddings',
    'X-Request-ID',
    '/v1/admin/usage/ledger',
    'Observability',
    'What this walkthrough intentionally does not duplicate',
    'Failure modes this integrated proof makes obvious',
]:
    assert needle in text, needle
PY`
- `rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md`

## Observability / Diagnostics

- Runtime signals: public `X-Request-ID` plus `X-Nebula-*` embeddings headers, metadata-only usage-ledger rows, and Observability route-target/detail surfaces for `embeddings`
- Inspection surfaces: `tests/test_embeddings_reference_migration.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`, `docs/embeddings-integrated-adoption-proof.md`, `GET /v1/admin/usage/ledger?request_id=...`, and the console Observability flow documented in `console/e2e/observability.spec.ts`
- Failure visibility: missing `X-Request-ID`, broken public-to-ledger correlation, doc-link drift, or wording that elevates Observability above the public request path
- Redaction constraints: no raw embedding inputs, vectors, provider secrets, or hosted-plane scope expansion should appear in assembled proof artifacts

## Integration Closure

- Upstream surfaces consumed: `docs/embeddings-adoption-contract.md`, `docs/embeddings-reference-migration.md`, `tests/test_embeddings_reference_migration.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`, `console/e2e/observability.spec.ts`, `README.md`, `docs/architecture.md`
- New wiring introduced in this slice: one final embeddings assembly doc plus pointer-only discoverability links from repo/docs entry surfaces back to the assembled walkthrough
- What remains before the milestone is truly usable end-to-end: nothing

## Tasks

- [ ] **T01: Author the embeddings integrated adoption walkthrough** `est:45m`
  - Why: S05's primary gap is the missing final assembly artifact that joins the already-shipped embeddings contract, migration proof, and durable evidence path into one credible narrow adoption story.
  - Files: `docs/embeddings-integrated-adoption-proof.md`, `docs/integrated-adoption-proof.md`, `docs/embeddings-adoption-contract.md`, `docs/embeddings-reference-migration.md`, `tests/test_embeddings_reference_migration.py`, `console/e2e/observability.spec.ts`
  - Do: Create `docs/embeddings-integrated-adoption-proof.md` using `docs/integrated-adoption-proof.md` as the structural precedent but keep it embeddings-specific; preserve the required proof order of public request -> response headers -> usage ledger -> Observability corroboration; explicitly say the contract doc remains canonical and the migration guide/test remain the proof source; include sections for what the walkthrough establishes, canonical proof order, minimal integrated walkthrough, what it intentionally does not duplicate, and failure modes that reveal scope drift under `R024`.
  - Verify: `test -f docs/embeddings-integrated-adoption-proof.md && ! grep -q "TBD\|TODO" docs/embeddings-integrated-adoption-proof.md && [ "$(rg -c "^## " docs/embeddings-integrated-adoption-proof.md)" -ge 6 ] && python - <<'PY'
from pathlib import Path
text = Path('docs/embeddings-integrated-adoption-proof.md').read_text()
for needle in ['docs/embeddings-adoption-contract.md','docs/embeddings-reference-migration.md','POST /v1/embeddings','X-Request-ID','/v1/admin/usage/ledger','Observability','What this walkthrough intentionally does not duplicate','Failure modes this integrated proof makes obvious']:
    assert needle in text, needle
PY`
  - Done when: `docs/embeddings-integrated-adoption-proof.md` exists as the embeddings-specific final walkthrough, links only to already-canonical sources for detailed semantics, and clearly protects the milestone from parity/helper/hosted-plane scope drift.
- [ ] **T02: Wire discoverability and close out R024 evidence** `est:45m`
  - Why: The new assembly doc only validates the milestone guardrail if readers can find it from entry surfaces and the assembled package is re-checked against the executable proof and narrow-scope boundaries.
  - Files: `README.md`, `docs/architecture.md`, `docs/embeddings-integrated-adoption-proof.md`, `.gsd/REQUIREMENTS.md`, `tests/test_embeddings_reference_migration.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`
  - Do: Add pointer-only links to `docs/embeddings-integrated-adoption-proof.md` from `README.md` and `docs/architecture.md` without duplicating embeddings contract semantics; make any minimal wording alignment edits in the new assembly doc if verification uncovers drift; run the focused embeddings proof suite and doc-source checks; then update `R024` in `.gsd/REQUIREMENTS.md` from `active` to `validated` with verification text that cites the final assembly doc and the rerun checks.
  - Verify: `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings && rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md && rg -n "R024|validated|embeddings-integrated-adoption-proof" .gsd/REQUIREMENTS.md`
  - Done when: entry docs expose the final embeddings assembly path without becoming a second contract surface, the focused proof/doc checks pass, and `R024` is updated with concrete validation evidence tied to the assembled artifacts.

## Files Likely Touched

- `docs/embeddings-integrated-adoption-proof.md`
- `README.md`
- `docs/architecture.md`
- `.gsd/REQUIREMENTS.md`
