# S03 UAT — Realistic migration proof

## Scope

Validate that Nebula provides a believable, narrow, minimal-change migration proof for an OpenAI-style embeddings caller using the public `POST /v1/embeddings` route, public evidence headers, and metadata-only usage-ledger correlation.

## Preconditions

1. Worktree is the assembled M003/S03 state.
2. Python environment exists at `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python`.
3. Test dependencies are installed.
4. The reviewer can read repo docs under `docs/` and run local pytest commands from this worktree.

---

## Test Case 1 — Executable migration proof passes end to end

**Purpose:** Confirm the canonical proof is executable, not just documented.

### Steps

1. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py
   ```
2. Observe the test output.

### Expected outcome

- The test passes.
- There is exactly one targeted migration-proof test.
- The proof covers a public `/v1/embeddings` request, response success, response headers, and ledger correlation.

---

## Test Case 2 — Public embeddings contract still supports the migration proof

**Purpose:** Confirm the migration proof still sits on the real supported embeddings path rather than a stale or widened contract.

### Steps

1. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py
   ```
2. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings
   ```
3. Run:
   ```bash
   /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py -k upstream_failures
   ```

### Expected outcome

- All commands pass.
- The public embeddings endpoint still behaves consistently with the migration proof assumptions.
- Upstream-failure handling remains explicit and does not silently widen or weaken the contract.

---

## Test Case 3 — Migration guide exists and is complete enough for a human evaluator

**Purpose:** Confirm there is a real human-facing migration proof artifact, not a placeholder.

### Steps

1. Run:
   ```bash
   test -f docs/embeddings-reference-migration.md
   ```
2. Run:
   ```bash
   ! grep -q "TBD\|TODO" docs/embeddings-reference-migration.md
   ```
3. Run:
   ```bash
   [ "$(rg -c "^## " docs/embeddings-reference-migration.md)" -ge 6 ]
   ```
4. Open `docs/embeddings-reference-migration.md` and inspect its sections.

### Expected outcome

- The file exists.
- It contains no `TBD` or `TODO` markers.
- It has at least 6 second-level sections.
- It reads like a real migration guide, not planning notes.

---

## Test Case 4 — Guide names the actual proof and evidence path

**Purpose:** Confirm the guide is grounded in runtime truth and points reviewers to the real proof surfaces.

### Steps

1. Run:
   ```bash
   rg -n "tests/test_embeddings_reference_migration.py|X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|What this migration proves|What not to use as migration proof" docs/embeddings-reference-migration.md
   ```
2. Review the matched lines in `docs/embeddings-reference-migration.md`.

### Expected outcome

- The guide explicitly names `tests/test_embeddings_reference_migration.py` as the source of truth.
- The guide explicitly references `X-Nebula-API-Key` auth.
- The guide instructs reviewers to inspect `X-Request-ID`.
- The guide points to `GET /v1/admin/usage/ledger?request_id=...` for durable evidence.
- The guide has a “What this migration proves” section.
- The guide has a “What not to use as migration proof” section.

---

## Test Case 5 — Discoverability works without creating a second contract source

**Purpose:** Confirm readers can find the migration guide while `docs/embeddings-adoption-contract.md` remains canonical.

### Steps

1. Run:
   ```bash
   rg -n "embeddings-reference-migration" docs/embeddings-adoption-contract.md README.md docs/architecture.md docs/*.md
   ```
2. Review the matching references.

### Expected outcome

- `docs/embeddings-adoption-contract.md` links to the migration guide as a subordinate proof/walkthrough.
- `README.md` points readers to the migration guide.
- `docs/architecture.md` points readers to the migration guide.
- None of those files restate the full embeddings contract inline as a competing source of truth.

---

## Test Case 6 — The executable proof uses a realistic minimal caller shape

**Purpose:** Confirm the migration proof is believable and narrow rather than a Nebula-specific demo.

### Steps

1. Open `tests/test_embeddings_reference_migration.py`.
2. Verify the request body uses:
   - `model`
   - `input` as a flat list of strings
3. Verify the public request is sent to `/v1/embeddings`.
4. Verify auth uses `X-Nebula-API-Key`.
5. Verify the proof captures `X-Request-ID` and queries `/v1/admin/usage/ledger?request_id=...`.

### Expected outcome

- The proof uses the real public endpoint.
- The request shape stays inside the documented narrow contract.
- The proof does not use unsupported options like `encoding_format`.
- The proof does not rely on helper wrappers or console-only flows.

---

## Test Case 7 — Durable evidence stays metadata-only

**Purpose:** Confirm the proof does not imply raw inputs or embeddings are persisted.

### Steps

1. Open `tests/test_embeddings_reference_migration.py`.
2. Inspect the final assertions against the ledger response.
3. Confirm the test asserts the absence of:
   - `input`
   - `inputs`
   - `embedding`
   - `embeddings`
4. Confirm the test asserts raw input text is not present in serialized ledger data.
5. Confirm the test asserts returned embedding vectors are not present in serialized ledger data.

### Expected outcome

- The proof explicitly enforces the metadata-only persistence boundary.
- The slice does not weaken Nebula's evidence/redaction guardrail.

---

## Test Case 8 — Human credibility review of the migration guide

**Purpose:** Confirm the guide reads as a believable engineering migration proof.

### Steps

1. Read `docs/embeddings-reference-migration.md` from top to bottom.
2. Judge whether the before/after example is a realistic provider-to-Nebula swap.
3. Judge whether the guide is honest about what changed.
4. Judge whether the guide is honest about what is out of scope.

### Expected outcome

- The guide reads as a plausible migration for a team already using the OpenAI Python client.
- The diff is narrow and specific.
- The guide does not oversell parity.
- The guide does not imply bearer auth, helper SDKs, or broad embeddings-option support.
- The guide clearly distinguishes migration proof from broader contract definition.

---

## Edge Cases To Check During Review

1. **False proof by docs only**  
   Reject the slice if the guide exists but the executable pytest proof fails.

2. **False proof by response only**  
   Reject the slice if the embeddings response succeeds but no `X-Request-ID`/ledger correlation path is present.

3. **Contract drift**  
   Reject the slice if the migration guide starts describing unsupported auth modes, unsupported request options, or broader embeddings parity.

4. **Persistence-boundary drift**  
   Reject the slice if tests or docs imply ledger persistence of raw input text or returned vectors.

5. **Discoverability drift**  
   Reject the slice if the migration guide cannot be found from key docs, or if entry docs start duplicating the canonical embeddings contract.

---

## Pass / Fail Criteria

**Pass** if all of the following are true:

- all four pytest verification commands pass,
- the migration guide exists and contains the required proof/evidence sections,
- discoverability links are present,
- the executable proof enforces public-header plus ledger correlation,
- the metadata-only persistence boundary is preserved,
- the guide remains narrow and credible.

**Fail** if any of the following occur:

- the executable proof fails,
- the migration guide is incomplete or placeholder-like,
- the proof stops at the public response and omits durable evidence,
- docs imply parity or auth support beyond the canonical contract,
- raw inputs or embedding vectors appear in durable evidence expectations.
