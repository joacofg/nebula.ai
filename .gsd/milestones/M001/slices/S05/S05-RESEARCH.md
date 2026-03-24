# M001/S05 — Research

**Date:** 2026-03-23

## Summary

S05 is a targeted integration slice, not a new-product slice. The remaining active requirement pressure is centered on **R003** (prove the documented happy path is actually completable in practice), while S05 also supports already-validated but still integration-sensitive work from **R004**, **R005**, and **R009** by exercising the joined system end to end. The repo already contains the canonical adoption composition from S02 (`docs/quickstart.md`, `docs/production-model.md`, `docs/adoption-api-contract.md`), the executable migration proof from S03 (`tests/test_reference_migration.py`, `docs/reference-migration.md`), and the day-1 value proof plus console surfaces from S04 (`docs/day-1-value.md`, Playground metadata/recorded outcome, Observability request explanation). The gap is final integration proof that these artifacts align as one adoption walkthrough rather than as adjacent slice outputs.

Recommendation: keep S05 narrow and runtime-truthful. Do not invent new API surface, new demo flows, or broader compatibility claims. Instead, add one canonical integrated proof document plus one executable verification seam that walks the exact adoption order locked in by prior slices: quickstart → public chat request → `X-Nebula-*` + `X-Request-ID` evidence → usage-ledger correlation → operator corroboration through Playground/Observability. Preserve the S02 composition rule and S04 proof ordering. Explicitly record environment-gated verification where local toolchains are missing rather than treating that as product evidence.

## Recommendation

Treat S05 as **assembly + proof**, not feature development.

Build one canonical integrated adoption walkthrough rooted in the existing docs and one integrated verification layer rooted in existing tests/surfaces. Follow the already-established rules from prior slices:
- from S02: keep `docs/quickstart.md` as the only happy-path walkthrough, `docs/production-model.md` as the operating model, and `docs/adoption-api-contract.md` as the only public API contract
- from S03/D009: keep the migration proof narrow, using base URL + `X-Nebula-API-Key` by default, adding `X-Nebula-Tenant-ID` only for ambiguous multi-tenant keys, and proving success by correlating `X-Request-ID`/`X-Nebula-*` headers to `GET /v1/admin/usage/ledger`
- from S04/D010: keep the proof flow public-request-first, then headers/request-id, then ledger correlation, with Playground and Observability only as operator corroboration surfaces
- from the installed `react-best-practices` / `agent-browser` guidance already available in the environment: prefer reusing existing React/data-fetching seams and existing browser/e2e proof surfaces rather than inventing new UI state or one-off operator pages

The likely natural split is: (1) docs assembly, (2) backend/integration verification, (3) console/e2e verification alignment, (4) milestone/requirement closure updates. Build/prove docs assembly first because it defines the canonical sequence all verification should follow.

## Implementation Landscape

### Key Files

- `docs/quickstart.md` — canonical happy-path self-hosted walkthrough. Already includes first public request, header inspection, usage ledger, Playground, and Observability references. S05 should reuse it, not duplicate it.
- `docs/reference-migration.md` — canonical migration proof rooted in `tests/test_reference_migration.py`; already defines the narrow caller diff and request-id/ledger correlation pattern.
- `docs/day-1-value.md` — canonical operator-visible value proof; already defines the exact proof sequence S05 should preserve.
- `docs/adoption-api-contract.md` — only canonical public API contract. S05 should link to it instead of restating request/response semantics.
- `docs/production-model.md` — runtime-truth reference for tenant/policy/API key/operator vs conceptual app/workload. Use this to keep the integrated proof honest.
- `README.md` — current top-level documentation map. Likely needs a small integration-oriented entry-point/link update once the final integrated proof exists.
- `tests/test_reference_migration.py` — strongest existing executable seam for public request + header + ledger correlation. Best starting point for integrated backend proof.
- `tests/test_admin_playground_api.py` — proves Playground remains admin-only, non-streaming, and ledger-correlatable. Important to preserve boundary clarity in S05.
- `tests/test_governance_api.py` — already covers ledger terminal statuses, policy denials, cache/fallback outcomes, and policy/runtime truth. Useful integrated regression coverage.
- `console/src/app/(console)/playground/page.tsx` — orchestrates Playground request, immediate metadata card, and recorded-outcome lookup by `requestId`.
- `console/src/components/playground/playground-metadata.tsx` — renders immediate response evidence fields (request id, tenant, route target/reason, provider, policy mode/outcome, cache, fallback, latency).
- `console/src/components/playground/playground-recorded-outcome.tsx` — renders persisted ledger evidence for the same request.
- `console/src/app/(console)/observability/page.tsx` — frames Observability as persisted request explanation plus dependency health.
- `console/src/components/ledger/ledger-request-detail.tsx` — request-detail explanation language; important for S05’s “joined system” proof.
- `console/e2e/playground.spec.ts` — already exercises operator metadata + recorded outcome together.
- `console/e2e/observability.spec.ts` — already exercises ledger filtering and dependency-health explanation.
- `.gsd/REQUIREMENTS.md` — R003 is still active; S05 likely needs to update its validation once final integrated proof exists.
- `.gsd/KNOWLEDGE.md` — should capture any final integration lessons, especially around proof ordering and environment gaps.

