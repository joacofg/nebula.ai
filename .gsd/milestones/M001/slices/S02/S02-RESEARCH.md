# S02 — Research

**Date:** 2026-03-23

## Summary

S02 should stay mostly documentation-led, grounded in the contract and operator surfaces already proven in S01 rather than adding new runtime behavior. The active requirements this slice owns/supports are `R003` (under-30-minute happy path), `R006` (tenant / app / workload / operator production model), and `R007` (guidance for startup teams, platform teams, and enterprise/self-hosted operators). The repo already contains most of the raw material: a canonical public contract (`docs/adoption-api-contract.md`), a self-hosted deployment runbook (`docs/self-hosting.md`), bootstrap credential/env semantics (`deploy/selfhosted.env.example`, `src/nebula/core/config.py`), admin/governance APIs (`src/nebula/api/routes/admin.py`), tenant resolution rules (`src/nebula/services/auth_service.py`), and operator console proof surfaces for tenants, Playground, and Observability (`console/src/app/(console)/*`).

The main gap is narrative assembly, not missing backend capability. Today the docs explain the public API contract and the deployment topology separately, but they do not yet give one end-to-end “do this first, then this, then verify these visible signals” quickstart, nor a crisp production-model explanation for how teams should map Nebula concepts to real usage. The planner should scope S02 around creating one canonical quickstart / operating-model doc pair and then wiring README/self-hosting/architecture links so downstream slices can point to them instead of re-explaining the model.

## Recommendation

Create two primary docs, then align entry docs around them:

1. a **happy-path quickstart** that starts from the supported self-hosted Compose path, names the exact required env vars, shows how to obtain the bootstrap client key vs admin key, demonstrates one public `POST /v1/chat/completions` request with `X-Nebula-API-Key`, and tells the adopter exactly where to confirm success (`X-Nebula-*` headers, console Playground, usage ledger, dependency health).
2. a **production model / operating model** doc that explains the current lightweight boundaries: tenant = policy and usage isolation unit, API key = client credential bound to one or more tenants, operator = admin-key holder using `/v1/admin/*` and the console, app/workload = conceptual traffic-shaping guidance rather than first-class runtime entities in M001.

Use the S01 rule explicitly: do not restate contract details broadly. The quickstart should link back to `docs/adoption-api-contract.md` for the stable public request/response boundary and keep its own claims limited to the adoption flow. This follows the established S01 documentation pattern (“single canonical contract doc; link from entry docs instead of duplicating”). For Next.js/React console references, the already-installed `react-best-practices` skill is relevant only insofar as S02 should rely on existing console surfaces rather than inventing new UI for explanation.

## Implementation Landscape

### Key Files

- `docs/adoption-api-contract.md` — canonical S01 public compatibility boundary. S02 must consume this, not reopen it. Quickstart should link here for auth, streaming, supported/unsupported fields, and response semantics.
- `docs/self-hosting.md` — canonical deployment runbook for the supported self-hosted path. Already names required env vars, supported topology, and verification endpoints; best base for quickstart sequencing.
- `deploy/selfhosted.env.example` — production-ish env template. Shows the exact self-hosted profile S02 should teach: `NEBULA_ENV=production`, `NEBULA_RUNTIME_PROFILE=premium_first`, `NEBULA_DEFAULT_MODEL=nebula-auto`, premium provider config, admin/bootstrap credentials.
- `README.md` — current entry doc. Already links to self-hosting, architecture, evaluation, and adoption contract, but quickstart remains split between deployment and API. Likely needs a new doc-map/link update after S02 docs exist.
- `docs/architecture.md` — current product/runtime framing. Good home for a short pointer to the production model doc instead of embedding more concept prose here.
- `src/nebula/core/config.py` — source of truth for required env behavior. Critical constraints: non-local env requires `premium_first`, non-default admin/bootstrap keys, non-mock premium provider, and a database URL.
- `src/nebula/services/auth_service.py` — source of truth for tenant resolution. Important for production model wording: API keys can be tenant-scoped, can authorize multiple tenants, and require explicit `X-Nebula-Tenant-ID` only when the key spans multiple tenants.
- `src/nebula/models/governance.py` — current runtime entities. There is no first-class `app` or `workload` model; those concepts must remain documentation guidance in S02, which also aligns with deferred `R012`.
- `src/nebula/services/governance_store.py` — proves bootstrap behavior and default policy creation. Useful for documenting day-1 bootstrap assumptions: default tenant is created, default policy allows the configured premium model, bootstrap API key is ensured.
- `src/nebula/api/routes/admin.py` — enumerates current operator actions: tenants, tenant policy, API keys, usage ledger, Playground. This is the concrete basis for the operator role in the production model.
- `tests/test_governance_api.py` — executable evidence for tenant creation, policy updates, API key issuance, tenant authorization failures, and usage ledger filters. Best backend verification source for S02’s production-model claims.
- `tests/test_admin_playground_api.py` — proves Playground is admin-only, non-streaming, request-id correlated, and writes ledger-visible outcomes.
- `tests/test_chat_completions.py` — proves the public client happy path with `X-Nebula-API-Key`, bootstrap tenant inference, SSE, and 422 validation behavior.
- `console/src/app/(console)/tenants/page.tsx` — existing operator surface for tenant operations; good visual proof for “tenant = governance unit”.
- `console/src/app/(console)/playground/page.tsx` — existing operator proof for immediate route metadata and recorded outcome correlation.
- `console/src/app/(console)/observability/page.tsx` — existing operator proof for usage-ledger filtering and dependency health.
- `console/src/components/auth/login-page-client.tsx` — concise current language for admin-key session semantics: memory-only access, direct-to-tenants landing, same-origin proxy boundary. Useful wording source for operator model.
- `console/src/components/api-keys/create-api-key-dialog.tsx` — shows the current API-key conceptual model in UI terms: explicit `tenant_id` and `allowed_tenant_ids`.
- `console/e2e/auth.spec.ts` — validates console login lands on Tenants and refresh clears in-memory admin session.
- `console/e2e/playground.spec.ts` — validates Playground’s immediate evidence and recorded-outcome story.
- `console/e2e/observability.spec.ts` — validates ledger filtering and dependency health framing.

