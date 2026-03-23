# UAT — S05 Final integrated adoption proof

## Preconditions
1. Work from this repository with the S05 slice changes present.
2. For doc-only validation, no services are required.
3. For runtime validation, have the Nebula gateway and console available through the project’s normal local setup.
4. For backend automated validation, ensure Python test tooling is installed so `python3 -m pytest ...` can run.
5. For console unit validation, ensure `console` dependencies are installed.
6. For browser e2e validation, ensure the console can compile cleanly and Playwright can start its web server.

## Test Case 1 — Discover the canonical integrated proof entry point
**Purpose:** Confirm a reader can find one final integrated walkthrough without the repo duplicating the API contract or production model.

### Steps
1. Open `README.md`.
2. Find the documentation entry that points to the integrated adoption proof.
3. Open `docs/integrated-adoption-proof.md`.
4. Verify the document links back to `docs/adoption-api-contract.md` and `docs/production-model.md` instead of restating those contracts in full.

### Expected outcomes
- `README.md` makes the integrated adoption proof discoverable.
- `docs/integrated-adoption-proof.md` exists and is clearly the canonical final walkthrough.
- The integrated doc composes existing canonicals rather than replacing or duplicating them.

## Test Case 2 — Verify the proof order is public request first, operator surfaces second
**Purpose:** Ensure the joined story remains runtime-truthful and does not accidentally position Playground as the adoption target.

### Steps
1. In `docs/integrated-adoption-proof.md`, locate the ordered walkthrough.
2. Confirm the first proof step is a real public `POST /v1/chat/completions` request.
3. Confirm the next proof step inspects `X-Nebula-*` headers and `X-Request-ID`.
4. Confirm the next proof step correlates the request through the usage ledger.
5. Confirm Playground appears only after ledger correlation.
6. Confirm Observability appears after Playground as the persisted explanation plus dependency-health surface.

### Expected outcomes
- The ordering is exactly public request → headers / `X-Request-ID` → usage ledger → Playground → Observability.
- Playground is described as corroboration only.
- Observability is described as persisted explanation and dependency health, not as the initial proof seam.

## Test Case 3 — Backend proof still correlates request headers to operator evidence
**Purpose:** Validate the integrated backend proof seam remains executable.

### Steps
1. Run:
   `python3 -m pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_chat_completions.py tests/test_response_headers.py -q`
2. If the command cannot run because `pytest` is unavailable, record the exact tooling error.
3. If the command runs, inspect failures for whether they indicate contract drift or ordinary test breakage.

### Expected outcomes
- In a provisioned environment, the suite passes.
- If `pytest` is missing, the result is recorded as an environment gap rather than product regression.
- The proof seam being exercised is public-response headers plus `X-Request-ID` correlated to admin ledger evidence.

## Test Case 4 — Playground unit proof surfaces remain aligned
**Purpose:** Confirm the console still exposes immediate corroboration for the same request story.

### Steps
1. Run:
   `npm --prefix console run test -- --run playground-metadata`
2. Run:
   `npm --prefix console run test -- --run playground-recorded-outcome`
3. Run:
   `npm --prefix console run test -- --run playground`
4. Review the passing tests and confirm they cover request metadata, recorded outcome, and page framing.

### Expected outcomes
- All three commands pass.
- Playground test coverage confirms immediate metadata and recorded outcome presentation are intact.
- No test asserts or implies that Playground is the public adoption target.

## Test Case 5 — Observability unit proof seam exists and validates integrated framing
**Purpose:** Confirm the previous missing `observability` unit-test target now resolves to a real test.

### Steps
1. Run:
   `npm --prefix console run test -- --run observability`
2. Inspect the matching test file if needed.
3. Confirm the test asserts the persisted request explanation copy and dependency-health framing.

### Expected outcomes
- The command passes instead of failing with “No test files found”.
- The matching test file is `console/src/app/(console)/observability/observability-page.test.tsx`.
- The test confirms copy that references correlation via public `X-Request-ID` and `X-Nebula-*` headers and confirms dependency-health messaging.

## Test Case 6 — Browser-level operator proof remains scripted
**Purpose:** Confirm the Playwright coverage still tells the same joined story at the UI layer.

### Steps
1. Run:
   `npm --prefix console run e2e -- --grep "playground|observability"`
2. If the command fails before tests execute, capture the first blocking error.
3. If the command runs, verify the Playground and Observability assertions match the integrated wording.

### Expected outcomes
- In a clean environment, the targeted Playwright specs pass.
- In this worktree, a failure caused by unrelated compile issues outside the S05 surfaces should be recorded as a broader blocker, not as slice regression.
- The specs should preserve the intended wording split between Playground and Observability.

## Test Case 7 — Requirement and knowledge records reflect final closure
**Purpose:** Ensure milestone bookkeeping matches what S05 actually proved.

### Steps
1. Open `.gsd/REQUIREMENTS.md`.
2. Locate `R003`.
3. Confirm its validation text references the integrated adoption proof, backend request-correlation tests, and aligned console proof surfaces.
4. Open `.gsd/KNOWLEDGE.md`.
5. Confirm the S05 entries describe final integrated proof wording and verification-gap handling.

### Expected outcomes
- `R003` contains concrete S05 closure evidence.
- Knowledge entries capture the operator proof ordering and how to treat missing runners vs unrelated blockers.

## Edge Case Checks
### Edge Case A — Missing targeted test file
1. Run `npm --prefix console run test -- --run observability`.
2. Confirm it no longer fails with “No test files found”.

**Expected:** The gap is closed by a concrete Observability test file.

### Edge Case B — Missing Python tooling
1. Run the targeted pytest command in an environment without pytest.
2. Confirm the resulting error is `No module named pytest`.

**Expected:** The result is logged as an environment gap, not as evidence that backend integrated proof changed.

### Edge Case C — Unrelated console compile blocker
1. Run the targeted Playwright command in a worktree with an unrelated Next.js TypeScript error outside S05 files.
2. Confirm the failure is attributed to that blocker rather than to Playground/Observability proof drift.

**Expected:** The blocker is treated as external to the slice’s proof surfaces unless evidence points otherwise.
