---
estimated_steps: 5
estimated_files: 7
skills_used:
  - test
  - review
---

# T02: Wire discoverability and close out R024 evidence

**Slice:** S05 — Final adoption assembly
**Milestone:** M003

## Description

Make the final embeddings assembly doc discoverable from the repo’s main entry surfaces and use it to close out the milestone guardrail requirement. This task should keep `README.md` and `docs/architecture.md` pointer-only, re-run the focused embeddings proof suite, and then update `R024` in `.gsd/REQUIREMENTS.md` with validation evidence grounded in the new integrated walkthrough plus the existing executable tests. The intent is to prove that the assembled story is complete and still narrow, not to add new runtime capabilities.

## Steps

1. Read `README.md`, `docs/architecture.md`, and `docs/embeddings-integrated-adoption-proof.md` so discoverability edits stay pointer-only and consistent with the new assembly document.
2. Add concise links in `README.md` and `docs/architecture.md` to `docs/embeddings-integrated-adoption-proof.md` without restating detailed embeddings request/response, auth, or failure semantics.
3. Re-run the focused embeddings verification commands and repo-wide source checks that prove the contract, migration guide, integrated walkthrough, and evidence surfaces still agree.
4. If verification exposes wording drift, make minimal fixes in `docs/embeddings-integrated-adoption-proof.md` so the assembled proof package stays aligned.
5. Update `R024` in `.gsd/REQUIREMENTS.md` from `active` to `validated` with concrete verification text citing `docs/embeddings-integrated-adoption-proof.md` and the focused rerun commands.

## Must-Haves

- [ ] `README.md` and `docs/architecture.md` point to `docs/embeddings-integrated-adoption-proof.md` as a discoverability layer without becoming a second detailed embeddings contract.
- [ ] `.gsd/REQUIREMENTS.md` records `R024` as validated with evidence tied to the integrated walkthrough and the focused embeddings verification suite.

## Verification

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- `rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md && rg -n "R024|validated|embeddings-integrated-adoption-proof" .gsd/REQUIREMENTS.md`

## Observability Impact

- Signals added/changed: documentation-level discoverability of the final embeddings proof path and requirement-state evidence for the milestone guardrail.
- How a future agent inspects this: read `README.md`, `docs/architecture.md`, `docs/embeddings-integrated-adoption-proof.md`, and the `R024` entry in `.gsd/REQUIREMENTS.md`; rerun the focused pytest/doc grep commands.
- Failure state exposed: broken doc links, duplicated contract language, or an `R024` validation claim that is not backed by the listed proof artifacts.

## Inputs

- `README.md` — repo-level documentation map and endpoint inventory that should expose the final walkthrough.
- `docs/architecture.md` — pointer-only architecture/discoverability surface for embeddings adoption.
- `docs/embeddings-integrated-adoption-proof.md` — new final assembly doc produced by T01.
- `tests/test_embeddings_reference_migration.py` — executable migration proof to rerun.
- `tests/test_embeddings_api.py` — public embeddings contract coverage to rerun.
- `tests/test_governance_api.py` — ledger/admin embeddings evidence coverage to rerun.
- `.gsd/REQUIREMENTS.md` — requirement registry where `R024` validation must be recorded.

## Expected Output

- `README.md` — pointer-only link to the embeddings integrated adoption walkthrough.
- `docs/architecture.md` — pointer-only mention of the final embeddings assembly walkthrough.
- `docs/embeddings-integrated-adoption-proof.md` — minimally aligned final walkthrough if verification requires wording fixes.
- `.gsd/REQUIREMENTS.md` — `R024` updated to `validated` with concrete proof references.
