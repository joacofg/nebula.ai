---
milestone_id: M003
title: Broader Adoption Surface
status: completed
verification_status: passed
summary_date: 2026-03-23
branch: milestone/M003
integration_branch: codex/v3-api-adoption
code_change_verification:
  diff_base: codex/v3-api-adoption
  command: git diff --stat HEAD $(git merge-base HEAD codex/v3-api-adoption) -- ':!.gsd/'
  result: passed
  notes: Non-.gsd changes are present across backend, docs, tests, and console Observability surfaces.
requirement_outcomes:
  - requirement_id: R020
    from_status: active
    to_status: validated
    proof: S01 delivered and close-out reverified a real authenticated POST /v1/embeddings route with passing tests in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and service-flow coverage cited by the slice summary.
  - requirement_id: R021
    from_status: active
    to_status: validated
    proof: S02 established docs/embeddings-adoption-contract.md as the canonical embeddings contract, with discoverability via README.md and docs/architecture.md and focused runtime/doc alignment checks cited in the slice summary.
  - requirement_id: R022
    from_status: active
    to_status: validated
    proof: S03 added tests/test_embeddings_reference_migration.py plus docs/embeddings-reference-migration.md and close-out reran the migration and embeddings pytest checks successfully.
  - requirement_id: R023
    from_status: active
    to_status: validated
    proof: S04 extended shared Observability ledger surfaces for embeddings request correlation and kept the durable proof path on X-Request-ID plus metadata-only usage-ledger evidence, with close-out pytest reruns passing.
  - requirement_id: R024
    from_status: active
    to_status: validated
    proof: S05 assembled the integrated walkthrough in docs/embeddings-integrated-adoption-proof.md, kept the canonical contract pointer-only in entry docs, and close-out reran focused embeddings proof checks successfully.
---

# Milestone Summary — M003: Broader Adoption Surface

## Milestone outcome

**Status:** Complete  
**Verification status:** Passed

M003 successfully widened Nebula's adoption story beyond chat completions by adding a narrow, test-backed public embeddings surface and assembling the full proof path around it. The assembled milestone now provides:

- a real authenticated public `POST /v1/embeddings` entrypoint,
- one canonical embeddings contract document,
- a realistic minimal-change migration proof for an OpenAI-style caller,
- durable metadata-only backend evidence correlated by `X-Request-ID`, and
- operator-side corroboration through shared Observability ledger surfaces.

Code-change verification also passed. Running `git diff --stat HEAD $(git merge-base HEAD codex/v3-api-adoption) -- ':!.gsd/'` showed non-`.gsd` changes in backend route/service/model code, docs, tests, and console Observability surfaces, so this milestone did not produce planning-only output.

## Verification performed

### Code change verification

Verified with:

- `git diff --stat HEAD $(git merge-base HEAD codex/v3-api-adoption) -- ':!.gsd/'`

Result:

- passed — non-`.gsd` changes exist in `src/nebula/...`, `docs/...`, `tests/...`, `README.md`, `docs/architecture.md`, and `console/...`.

### Focused executable verification rerun

Re-ran the milestone-critical proof suite in the assembled worktree:

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py` → passed
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` → passed
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` → passed

### Artifact/integration presence checks

Confirmed milestone-critical assembled artifacts and surfaces exist in the current worktree:

- `src/nebula/api/routes/embeddings.py`
- `docs/embeddings-adoption-contract.md`
- `docs/embeddings-reference-migration.md`
- `docs/embeddings-integrated-adoption-proof.md`
- `tests/test_embeddings_api.py`
- `tests/test_embeddings_reference_migration.py`
- `console/src/components/ledger/ledger-filters.tsx`
- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/e2e/observability.spec.ts`

## Success criteria verification

### 1) A team can point a common OpenAI-style embeddings caller at Nebula through `POST /v1/embeddings` with minimal changes and receive a usable embeddings response within the documented narrow contract.

**Result:** Met

**Evidence:**

- S01 added the authenticated public `POST /v1/embeddings` route with a narrow request boundary (`model` + string or flat list-of-strings `input`) and OpenAI-style float-vector responses.
- S03 added `tests/test_embeddings_reference_migration.py` as an executable minimal-change migration proof and `docs/embeddings-reference-migration.md` as the human-readable guide.
- Close-out reran `tests/test_embeddings_reference_migration.py` and `tests/test_embeddings_api.py`, both of which passed.

### 2) Nebula documents the embeddings adoption boundary canonically, including explicit unsupported or deferred edges, and the migration proof matches runtime truth.

**Result:** Met

**Evidence:**

- S02 established `docs/embeddings-adoption-contract.md` as the single canonical public embeddings contract and updated `README.md` plus `docs/architecture.md` to stay pointer-only.
- S02 summary records runtime/doc alignment for request shape, auth, response shape, headers, ledger correlation, and explicit `401` / `422` / `502` failure classes.
- S03 grounded the migration guide in the executable proof rather than prose alone.
- The canonical contract, migration guide, and runtime tests all still exist in the assembled worktree.

