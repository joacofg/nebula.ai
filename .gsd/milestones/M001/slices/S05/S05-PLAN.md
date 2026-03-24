# S05: Final integrated adoption proof

**Goal:** Assemble Nebula's existing adoption canonicals, migration proof, and operator-visible evidence into one final integrated proof that preserves the public contract boundary and shows the documented happy path is actually completable as a joined system.
**Demo:** A developer can start from the documented quickstart, follow the canonical migration/value proof sequence, and verify one real public `POST /v1/chat/completions` request through `X-Nebula-*` headers, `X-Request-ID`, usage-ledger correlation, and operator corroboration without treating Playground as the adoption target.

## Must-Haves

- One canonical integrated adoption proof exists and composes `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, `docs/production-model.md`, and `docs/adoption-api-contract.md` without duplicating their contract/setup content.
- Executable verification proves the public request → headers / `X-Request-ID` → usage ledger correlation pattern still holds as the backbone of the integrated adoption story.
- Console-facing proof surfaces remain aligned with the integrated story: Playground is corroboration only, Observability remains the persisted explanation plus dependency-health surface, and the joined story is asserted in automated UI coverage.
- `R003` gains concrete validation rooted in the integrated proof artifact and executable verification, with any missing local runners recorded as environment gaps rather than product regressions.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `python3 -m pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_chat_completions.py tests/test_response_headers.py -q`
- `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome && npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability`
- `npm --prefix console run e2e -- --grep "playground|observability"`
- `rg -n "integrated adoption|quickstart|reference migration|day-1 value|adoption-api-contract|production-model|X-Request-ID|Playground|Observability" README.md docs/*.md .gsd/REQUIREMENTS.md .gsd/KNOWLEDGE.md`

## Observability / Diagnostics

- Runtime signals: public `X-Nebula-*` response headers, `X-Request-ID`, usage-ledger fields (`final_route_target`, `final_provider`, `route_reason`, `policy_outcome`, `terminal_status`), Playground immediate metadata, Observability dependency-health state
- Inspection surfaces: `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, `console/e2e/playground.spec.ts`, `console/e2e/observability.spec.ts`, `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, `GET /v1/admin/usage/ledger`, console Playground, console Observability
- Failure visibility: missing response headers, broken ledger correlation, UI copy drift that weakens boundary clarity, or absent local `pytest` / `vitest` / `playwright` runners recorded as environment blockers
- Redaction constraints: keep proofs metadata-only; do not introduce raw prompt/response, credential, or secret disclosure beyond existing operator/admin surfaces

## Integration Closure

- Upstream surfaces consumed: `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, `docs/production-model.md`, `docs/adoption-api-contract.md`, `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, `console/src/app/(console)/playground/page.tsx`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/playground/playground-metadata.tsx`, `console/src/components/playground/playground-recorded-outcome.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/e2e/playground.spec.ts`, `console/e2e/observability.spec.ts`
- New wiring introduced in this slice: one canonical integrated-proof doc/entry path, one explicit integrated backend proof seam, and one final requirement/knowledge closure update tying docs, tests, and operator surfaces together
- What remains before the milestone is truly usable end-to-end: nothing beyond rerunning the listed verification in a provisioned environment if local test runners are absent in the active worktree

## Tasks

- [x] **T01: Compose the canonical integrated adoption walkthrough** `est:45m`
  - Why: S05 needs one discoverable final proof path that assembles the existing canonicals into a single adoption story without reopening the public contract or rewriting the setup docs.
  - Files: `docs/integrated-adoption-proof.md`, `README.md`, `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`
  - Do: Add a final integrated adoption proof document that explicitly preserves the stable order public request → `X-Nebula-*` / `X-Request-ID` → usage ledger → Playground / Observability corroboration; link back to `docs/adoption-api-contract.md` and `docs/production-model.md` instead of restating them; add only the minimal README and doc cross-links needed to make this integrated path discoverable from the existing documentation map.
  - Verify: `test -f docs/integrated-adoption-proof.md && rg -n "integrated adoption|X-Request-ID|Playground|Observability|adoption-api-contract|production-model" README.md docs/integrated-adoption-proof.md docs/quickstart.md docs/reference-migration.md docs/day-1-value.md`
  - Done when: The repo has one canonical integrated-proof entry point, the adoption sequence is explicit and runtime-truthful, and the existing canonicals remain separate rather than duplicated.
- [x] **T02: Extend executable public-to-operator integration proof** `est:1h`
  - Why: The final slice must prove in code that the assembled adoption story still holds end to end from the public request path through ledger/operator evidence, not just in prose.
  - Files: `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, `tests/test_chat_completions.py`, `tests/test_response_headers.py`
  - Do: Add or refine focused integration assertions that preserve the S03/S04 proof order, keep Playground clearly admin-only corroboration, and prove the response-header plus `X-Request-ID` correlation pattern remains the backbone of the integrated story; reuse existing fixtures/runtime harnesses instead of introducing parallel test infrastructure.
  - Verify: `python3 -m pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_chat_completions.py tests/test_response_headers.py -q`
  - Done when: The integrated backend proof is executable from the real public route boundary through ledger correlation, and any verification failure points clearly to contract drift rather than missing assembly.
- [x] **T03: Align console proof surfaces and close requirement evidence** `est:1h`
  - Why: Final milestone closure requires the operator-facing UI proof and milestone bookkeeping to tell the same joined story as the docs and backend verification, and R003 needs explicit validation language.
  - Files: `console/e2e/playground.spec.ts`, `console/e2e/observability.spec.ts`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `.gsd/REQUIREMENTS.md`, `.gsd/KNOWLEDGE.md`
  - Do: Tighten console e2e and any minimal supporting UI copy/assertion seams so Playground reads as immediate corroboration and Observability as persisted explanation plus dependency health inside the integrated proof; then update requirement and knowledge records with the final integrated validation pattern and explicit environment-gap handling if local runners are unavailable.
  - Verify: `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome && npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability && npm --prefix console run e2e -- --grep "playground|observability" && rg -n "R003|integrated adoption|environment gap|X-Request-ID|Playground|Observability" .gsd/REQUIREMENTS.md .gsd/KNOWLEDGE.md console/e2e/playground.spec.ts console/e2e/observability.spec.ts`
  - Done when: The UI proof matches the integrated adoption sequence, milestone knowledge/validation records document the final proof pattern, and R003 has concrete closure evidence.

## Files Likely Touched

- `docs/integrated-adoption-proof.md`
- `README.md`
- `docs/quickstart.md`
- `docs/reference-migration.md`
- `docs/day-1-value.md`
- `tests/test_reference_migration.py`
- `tests/test_admin_playground_api.py`
- `tests/test_governance_api.py`
- `console/e2e/playground.spec.ts`
- `console/e2e/observability.spec.ts`
- `.gsd/REQUIREMENTS.md`
- `.gsd/KNOWLEDGE.md`
