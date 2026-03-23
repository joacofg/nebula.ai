# S02: Happy-path quickstart and production model

**Goal:** Give adopters one concrete self-hosted quickstart and one explicit operating-model reference so a team can stand up Nebula, send a first public chat-completions request, and understand how tenant, API key, app/workload guidance, and operator responsibilities map to production usage without guessing.
**Demo:** Starting from the supported Compose deployment path, a reader can follow the docs to configure real credentials, log into the operator console, issue or reuse the bootstrap client key, send a public `POST /v1/chat/completions` request with `X-Nebula-API-Key`, and verify success through `X-Nebula-*` headers plus the existing Playground / usage-ledger / Observability surfaces while understanding that app/workload are documentation guidance rather than first-class runtime entities.

## Must-Haves

- A canonical quickstart doc exists for the supported self-hosted path and links back to `docs/adoption-api-contract.md` instead of reopening the public contract.
- A canonical production-model doc explains tenant, API key, operator, app, and workload boundaries using the current runtime truth: tenant/policy/API key are real entities, operator uses admin surfaces, and app/workload remain conceptual guidance in M001.
- Entry docs point to the new canonical docs so downstream slices can reuse one happy path and one operating model instead of restating them.
- The slice verification proves both content integrity and that the referenced backend / console evidence surfaces still back the claims.

## Proof Level

- This slice proves: operational
- Real runtime required: no
- Human/UAT required: yes

## Verification

- `test -f docs/quickstart.md && test -f docs/production-model.md && grep -c "^## " docs/quickstart.md | awk '{exit !($1 >= 5)}' && grep -c "^## " docs/production-model.md | awk '{exit !($1 >= 5)}'`
- `rg -n "docs/quickstart.md|docs/production-model.md|adoption-api-contract|self-hosting|Playground|Observability|usage ledger" README.md docs/self-hosting.md docs/architecture.md docs/quickstart.md docs/production-model.md`
- `! rg -n "TODO|TBD" README.md docs/quickstart.md docs/production-model.md docs/self-hosting.md docs/architecture.md`
- `pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_admin_playground_api.py -q`
- `npm --prefix console run test -- --run`

## Observability / Diagnostics

- Runtime signals: existing `X-Nebula-*` response headers on the public path, `X-Request-ID` on Playground, and persisted usage-ledger rows remain the evidence sources the docs must point to.
- Inspection surfaces: `docs/quickstart.md`, `docs/production-model.md`, `README.md`, `docs/self-hosting.md`, `docs/architecture.md`, `GET /v1/admin/usage/ledger`, and the console Playground / Observability pages.
- Failure visibility: doc drift is detected by missing links or placeholder text; product-behavior drift is detected by the referenced pytest suites and console tests failing against the claims these docs make.
- Redaction constraints: docs may name required env var keys and headers, but must not inline secret values or imply copying admin keys into application traffic.

## Integration Closure

- Upstream surfaces consumed: `docs/adoption-api-contract.md`, `docs/self-hosting.md`, `README.md`, `docs/architecture.md`, `src/nebula/services/auth_service.py`, `src/nebula/api/routes/admin.py`, `src/nebula/core/config.py`, `tests/test_chat_completions.py`, `tests/test_governance_api.py`, `tests/test_admin_playground_api.py`, `console/src/components/auth/login-page-client.tsx`, `console/src/components/api-keys/create-api-key-dialog.tsx`.
- New wiring introduced in this slice: documentation composition only — new canonical quickstart and production-model docs linked from entry docs and aligned to existing runtime/operator surfaces.
- What remains before the milestone is truly usable end-to-end: S03 must embody this quickstart and production model in a realistic migrated integration, and S05 must exercise the joined docs-plus-runtime adoption story end to end.

## Tasks

- [ ] **T01: Author the production model and happy-path quickstart docs** `est:1h`
  - Why: S02's main risk is ambiguity, not missing runtime code; the slice needs canonical docs that explain how Nebula should be structured in production and how to reach a working first request on the supported path.
  - Files: `docs/production-model.md`, `docs/quickstart.md`, `docs/adoption-api-contract.md`, `docs/self-hosting.md`, `src/nebula/services/auth_service.py`, `src/nebula/api/routes/admin.py`, `src/nebula/core/config.py`
  - Do: Write `docs/production-model.md` to define tenant, API key, operator, app, and workload boundaries from the current runtime truth; make explicit that `app` and `workload` are guidance only in M001 and that multi-tenant API keys require `X-Nebula-Tenant-ID`. Then write `docs/quickstart.md` as the single supported adoption flow: configure `deploy/selfhosted.env`, start the Compose stack, log into the console with the admin key, explain bootstrap client key usage versus issuing tenant-scoped keys, send one public `POST /v1/chat/completions` request with `X-Nebula-API-Key`, and point to `X-Nebula-*` headers, Playground, usage ledger, and Observability as verification surfaces. Link to `docs/adoption-api-contract.md` for request/response semantics instead of duplicating the contract.
  - Verify: `test -f docs/quickstart.md && test -f docs/production-model.md && rg -n "X-Nebula-API-Key|X-Nebula-Admin-Key|X-Nebula-Tenant-ID|Playground|Observability|usage ledger|startup|platform|enterprise|app|workload" docs/quickstart.md docs/production-model.md`
  - Done when: both canonical docs exist, are non-empty, state the correct client-vs-operator credential split, explain when tenant headers are needed, and keep app/workload framed as conceptual guidance rather than runtime entities.
- [ ] **T02: Wire entry docs to the new canonical adoption story and lock verification to existing evidence** `est:45m`
  - Why: The new docs only reduce ambiguity if the repository entrypoints route readers to them and the slice closes with executable checks tied to live product evidence.
  - Files: `README.md`, `docs/self-hosting.md`, `docs/architecture.md`, `docs/quickstart.md`, `docs/production-model.md`, `tests/test_chat_completions.py`, `tests/test_governance_api.py`, `tests/test_admin_playground_api.py`
  - Do: Update `README.md`, `docs/self-hosting.md`, and `docs/architecture.md` so they point to `docs/quickstart.md` and `docs/production-model.md` wherever they currently leave the happy path or operating model fragmented. Keep `docs/adoption-api-contract.md` as the only public contract doc and ensure entry docs reference, rather than duplicate, that boundary. Add any concise cross-links needed inside the new docs so a reader can move from deployment to public request to operator confirmation without dead ends, then run the planned doc-integrity and test commands.
  - Verify: `rg -n "docs/quickstart.md|docs/production-model.md|adoption-api-contract|self-hosting|Playground|Observability|usage ledger" README.md docs/self-hosting.md docs/architecture.md docs/quickstart.md docs/production-model.md && ! rg -n "TODO|TBD" README.md docs/quickstart.md docs/production-model.md docs/self-hosting.md docs/architecture.md`
  - Done when: repo entry docs clearly route adopters to one quickstart and one production model, there are no placeholder markers in the touched docs, and the slice verification commands are ready to prove the claims still match backend and console evidence.

## Files Likely Touched

- `docs/quickstart.md`
- `docs/production-model.md`
- `README.md`
- `docs/self-hosting.md`
- `docs/architecture.md`
