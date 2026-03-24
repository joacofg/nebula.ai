# S05: Final adoption assembly — UAT

## Scope

Validate that Nebula’s embeddings adoption story is assembled end to end as one narrow, discoverable proof package: canonical contract, realistic migration proof, durable metadata-only backend evidence, and Observability corroboration all agree without creating a second contract surface or widening scope.

## Preconditions

1. Worktree is the assembled M003/S05 state.
2. Python environment exists at `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python`.
3. Test dependencies are installed.
4. Reviewer can open and read `README.md`, `docs/architecture.md`, `docs/embeddings-adoption-contract.md`, `docs/embeddings-reference-migration.md`, and `docs/embeddings-integrated-adoption-proof.md`.
5. Reviewer can run local pytest commands from this worktree.
6. If doing a UI spot-check beyond source review, the reviewer has access to a running console and gateway plus a browser.

---

## Test Case 1 — Integrated walkthrough exists and is complete

**Purpose:** Confirm the final assembly artifact is real, non-placeholder, and structurally complete.

### Steps

1. Run:
   ```bash
   test -f docs/embeddings-integrated-adoption-proof.md
   ```
2. Run:
   ```bash
   ! grep -q "TBD\|TODO" docs/embeddings-integrated-adoption-proof.md
   ```
3. Run:
   ```bash
   [ "$(rg -c "^## " docs/embeddings-integrated-adoption-proof.md)" -ge 6 ]
   ```
4. Open `docs/embeddings-integrated-adoption-proof.md`.

### Expected outcome

- The file exists.
- It contains no placeholder markers.
- It has at least 6 second-level sections.
- It reads like a final joined walkthrough rather than planning notes.

---

## Test Case 2 — The walkthrough preserves the required proof order

**Purpose:** Confirm the assembled story follows the intended public-to-ledger-to-Observability flow.

### Steps

1. Open `docs/embeddings-integrated-adoption-proof.md`.
2. Review the sections that describe the proof sequence.
3. Confirm the document explicitly presents this order:
   1. public `POST /v1/embeddings`
   2. public `X-Request-ID` plus `X-Nebula-*` headers
   3. `GET /v1/admin/usage/ledger?request_id=...`
   4. Observability corroboration

### Expected outcome

- The public route is the first proof step.
- `X-Request-ID` and `X-Nebula-*` headers are described before any admin/UI surface.
- Usage-ledger correlation is the durable evidence seam.
- Observability is explicitly presented as subordinate corroboration.

---

## Test Case 3 — The walkthrough composes canonicals instead of replacing them

**Purpose:** Confirm S05 assembled the story without creating a second detailed public contract.

### Steps

1. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python - <<'PY'
   from pathlib import Path
   text = Path('docs/embeddings-integrated-adoption-proof.md').read_text()
   for needle in [
       'docs/embeddings-adoption-contract.md',
       'docs/embeddings-reference-migration.md',
       'What this walkthrough intentionally does not duplicate',
       'Failure modes this integrated proof makes obvious',
   ]:
       assert needle in text, needle
   PY
   ```
2. Read the “What this walkthrough intentionally does not duplicate” section.
3. Compare it with `docs/embeddings-adoption-contract.md` and `docs/embeddings-reference-migration.md`.

### Expected outcome

- The integrated walkthrough points back to the canonical contract and migration guide.
- It explicitly says what it does not duplicate.
- It does not restate full request/response semantics as a competing contract source.
- It does not replace the executable migration proof.

---

## Test Case 4 — Discoverability works from repo entry surfaces without contract duplication

**Purpose:** Confirm reviewers can find the assembled walkthrough from normal entry docs.

### Steps

1. Run:
   ```bash
   rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md
   ```
2. Review matches in `README.md`.
3. Review matches in `docs/architecture.md`.

### Expected outcome

- `README.md` links to `docs/embeddings-integrated-adoption-proof.md`.
- `docs/architecture.md` links to `docs/embeddings-integrated-adoption-proof.md`.
- Both files also point to the canonical contract/migration docs where appropriate.
- Those entry docs remain pointer-only and do not become second detailed embeddings contracts.

---

## Test Case 5 — Focused embeddings proof suite passes in the assembled worktree

**Purpose:** Confirm the final assembly still matches runtime truth.

### Steps

1. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py
   ```
2. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py
   ```
3. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings
   ```

### Expected outcome

- All commands pass.
- The integrated walkthrough’s public request, response-header, and durable evidence story matches the executable proof.
- No last-mile doc drift is present between S02/S03/S04 artifacts and the final assembled state.

---

## Test Case 6 — Requirement evidence is closed out concretely

**Purpose:** Confirm the milestone constraint requirement is validated by execution-backed evidence.

### Steps

1. Open `.gsd/REQUIREMENTS.md`.
2. Locate `R024`.
3. Review its status and validation text.

### Expected outcome

- `R024` is marked `validated`.
- Its validation text cites:
  - `docs/embeddings-integrated-adoption-proof.md`
  - discoverability from `README.md` and `docs/architecture.md`
  - passing focused embeddings pytest reruns
- The wording clearly describes narrow-scope adoption proof rather than broad embeddings parity.

---

## Test Case 7 — Human review confirms the assembled story is narrow and credible

**Purpose:** Confirm the final package reads as disciplined adoption proof rather than scope creep.

### Steps

1. Read `docs/embeddings-adoption-contract.md`.
2. Read `docs/embeddings-reference-migration.md`.
3. Read `docs/embeddings-integrated-adoption-proof.md`.
4. Judge whether each document keeps a distinct role.
5. Judge whether the assembled story avoids promising more than M003 actually delivers.

### Expected outcome

- Contract doc = detailed public boundary.
- Migration doc = realistic minimal-change caller swap.
- Integrated proof doc = final joined walkthrough.
- The assembled story does **not** imply:
  - broader OpenAI embeddings parity
  - helper SDK or wrapper rollout
  - hosted-plane expansion
  - new payload-capture or infrastructure work

---

## Test Case 8 — Optional live proof spot-check of the assembled sequence

**Purpose:** Confirm a reviewer can follow the walkthrough against real behavior, not just docs.

### Steps

1. Use the contract and migration guide to send one real `POST /v1/embeddings` request.
2. Capture `X-Request-ID` and the `X-Nebula-*` headers from the public response.
3. Query:
   ```bash
   curl "http://localhost:8000/v1/admin/usage/ledger?request_id=<captured-request-id>" \
     -H "X-Nebula-Admin-Key: <admin-key>"
   ```
4. Open Observability and locate the same request as a corroborating operator view.
5. Compare the live experience to `docs/embeddings-integrated-adoption-proof.md`.

### Expected outcome

- The live steps follow the same order described in the integrated walkthrough.
- The public response, ledger row, and Observability view tell one coherent story for the same request.
- The durable row stays metadata-only.

---

## Edge Cases To Check During Review

1. **Discoverability drift**  
   Fail the slice if the integrated walkthrough cannot be found from `README.md` or `docs/architecture.md`.

2. **Contract duplication drift**  
   Fail the slice if the integrated walkthrough, README, or architecture guide starts restating the full embeddings contract as a competing source of truth.

3. **Proof-order drift**  
   Fail the slice if the assembled story starts with Observability or treats it as more authoritative than the public route plus ledger correlation.

4. **Scope-creep drift**  
   Fail the slice if the final docs imply broader embeddings parity, helper SDK expansion, hosted-plane widening, or new infrastructure commitments.

5. **Execution drift**  
   Fail the slice if the focused embeddings pytest suite no longer passes in the assembled worktree.

---

## Pass / Fail Criteria

**Pass** if all of the following are true:

- the integrated walkthrough exists and is complete,
- the walkthrough preserves the required proof order,
- the walkthrough explicitly delegates to the canonical contract and migration proof,
- `README.md` and `docs/architecture.md` expose the walkthrough through pointer-only discoverability,
- the focused embeddings pytest suite passes,
- `R024` is validated with concrete evidence,
- the assembled story remains narrow, credible, and metadata-only.

**Fail** if any of the following occur:

- the integrated walkthrough is missing or placeholder-like,
- entry docs cannot lead a reviewer to the assembled proof,
- the final story duplicates or replaces the canonical contract,
- Observability is elevated above the public request plus ledger proof path,
- executable proof no longer matches the assembled docs,
- the final package implies broader scope than M003 actually delivered.
