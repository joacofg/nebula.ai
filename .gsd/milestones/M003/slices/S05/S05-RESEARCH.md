# S05 Research — Final adoption assembly

## Summary
- **Primary active requirement:** `R024` (owner: `M003/S05`). This slice is the milestone-wide guardrail close-out: prove the assembled embeddings adoption story stays narrow and does not drift into broader parity, SDK sprawl, hosted-plane expansion, or unrelated infrastructure.
- This is **light research**. The core patterns already exist in the repo from the chat-completions milestone and from M003 slices S02–S04. S05 should mostly **assemble existing canonicals and proof surfaces** rather than invent new runtime behavior.
- The strongest existing precedent is `docs/integrated-adoption-proof.md` for chat. S05 likely needs the **embeddings equivalent**: a final joined walkthrough that points to the canonical contract (`docs/embeddings-adoption-contract.md`), the migration proof (`docs/embeddings-reference-migration.md` + `tests/test_embeddings_reference_migration.py`), and the durable evidence/corroboration path (usage ledger + Observability).
- The loaded slice summaries already contain the critical rule: **preserve proof order**. For embeddings, the assembled story should remain:
  1. public `POST /v1/embeddings`
  2. `X-Request-ID` + `X-Nebula-*` headers
  3. `GET /v1/admin/usage/ledger?request_id=...`
  4. Observability filter/detail corroboration
- The most likely work is documentation/discoverability plus a small close-out verification artifact. Avoid new backend or console features unless the assembly exposes a concrete gap.

## Recommendation
- Build S05 as a **docs-and-proof assembly slice**, not as another implementation slice.
- Follow the established docs-composition rule from S02 and S03:
  - `docs/embeddings-adoption-contract.md` remains the **only canonical public contract**.
  - `docs/embeddings-reference-migration.md` remains the **migration proof guide**.
  - Add one **joined embeddings adoption walkthrough** that explicitly assembles, but does not redefine, those sources.
- Reuse the structure and tone of `docs/integrated-adoption-proof.md`, but keep it embeddings-specific and narrower:
  - start from the public embeddings route, not console/admin surfaces
  - explicitly subordinate Observability to the public-response + ledger path
  - include a “what this intentionally does not duplicate” section to protect R024
  - include “failure modes this assembled proof makes obvious” so drift is detectable
- Update only pointer surfaces that improve discoverability of the joined story, most likely `README.md` and possibly `docs/architecture.md`. Do not restate request/response semantics there.
- Verification should emphasize **agreement across artifacts** more than new runtime behavior.

## Implementation Landscape

### Existing files that already define the embeddings adoption story
- `docs/embeddings-adoption-contract.md`
  - Canonical `POST /v1/embeddings` contract.
  - Already names supported request shape, auth (`X-Nebula-API-Key`), success shape, headers, ledger correlation, failures, and unsupported/deferred edges.
  - This file must remain the only detailed public contract per decision `D018`.
- `docs/embeddings-reference-migration.md`
  - Human-readable before/after migration guide.
  - Already frames the minimal caller diff, the request/headers/ledger proof sequence, and explicitly warns against parity creep.
- `tests/test_embeddings_reference_migration.py`
  - Executable source of truth for the migration proof.
  - Verifies response body, `X-Request-ID`, `X-Nebula-*`, ledger correlation, and metadata-only redaction.
- `console/src/components/ledger/ledger-filters.tsx`
  - Observability filter surface already supports route target `embeddings`.
- `console/src/components/ledger/ledger-table.tsx`
  - Request ID is visible in the ledger table, which is important for correlating the public header to operator evidence.
- `console/src/components/ledger/ledger-request-detail.tsx`
  - Request detail already shows the metadata-only explanation fields needed for operator corroboration.
- `console/e2e/observability.spec.ts`
  - Encodes the intended operator corroboration path for embeddings and explicitly asserts no raw input/vector leakage.

### Best precedent for S05 assembly
- `docs/integrated-adoption-proof.md`
  - This is the chat-completions “final assembled story” precedent.
  - It does not redefine quickstart, API contract, or operating model; it stitches them together into one joined proof sequence.
  - S05 should probably mirror this pattern for embeddings rather than invent a new doc shape.

### Existing discoverability surfaces
- `README.md`
  - Already links to `docs/embeddings-adoption-contract.md` and `docs/embeddings-reference-migration.md`.
  - Does **not** currently link to an embeddings integrated/final assembly doc, because that file does not exist yet.
