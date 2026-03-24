# S03: Integrated production-structuring walkthrough — Research

**Date:** 2026-03-23

## Summary

This slice primarily supports `R006` and closes the final milestone proof gap described in the roadmap: assemble one coherent production-structuring walkthrough across the existing canonicals and the already-aligned console truth surfaces from S01 and S02. The codebase already has the right underlying assets. `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`, and `docs/integrated-adoption-proof.md` together cover runtime truth, first request, migration proof, and integrated operator proof. The console surfaces already reinforce the same boundaries: Tenants = enforced boundary, API keys = caller scope, Playground = admin-only corroboration, Observability = persisted evidence plus dependency-health context.

Recommendation: keep S03 composition-first. Do not introduce new runtime concepts, routes, or console objects. The strongest implementation is to tighten the end-to-end walkthrough at the documentation layer and add/align focused verification around the exact story order: tenant/API-key structuring decision -> public request/header rule -> usage-ledger correlation -> Playground corroboration -> Observability persisted explanation. This matches the loaded `react-best-practices` skill guidance to avoid unnecessary churn and preserve narrow, explicit verification for copy-heavy React surfaces.

## Recommendation

Use the existing canonicals and focused Vitest pattern rather than building a new product flow. Start from `docs/integrated-adoption-proof.md` and `docs/production-model.md`, verify they explicitly compose the S01/S02 console truths, then add or tighten doc/tests only where the assembled operator story is still implicit. If any product-layer work is needed, keep it limited to copy/assertions in already-touched console surfaces rather than new UI mechanics.

Why:
- S01 already locked API-key scope semantics, Playground framing, and Observability framing.
- S02 already locked tenant/app/workload guidance and negative drift checks.
- The remaining risk is coherence of the assembled walkthrough, not missing runtime capability.
- The established test pattern in this repo is narrow text assertions plus absence checks, not broad snapshots or speculative E2E expansion.

## Implementation Landscape

### Key Files

- `docs/production-model.md` — canonical runtime truth for tenant, API key, admin session, `X-Nebula-Tenant-ID`, and app/workload-as-guidance-only. This is the source for the production-structuring rules S03 must not contradict.
- `docs/quickstart.md` — canonical self-hosted first-request walkthrough. Already includes operator login, bootstrap vs tenant-scoped key choice, tenant-header rules, and post-request evidence surfaces.
- `docs/reference-migration.md` — canonical public request + `X-Request-ID` + usage-ledger correlation proof. Important because S03 should preserve the rule that `X-Nebula-Tenant-ID` is conditional, not default.
- `docs/integrated-adoption-proof.md` — already exists as the canonical assembled walkthrough. Most likely primary S03 doc surface to inspect/update because it explicitly defines proof order and ties canonicals together.
- `console/src/app/(console)/tenants/page.tsx` — top-level tenant/app/workload runtime-truth copy from S02. Use as the console source for “tenants are the enforced boundary; apps/workloads are conventions.”
- `console/src/components/tenants/tenant-editor-drawer.tsx` — tenant metadata framing as optional notes/runbook context only. Useful if the walkthrough needs an explicit operator example of where app/workload intent lives today.
- `console/src/app/(console)/playground/page.tsx` — S01 page-level Playground framing: admin-session, non-streaming, corroboration only, not the public boundary.
- `console/src/components/playground/playground-form.tsx` — adds the immediate-vs-recorded evidence split in plain UI copy: immediate completion/request id first, ledger evidence after persistence.
- `console/src/components/playground/playground-recorded-outcome.tsx` — explicit wording for persisted ledger outcome of the same request.
- `console/src/app/(console)/observability/page.tsx` — page-level persisted request evidence plus dependency-health context framing.
- `console/src/app/(console)/tenants/page.test.tsx` — focused assertion for tenant/API-key/app-workload runtime truth.
- `console/src/components/tenants/tenant-table.test.tsx` — negative checks that app/workload pseudo-entity columns are absent.
- `console/src/components/playground/playground-page.test.tsx` — focused assertion that Playground is corroboration, not the public integration boundary.
- `console/src/components/playground/playground-form.test.tsx` — focused assertion that Playground is tenant-selected, admin-session, and non-streaming, with immediate vs later recorded evidence.
- `console/src/app/(console)/observability/page.test.tsx` — focused assertion that Observability is persisted request evidence plus dependency-health context.
- `.gsd/milestones/M002/slices/S02/S02-UAT.md` — already contains a concrete tenant-surface UAT script. Its structure is a good model if S03 needs a final integrated UAT/read-through artifact instead of more product code.