### Build Order

1. **Define the canonical integrated walkthrough first**
   - Add/update a final S05-facing document that stitches together the existing canonicals without duplicating their contracts.
   - This unblocks all executor work because tests and entry-point links need one agreed sequence to assert.

2. **Extend the backend proof path second**
   - Start from `tests/test_reference_migration.py` and existing governance/admin-playground seams.
   - Goal: prove one realistic adoption chain remains coherent from public request to operator evidence, without widening scope.

3. **Align console/e2e proof third**
   - Reuse existing Playground and Observability tests/components.
   - Only add assertions or small copy/link adjustments needed to make the joined adoption story explicit; avoid new product surfaces.

4. **Close milestone bookkeeping last**
   - Update `README.md` / requirement validation / knowledge only after the canonical proof artifact and executable seams are stable.

### Verification Approach

Primary verification should remain composition-based and reuse existing suites:

- Backend/integration:
  - `python3 -m pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_chat_completions.py tests/test_response_headers.py -q`
  - targeted subset if needed: `python3 -m pytest tests/test_reference_migration.py -k "tenant_header or request_id or ledger" -q`
- Console component/integration:
  - `npm --prefix console run test -- --run playground-metadata`
  - `npm --prefix console run test -- --run playground-recorded-outcome`
  - `npm --prefix console run test -- --run playground`
  - `npm --prefix console run test -- --run observability`
- Console e2e:
  - `npm --prefix console run e2e -- --grep "playground|observability"`
- Doc/link integrity:
  - `rg -n "quickstart|reference migration|day-1 value|adoption-api-contract|production-model|X-Request-ID|Observability|Playground" README.md docs/*.md`

Observable success for S05:
- one canonical integrated adoption proof exists without restating the API contract
- public request evidence still starts with `POST /v1/chat/completions`
- `X-Request-ID` remains the binding mechanism from public response to ledger/operator surfaces
- Playground remains corroboration, not the adoption target
- Observability still reads as persisted explanation + dependency-health context
- R003 gains concrete final validation language or at minimum a tighter proof artifact than “mapped”
- if local toolchains are absent, record that as environment gap exactly as S02/S04 did

## Constraints

- S05 must preserve the S02 documentation composition rule: quickstart, production model, and adoption contract stay canonical and separate.
- S05 must preserve runtime truth from S02: tenant/policy/API key/operator are real entities; app/workload remain conceptual only in M001.
- The final proof must stay grounded in the public `POST /v1/chat/completions` path; do not substitute admin Playground as the main path.
- Playground is admin-only and non-streaming by tested contract; any integrated proof must keep that distinction explicit.
- Slice-level executable verification depends on provisioned local Python (`pytest`) and console tooling (`vitest`, `playwright`) in the active worktree; missing tools are environment gaps, not product regressions.

## Common Pitfalls

- **Rewriting the canonicals into a new mega-doc** — avoid duplicating `docs/adoption-api-contract.md`, `docs/quickstart.md`, or `docs/production-model.md`; S05 should compose them.
- **Treating Playground as the migration/adoption target** — keep Playground strictly as operator corroboration, matching S01/S04 boundaries and `tests/test_admin_playground_api.py`.
- **Weakening the proof order** — the stable sequence is public request → `X-Nebula-*`/`X-Request-ID` → usage ledger → Playground/Observability corroboration.
- **Implying app/workload runtime support** — `docs/production-model.md` is explicit that these are guidance only in M001.
- **Mistaking missing local test runners for failed slice behavior** — record absent `pytest`/`vitest`/`playwright` as environment blockers when they occur.

## Open Risks

- R003 is still active because prior slices improved clarity and proof fragments, but S05 may still need an explicit integrated validation artifact/update in `.gsd/REQUIREMENTS.md` to retire it cleanly.
- The existing README already has some duplicated/garbled endpoint lines near the end; any S05 entry-point cleanup should avoid broad README rewrites unless directly needed for integrated-proof discoverability.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js | `react-best-practices` | available |
| Browser / UI verification | `agent-browser` | available |
| FastAPI | `wshobson/agents@fastapi-templates` | none found locally; installable |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | none found locally; installable |
| Playwright | `currents-dev/playwright-best-practices-skill@playwright-best-practices` | none found locally; installable |