- `docs/architecture.md`
  - Already points to the contract and migration guide while avoiding duplication.
  - Likely candidate for one pointer-only link to any new embeddings assembly doc.

## Constraints and guardrails
- `R024` is the only active requirement in play here. S05 must prove scope discipline, not broaden the milestone.
- Decisions to preserve:
  - `D018`: contract detail stays centralized in `docs/embeddings-adoption-contract.md`.
  - `D019`: migration proof remains anchored in executable test + pointer-only human guide.
  - `D020`: Observability is corroboration of the same usage-ledger truth, not a new proof source.
- The loaded `agent-browser` guidance reinforces the same implementation stance: use explicit assertions/verification, but do not turn browser/UI work into speculative exploration. For S05, browser work should be unnecessary unless a human-verification artifact must be refreshed.
- The loaded `react-best-practices` / Next.js-related skills are not central here because the console feature work is already done; this slice should avoid fresh UI implementation unless assembly reveals an actual missing proof seam.

## Natural seams for the planner
1. **Assembly doc creation**
   - Likely new file under `docs/`, analogous to `docs/integrated-adoption-proof.md`.
   - This is the main deliverable and can be done independently first.
2. **Pointer-surface updates**
   - `README.md`
   - maybe `docs/architecture.md`
   - keep these edits discoverability-only.
3. **Requirement/close-out verification**
   - Rerun the existing embeddings proof suite and add grep/assertion checks that the new assembly doc preserves canonical boundaries and references the right sources.
   - If required by the team’s process, this is also where `R024` can be updated from `active` to `validated` once proof is assembled.

## What to build or prove first
1. **First: decide whether S05 needs a new final embeddings assembly doc.**
   - Based on current repo state, yes: chat has `docs/integrated-adoption-proof.md`, embeddings does not.
   - This is the missing “assembled milestone proof package” named in the roadmap.
2. **Second: make discoverability pointer-only.**
   - Add links without duplicating contract semantics.
3. **Third: verify artifact agreement.**
   - The important proof is that the contract, migration guide/test, and operator corroboration surfaces all describe the same narrow path.

## Verification plan
Prefer focused checks already aligned to the slice summaries:

### Runtime / proof checks
```bash
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings
```

### Source/discoverability checks
```bash
rg -n "embeddings-adoption-contract|embeddings-reference-migration|integrated-adoption-proof|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md
```

### Assembly-doc integrity checks
If a new embeddings assembly doc is added, verify:
```bash
test -f docs/<new-embeddings-assembly-doc>.md
! rg -n "TODO|TBD" docs/<new-embeddings-assembly-doc>.md
python - <<'PY'
from pathlib import Path
text = Path('docs/<new-embeddings-assembly-doc>.md').read_text()
assert 'docs/embeddings-adoption-contract.md' in text
assert 'docs/embeddings-reference-migration.md' in text
assert 'X-Request-ID' in text
assert '/v1/admin/usage/ledger' in text
assert 'Observability' in text
PY
```

### Optional console proof checks
Only if the environment supports console runners; S04 already documented these may be unavailable in this worktree:
```bash
npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx
npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx
npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx
npm --prefix console run playwright test e2e/observability.spec.ts
```
Treat missing local runners as an environment caveat, not necessarily a slice blocker, unless S05 changes console code.

## Skill discovery suggestions
Directly relevant technologies here are documentation assembly plus existing Next.js/Playwright/FastAPI surfaces. Installed project skills already cover most of this:
- Installed: `react-best-practices`
- Installed: `agent-browser`
- Installed: `test`
- Installed: `review`

Promising non-installed skills found via `npx skills find` (do not install automatically):
- Next.js: `wshobson/agents@nextjs-app-router-patterns`
- FastAPI: `wshobson/agents@fastapi-templates`
- Playwright: `currents-dev/playwright-best-practices-skill@playwright-best-practices`

These are probably unnecessary for S05 unless the slice unexpectedly expands beyond doc assembly into framework changes.

## Likely missing artifact
- There is currently **no embeddings equivalent** of `docs/integrated-adoption-proof.md`.
- That missing joined-walkthrough artifact is the clearest gap between “slice summaries exist” and “milestone adoption story is assembled end-to-end.”
- The planner should assume the primary change is creating that doc and making it discoverable while preserving the single-source-of-truth contract rule.
