---
estimated_steps: 3
estimated_files: 4
skills_used:
  - react-best-practices
---

# T01: Tighten the canonical integrated walkthrough

**Slice:** S03 — Integrated production-structuring walkthrough
**Milestone:** M002

## Description

Make the final canonical walkthrough explicitly production-structuring-first. This task should strengthen `docs/integrated-adoption-proof.md` so an operator can start from tenant/API-key structure, keep the real public route as the first runtime proof, preserve the conditional `X-Nebula-Tenant-ID` rule, and then move through usage-ledger, Playground, and Observability corroboration in the exact order established by prior slices.

## Steps

1. Read `docs/integrated-adoption-proof.md` against `docs/production-model.md`, `docs/quickstart.md`, and `docs/reference-migration.md` and identify where the production-structuring setup or tenant-header rule is still implicit rather than explicit.
2. Update `docs/integrated-adoption-proof.md` to add the missing operator framing: tenants are the enforced boundary, API keys carry caller scope, app/workload stay guidance-only, and `X-Nebula-Tenant-ID` is required only for intentionally multi-tenant keys.
3. Keep the document composition-first by linking back to the canonicals instead of duplicating setup or API-contract detail, and preserve the proof order of public request → public headers/request id → usage ledger → Playground corroboration → Observability corroboration.

## Must-Haves

- [ ] `docs/integrated-adoption-proof.md` explicitly starts from production-structuring choices grounded in `docs/production-model.md` before the public proof sequence continues.
- [ ] The walkthrough keeps Playground and Observability in corroboration roles only and does not imply `app` or `workload` are first-class runtime/admin objects.

## Verification

- `test -s docs/integrated-adoption-proof.md`
- `rg -n "production-model|X-Nebula-Tenant-ID|usage ledger|Playground|Observability|tenant" docs/integrated-adoption-proof.md`

## Inputs

- `docs/integrated-adoption-proof.md` — current assembled walkthrough that needs the production-structuring framing tightened.
- `docs/production-model.md` — canonical runtime-truth source for tenant, API-key, operator, and app/workload boundaries.
- `docs/quickstart.md` — canonical first-request and operator-console entry flow.
- `docs/reference-migration.md` — canonical conditional-tenant-header and public-to-ledger proof source.

## Expected Output

- `docs/integrated-adoption-proof.md` — updated final walkthrough that explicitly composes production structuring, public proof, and operator corroboration in one ordered story.