### Build Order

1. **Define the production model in docs first.** This is the conceptual risk for S02 and unblocks everything else. The planner should pin exact wording for tenant, API key, operator, app, and workload based on the actual runtime models and S01 constraints.
2. **Assemble the quickstart second.** Once the conceptual model is stable, create the single happy-path flow: configure env, start Compose, sign into console with admin key, identify/bootstrap tenant and client key, send one public request, inspect headers, confirm in Playground / ledger / Observability.
3. **Wire entry docs to the new canonical docs.** Update `README.md`, `docs/self-hosting.md`, and possibly `docs/architecture.md` to point at the quickstart and operating-model docs instead of carrying parallel explanations.
4. **Only then consider tests/docs assertions.** If S02 adds doc-quality guardrails, they should verify references and absence of placeholder language rather than inventing new runtime tests.

### Verification Approach

- Doc integrity / linkage:
  - `rg -n "quickstart|operating model|production model|tenant|workload|operator" README.md docs`
  - `rg -n "adoption-api-contract|self-hosting|usage ledger|Playground|Observability" README.md docs`
  - `rg -n "TODO|TBD" README.md docs/<new-doc>.md docs/<new-doc>.md`
- Backend evidence re-use (no new behavior expected):
  - `pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_admin_playground_api.py -q`
- Console evidence re-use for the operator story:
  - `npm --prefix console run test -- --run`
  - `npm --prefix console run test:e2e` or the repo’s `make console-e2e` if the environment exists
- Human acceptance signals for S02 content:
  - A reader can answer: “Which key does the app use?”, “Which key does the operator use?”, “When do I need `X-Nebula-Tenant-ID`?”, “What is a tenant?”, “Where do I confirm routing happened?”, and “Are app/workload runtime objects yet?” without reading code.

## Constraints

- `docs/adoption-api-contract.md` is the only canonical public compatibility boundary; S02 must link to it rather than re-documenting the request/response contract.
- `app` and `workload` are not first-class runtime/admin entities today; `src/nebula/models/governance.py` only models tenant, policy, API key, and usage ledger. Keep app/workload guidance conceptual to avoid accidentally promising R012 early.
- Outside local env, `src/nebula/core/config.py` requires `NEBULA_RUNTIME_PROFILE=premium_first`, non-default admin/bootstrap keys, non-mock premium provider, and `NEBULA_DATABASE_URL`.
- The public path uses `X-Nebula-API-Key`, not bearer auth; operator/admin flows use `X-Nebula-Admin-Key` via console proxying.
- Playground is admin-only and non-streaming; do not use it as evidence of public-client compatibility.

## Common Pitfalls

- **Reopening the API contract in quickstart docs** — avoid by linking back to `docs/adoption-api-contract.md` for request semantics and unsupported features.
- **Overstating app/workload support** — document them as structuring guidance only; the runtime does not currently persist or enforce them as entities.
- **Blurring client and operator credentials** — keep `X-Nebula-API-Key` and `X-Nebula-Admin-Key` visually and narratively separate.
- **Using local-dev setup as the production story** — S02 should prefer the supported Compose self-hosted path, with local dev clearly secondary.

## Open Risks

- The current repo may not yet expose a user-facing doc that tells adopters how to obtain or mint additional tenant-scoped client keys beyond the bootstrap key in a quickstart-friendly way; the planner should check whether S02 can rely on existing admin API/console docs alone or needs a short guided example.
- If the slice tries to tailor guidance deeply per ICP (startup/platform/enterprise) inside many docs, it could create another drift surface. Prefer a single production-model doc with short persona subsections.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Next.js | `react-best-practices` | installed / available |
| React | `react-best-practices` | installed / available |
| Next.js | `wshobson/agents@nextjs-app-router-patterns` | available |
| React | `vercel-labs/agent-skills@vercel-react-best-practices` | available |
| FastAPI | `wshobson/agents@fastapi-templates` | available |

