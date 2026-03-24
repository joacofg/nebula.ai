# S05: Final adoption assembly — Summary

## Slice Summary

**Status:** Complete  
**Milestone:** M003  
**Slice Goal:** Assemble the full embeddings adoption story into one narrow, end-to-end proof package that joins the canonical contract, realistic migration path, and durable evidence/corroboration flow without widening Nebula into broader embeddings parity, SDK sprawl, hosted-plane expansion, or unrelated infrastructure work.

### What this slice actually delivered

S05 closed M003 by turning the already-built embeddings pieces into one discoverable, verification-backed adoption story.

The assembled result is:

- `docs/embeddings-integrated-adoption-proof.md` now exists as the embeddings-specific final walkthrough
- the walkthrough preserves the intended proof order:
  1. public `POST /v1/embeddings`
  2. `X-Request-ID` plus `X-Nebula-*` headers
  3. `GET /v1/admin/usage/ledger?request_id=...`
  4. Observability as subordinate corroboration
- `docs/embeddings-adoption-contract.md` remains the only detailed public contract
- `docs/embeddings-reference-migration.md` and `tests/test_embeddings_reference_migration.py` remain the canonical migration proof sources
- `README.md` and `docs/architecture.md` now expose the integrated walkthrough through pointer-only discoverability links rather than duplicating request/auth/failure semantics
- focused executable proof was rerun in the assembled worktree and passed:
  - `tests/test_embeddings_reference_migration.py`
  - `tests/test_embeddings_api.py`
  - `tests/test_governance_api.py -k embeddings`
- `R024` is validated with concrete evidence tied to the walkthrough, discoverability surfaces, and rerun proof checks

This means M003 now reads as one coherent adoption package instead of four adjacent slice artifacts: a reviewer can start from the public endpoint, verify public evidence, confirm durable metadata-only backend correlation, and then use Observability as operator corroboration without confusing any of those layers for a broader parity promise.

### Key implementation and documentation patterns established

1. **Final assembly docs should compose canonicals, not replace them.**  
   `docs/embeddings-integrated-adoption-proof.md` is intentionally composition-first. It assembles the story while delegating detailed API semantics to `docs/embeddings-adoption-contract.md` and realistic caller-diff details to `docs/embeddings-reference-migration.md` plus `tests/test_embeddings_reference_migration.py`.

2. **Discoverability surfaces should stay pointer-only.**  
   `README.md` and `docs/architecture.md` now help readers find the final walkthrough, but they do not restate the embeddings contract inline. That keeps the canonical public boundary narrow and reduces drift risk.

3. **The proof order is itself part of the contract.**  
   The assembled story only works if it stays ordered as public request -> public headers -> usage ledger -> Observability. If a future change starts with Observability or treats it as more authoritative than the public route plus ledger, that is adoption-proof drift.

4. **Requirement close-out should cite joined evidence, not just doc existence.**  
   R024 was not closed by adding one doc alone. It was closed by combining discoverability links, the integrated walkthrough, and passing focused embeddings proof reruns.

### Scope / guardrail outcome

S05 preserved the milestone guardrails:

- no broad embeddings parity claims
- no helper SDK or wrapper expansion
- no new hosted-plane responsibilities
- no new backend or console infrastructure family
- no second drifting embeddings contract surface
- no widening of persistence beyond metadata-only usage-ledger evidence

The slice therefore validates the milestone’s final constraint story rather than reopening scope.

### Verification run for close-out

All slice-level verification passed in this worktree:

#### Passed
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- `test -f docs/embeddings-integrated-adoption-proof.md && ! grep -q "TBD\|TODO" docs/embeddings-integrated-adoption-proof.md && [ "$(rg -c "^## " docs/embeddings-integrated-adoption-proof.md)" -ge 6 ]`
- content assertion on `docs/embeddings-integrated-adoption-proof.md` for:
  - `docs/embeddings-adoption-contract.md`
  - `docs/embeddings-reference-migration.md`
  - `POST /v1/embeddings`
  - `X-Request-ID`
  - `/v1/admin/usage/ledger`
  - `Observability`
  - `What this walkthrough intentionally does not duplicate`
  - `Failure modes this integrated proof makes obvious`
- `rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md`

### Observability / diagnostics confirmed

The slice plan required confirmation of the named proof and corroboration surfaces. They are aligned in the assembled worktree:

- public embeddings responses expose `X-Request-ID` and `X-Nebula-*` headers
- `GET /v1/admin/usage/ledger?request_id=...` remains the durable metadata-only correlation seam
- `console/e2e/observability.spec.ts` remains the operator corroboration proof surface referenced by the integrated walkthrough
- `docs/embeddings-integrated-adoption-proof.md` explicitly keeps Observability subordinate to the public request and usage-ledger proof path

### Requirement impact

- **R024** is validated in the assembled worktree.
- **R021, R022, and R023** are reinforced by the final composed proof path and its discoverability, but their underlying slice-owned sources remain unchanged.

### Decisions and knowledge worth carrying forward

- Final assembly docs should name failure modes that reveal proof drift or scope drift rather than silently assuming the reader will infer them.
- For narrow adoption milestones, pointer-only repo entry surfaces are a feature, not a weakness: they make the final proof discoverable while protecting the canonical contract from duplication.
- Requirement validation at milestone close-out is stronger when it cites both executable reruns and the integrated walkthrough that explains how to interpret those reruns.

### What downstream roadmap work should know

M003 is now assembled as one narrow embeddings adoption story:

1. **Public contract:** `docs/embeddings-adoption-contract.md`
2. **Realistic migration proof:** `docs/embeddings-reference-migration.md` + `tests/test_embeddings_reference_migration.py`
3. **Durable evidence and operator corroboration:** `GET /v1/admin/usage/ledger?request_id=...` + Observability surfaces
4. **Final joined walkthrough:** `docs/embeddings-integrated-adoption-proof.md`

Any future slice that builds on embeddings adoption should preserve those roles instead of collapsing them together. If a later milestone needs broader embeddings semantics, helper ergonomics, or richer hosted/operator surfaces, it should be framed as a new explicit scope expansion rather than an implied continuation of M003.

## UAT Summary

This slice is ready for human validation as a final assembly review. A reviewer should be able to:

1. Find the integrated walkthrough from `README.md` and `docs/architecture.md`.
2. Confirm the walkthrough points back to the canonical contract and migration proof instead of duplicating them.
3. Follow the proof order from public `POST /v1/embeddings` to `X-Request-ID` / `X-Nebula-*` headers to `GET /v1/admin/usage/ledger?request_id=...` to Observability corroboration.
4. Confirm the walkthrough names failure modes that would indicate proof drift or scope drift.
5. Confirm the focused embeddings proof suite passes in the assembled worktree.
6. Confirm the assembled story still preserves the narrow metadata-only, no-parity-creep adoption boundary.
