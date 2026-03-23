---
estimated_steps: 3
estimated_files: 7
skills_used:
  - react-best-practices
---

# T01: Author the production model and happy-path quickstart docs

**Slice:** S02 — Happy-path quickstart and production model
**Milestone:** M001

## Description

Create the two canonical docs this slice needs: a production-model reference that defines Nebula's current operating boundaries truthfully, and a quickstart that walks a new adopter through the supported self-hosted path to a first successful public request plus operator-visible confirmation. Keep the public API contract anchored in `docs/adoption-api-contract.md` rather than re-documenting it.

## Steps

1. Read the existing runtime truth in `src/nebula/services/auth_service.py`, `src/nebula/api/routes/admin.py`, `src/nebula/core/config.py`, `console/src/components/auth/login-page-client.tsx`, and `console/src/components/api-keys/create-api-key-dialog.tsx`, then write `docs/production-model.md` to define tenant, API key, operator, app, and workload boundaries without promising product surfaces that do not exist.
2. Write `docs/quickstart.md` as the canonical supported adoption flow: configure `deploy/selfhosted.env.example`, start `docker-compose.selfhosted.yml`, sign into the console with the admin key, explain bootstrap client key use versus tenant-scoped key creation, send one public `POST /v1/chat/completions` request with `X-Nebula-API-Key`, and show where to confirm success through headers, Playground, the usage ledger, and Observability.
3. Add cross-links between the two new docs and `docs/adoption-api-contract.md` / `docs/self-hosting.md` so executors and downstream slices can treat them as the single canonical operating-model and quickstart references.

## Must-Haves

- [ ] `docs/production-model.md` makes clear that tenant, policy, and API key are real runtime/admin entities, operator uses admin-key-backed console and `/v1/admin/*`, and app/workload remain conceptual guidance in M001.
- [ ] `docs/quickstart.md` shows the credential split between `X-Nebula-API-Key` and `X-Nebula-Admin-Key`, explains when `X-Nebula-Tenant-ID` is required, and points back to `docs/adoption-api-contract.md` for the supported request/response boundary.

## Verification

- `test -f docs/quickstart.md && test -f docs/production-model.md && grep -c "^## " docs/quickstart.md | awk '{exit !($1 >= 5)}' && grep -c "^## " docs/production-model.md | awk '{exit !($1 >= 5)}'`
- `rg -n "X-Nebula-API-Key|X-Nebula-Admin-Key|X-Nebula-Tenant-ID|Playground|Observability|usage ledger|startup|platform|enterprise|app|workload" docs/quickstart.md docs/production-model.md`

## Inputs

- `src/nebula/services/auth_service.py` — tenant resolution rules and when explicit `X-Nebula-Tenant-ID` is required
- `src/nebula/api/routes/admin.py` — current operator surfaces for tenants, API keys, usage ledger, and Playground
- `src/nebula/core/config.py` — required production env semantics and bootstrap/admin key constraints
- `docs/adoption-api-contract.md` — canonical public contract that the quickstart must link to instead of duplicating
- `docs/self-hosting.md` — supported deployment runbook that the quickstart must build on
- `console/src/components/auth/login-page-client.tsx` — current operator-session semantics wording
- `console/src/components/api-keys/create-api-key-dialog.tsx` — current API-key conceptual model in the console

## Expected Output

- `docs/production-model.md` — canonical operating-model reference for tenant, API key, operator, app, and workload boundaries
- `docs/quickstart.md` — canonical self-hosted happy-path adoption flow from env setup to first public request and operator-visible confirmation
