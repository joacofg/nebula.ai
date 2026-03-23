# Slice Summary — S02: Happy-path quickstart and production model

## Status
Complete with documented environment gaps in executable verification.

## Slice Goal
Give adopters one concrete self-hosted quickstart and one explicit operating-model reference so a team can stand up Nebula, send a first public chat-completions request, and understand how tenant, API key, app/workload guidance, and operator responsibilities map to production usage without guessing.

## What This Slice Delivered
S02 turned the adoption story from scattered repo knowledge into a canonical documentation flow.

It added:
- `docs/quickstart.md` as the single supported self-hosted happy-path walkthrough from env setup to first public `POST /v1/chat/completions` request.
- `docs/production-model.md` as the single operating-model reference for tenant, policy, API key, operator, and app/workload framing.
- Cross-links from `README.md`, `docs/self-hosting.md`, and `docs/architecture.md` so adopters are routed into one quickstart, one production-model doc, and one public API contract instead of piecing together overlapping guidance.

It also preserved the S01 boundary by keeping:
- `docs/adoption-api-contract.md` as the only canonical public compatibility contract.
- Playground explicitly positioned as an admin/operator inspection surface, not the public adoption boundary.

## Runtime Truth This Slice Locked In
S02 established the language downstream slices should treat as authoritative for M001:
- **Tenant** is the real governance boundary.
- **Tenant policy** is the enforced runtime policy surface.
- **API key** is the public client credential for `POST /v1/chat/completions`.
- **Admin key / operator session** is for `/v1/admin/*` and console access only.
- **`X-Nebula-Tenant-ID`** is required only when a public API key is intentionally authorized for multiple tenants and the tenant cannot be inferred.
- **App** and **workload** are still documentation guidance only in M001, not first-class runtime entities.

That framing matters because S03 can now build a realistic migration example without inventing product structures that do not yet exist.

## Patterns Established
- Keep adoption guidance decomposed into three canonicals:
  1. `docs/self-hosting.md` for deployment
  2. `docs/quickstart.md` for first-request execution
  3. `docs/production-model.md` for production structuring
- Keep `docs/adoption-api-contract.md` as the sole public API contract instead of re-describing request/response behavior elsewhere.
- Separate public client evidence from operator evidence:
  - public path: `X-Nebula-*` headers
  - operator path: Playground, `X-Request-ID`, usage ledger, Observability
- Treat bootstrap access as a first-request convenience, not the long-term production key-management model.

## Verification Performed
### Passed
- File existence and section-structure checks for `docs/quickstart.md` and `docs/production-model.md`
- Link/reference integrity checks across:
  - `README.md`
  - `docs/self-hosting.md`
  - `docs/architecture.md`
  - `docs/quickstart.md`
  - `docs/production-model.md`
- Placeholder scan confirming no `TODO` / `TBD` markers remained in touched docs
- Manual content verification against the docs confirmed the expected claims are present:
  - admin vs client credential split
  - tenant-header requirement rules
  - Playground/Observability/usage-ledger evidence surfaces
  - startup/platform/enterprise framing

### Blocked by environment, not by slice content
- `pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_admin_playground_api.py -q`
- `npm --prefix console run test -- --run`

In this worktree, both failed because the required local tools were absent:
- `pytest: command not found`
- `console/node_modules/.bin/vitest` missing

This means the slice achieved documentation closure, but executable regression confirmation still needs rerun in a provisioned environment.

## Observability / Diagnostic Surfaces Confirmed
The docs consistently point adopters to the existing evidence surfaces that back the slice claims:
- public `X-Nebula-*` response headers
- Playground `X-Request-ID`
- `GET /v1/admin/usage/ledger`
- console Playground
- console Observability

No new runtime observability was introduced; S02’s job was to make those existing surfaces part of the adoption path and production model.

## Requirement Impact
Validated based on slice evidence:
- `R006` — production boundary explanation is now explicit and canonical.
- `R007` — adoption guidance is now intentionally framed for startup teams, platform-minded adopters, and enterprise/self-hosted operators.

Still not fully retired by S02 alone:
- `R003` remains active because the under-30-minute claim still needs stronger live walkthrough proof, not just documentation quality.

## Decisions / Knowledge Captured
Added decision:
- `D008` — adoption guidance should live in one canonical quickstart, one canonical production-model doc, and one canonical public API contract.

Added useful knowledge:
- the S02 documentation composition rule
- the M001 runtime-truth rule for tenant/policy/API key/operator vs conceptual app/workload
- the fact that slice-level executable verification depends on local Python and console test tooling being provisioned in the active worktree

## What Downstream Slices Should Know
### For S03
Use this slice’s docs as the scenario baseline. The migration example should:
- follow `docs/quickstart.md` rather than inventing a second onboarding path
- respect the tenant/operator/app/workload framing from `docs/production-model.md`
- use the public API contract from `docs/adoption-api-contract.md`
- show either bootstrap-first or tenant-key-first behavior explicitly, not ambiguously

### For S04
Day-1 value proof should reuse the evidence surfaces already named here:
- `X-Nebula-*` public headers
- Playground
- usage ledger
- Observability

### For S05
Final integrated acceptance should rerun this slice’s blocked executable checks in a fully provisioned environment so the docs-to-runtime alignment is proven, not only described.

## Residual Risks
- The documentation is now coherent, but this worktree did not have the toolchain needed to rerun backend and console suites.
- The happy path is credible on paper and linked to real surfaces, but S03/S05 still need to embody and exercise it end to end.
- App/workload remain conceptual only; downstream work should avoid accidentally implying stronger runtime support than exists.

## Files Material to This Slice
- `docs/quickstart.md`
- `docs/production-model.md`
- `README.md`
- `docs/self-hosting.md`
- `docs/architecture.md`
- `.gsd/REQUIREMENTS.md`
- `.gsd/KNOWLEDGE.md`
- `.gsd/DECISIONS.md`

## Bottom Line
S02 closed the production-model ambiguity risk at the documentation layer. Nebula now has one supported quickstart, one explicit operating model, and one bounded public contract that downstream slices can build on. The main remaining gap is executable re-verification in a prepared environment, not ambiguity in the adoption story.