### 3) An embeddings adoption request can be tied to durable backend/operator evidence so teams can explain what happened during evaluation without new helper layers.

**Result:** Met

**Evidence:**

- S01 established `X-Request-ID` emission and request-id correlation through `GET /v1/admin/usage/ledger?request_id=...` with metadata-only persistence.
- S04 extended shared Observability ledger surfaces so operators can filter to `embeddings`, see `request_id`, and inspect persisted outcome fields without a new admin API or new storage.
- S03 and S04 both preserve the proof order: public response → request id / headers → usage ledger → Observability corroboration.
- Close-out reran `tests/test_embeddings_reference_migration.py` and `tests/test_embeddings_api.py` successfully, reinforcing the durable evidence path.

### 4) The assembled milestone widens the adoption story without adding broad parity work, SDK sprawl, hosted-plane expansion, or unrelated infrastructure work.

**Result:** Met

**Evidence:**

- S01 kept the public embeddings contract intentionally narrow and avoided chat-orchestration reuse or broader option parity.
- S02 documented explicit unsupported/deferred edges such as bearer auth, `encoding_format`, alternate encodings, and broader parity claims.
- S03 reused an OpenAI-style client pattern instead of introducing helper SDKs or wrappers.
- S04 extended existing ledger/admin surfaces rather than adding embeddings-specific storage or a new admin API family.
- S05 assembled the proof package composition-first and validated R024 with focused pytest reruns and pointer-only entry-doc discoverability.

### Success criteria not met

- None.

## Definition of done verification

### Slice completion and summary presence

**Result:** Met

Verified all roadmap slices are complete and summaries exist for:

- `S01`
- `S02`
- `S03`
- `S04`
- `S05`

The milestone directory contains all expected slice summary files and supporting roadmap/context artifacts.

### Cross-slice integration verification

**Result:** Met

Verified that the key integration points described in the roadmap are present and coherent:

- **S01 → S02:** runtime embeddings route exists and is the basis for the canonical contract doc.
- **S01 → S03:** stable public embeddings path and auth model are used by the realistic migration proof.
- **S01 → S04:** `X-Request-ID` and usage-ledger correlation are reused as the durable evidence seam.
- **S02/S03/S04 → S05:** final integrated walkthrough composes the canonical contract, realistic migration proof, and operator corroboration without replacing any canonical source.

The assembled worktree still contains all milestone-critical docs, tests, route code, and shared Observability surfaces required for the joined story.

### Integrated acceptance

**Result:** Passed

Integrated acceptance is supported by:

- passing focused embeddings pytest reruns,
- assembled artifact presence checks,
- requirement evidence from each slice summary, and
- confirmation that the final worktree still contains the runtime, docs, proof, and operator corroboration surfaces that the milestone depends on.

## Requirement status transitions validation

The following requirement transitions are supported by milestone evidence and remain valid:

- **R020:** active → validated
  - Supported by S01 runtime delivery and close-out reruns of `tests/test_embeddings_api.py` and `tests/test_governance_api.py -k embeddings`.
- **R021:** active → validated
  - Supported by S02 canonical contract delivery in `docs/embeddings-adoption-contract.md` and documented discoverability/runtime-alignment checks.
- **R022:** active → validated
  - Supported by S03 executable migration proof in `tests/test_embeddings_reference_migration.py` and `docs/embeddings-reference-migration.md`, plus rerun pytest confirmation.
- **R023:** active → validated
  - Supported by S04 durable evidence correlation through request-id, metadata-only usage ledger, and shared Observability surfaces.
- **R024:** active → validated
  - Supported by S05 integrated walkthrough assembly, focused rerun verification, and sustained scope guardrails.

No additional requirement status changes were justified beyond those already recorded for M003.

## Cross-cutting lessons from the milestone

The most reusable patterns from M003 were:

- keep new public adoption surfaces narrow and directly wired to the underlying service instead of forcing reuse through broader orchestration layers,
- preserve one canonical contract document and keep README/architecture entry docs pointer-only,
- treat migration proof as incomplete unless the same public response is correlated to durable metadata-only backend evidence,
- extend shared operator surfaces for corroboration instead of creating route-specific UI or storage,
- treat the proof order itself as part of the contract: public request → headers → usage ledger → Observability.

## Gaps / caveats

No milestone-blocking gaps remain for M003 close-out.

Console-specific Vitest/Playwright reruns were previously noted in slice summaries as partially environment-constrained, but the milestone-critical backend proof suite was rerun successfully in this assembled worktree, and the required console/operator surfaces remain present in source.

## Final assessment

M003 passes close-out verification. Nebula now has a real, narrow, and credibly documented embeddings adoption surface that is backed by executable proof and durable operator-visible evidence without drifting into broader parity or infrastructure scope.