### Build Order

1. **Prove the assembled doc story first** in `docs/integrated-adoption-proof.md` against `docs/production-model.md`, `docs/quickstart.md`, and `docs/reference-migration.md`.
   - This is the highest-value/risk seam because S03 is about coherence, not new mechanics.
   - Confirm the walkthrough explicitly answers: how to structure real teams around tenants and keys, when the tenant header is required, and where apps/workloads belong today.
2. **Cross-check the console surfaces already match the walkthrough order** using the existing Tenants, Playground, and Observability pages/tests.
   - If the docs rely on a console claim that is not literally present, add/tighten focused copy or tests in the smallest touched surface.
3. **Only then add verification artifacts**.
   - Prefer focused Vitest assertions or a compact integrated UAT/checklist doc over broad new end-to-end automation.
   - The natural split is docs composition first, verification second.

### Verification Approach

Primary verification should be contract/integration-level, not feature-expansion:

- Docs/manual coherence review:
  - confirm `docs/integrated-adoption-proof.md` preserves the canonical proof order
  - confirm `docs/production-model.md` still anchors tenant/API-key/app/workload runtime truth
  - confirm `docs/quickstart.md` and `docs/reference-migration.md` still agree on conditional `X-Nebula-Tenant-ID`
- Focused console tests:
  - `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx`
  - `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'`
- If docs change materially, add a manual read-through/UAT artifact for the exact operator flow the roadmap calls for:
  - tenant boundary decision
  - API-key scope decision
  - public request
  - header/request-id capture
  - usage-ledger correlation
  - Playground corroboration
  - Observability corroboration

## Constraints

- Do not introduce `app` or `workload` as runtime/admin entities; loaded milestone context and S02 both treat them as conventions only.
- Do not widen scope into backend/admin API changes; current milestone context explicitly says no new backend fields, entities, or admin APIs were introduced.
- Preserve canonical doc roles: `docs/quickstart.md` = happy path, `docs/production-model.md` = runtime truth, `docs/adoption-api-contract.md` = public contract, `docs/reference-migration.md` = migration proof, `docs/integrated-adoption-proof.md` = assembled walkthrough.
- Preserve proof ordering from project knowledge: public `POST /v1/chat/completions` first, then `X-Nebula-*` + `X-Request-ID`, then usage-ledger correlation, then Playground corroboration, then Observability.

## Common Pitfalls

- **Turning the integrated walkthrough into a second contract doc** — keep detailed API semantics in `docs/adoption-api-contract.md` and runtime entity semantics in `docs/production-model.md`; link instead of duplicating.
- **Accidentally making `X-Nebula-Tenant-ID` sound mandatory** — keep the S03/M001 rule explicit: it is required only for intentionally multi-tenant keys.
- **Collapsing Playground and Observability into one generic admin proof surface** — S01 established a strict split: Playground is immediate/admin-side corroboration; Observability is persisted explanation plus dependency-health context.
- **Reintroducing pseudo-entity language in console or docs** — continue S02’s positive-plus-negative test pattern (`workspace`, `app`, `workload` drift checks) instead of relying on snapshots.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js console | `react-best-practices` | available |
| React | `vercel-labs/agent-skills@vercel-react-best-practices` | discoverable |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | discoverable |
| Vitest | `onmax/nuxt-skills@vitest` | discoverable |
