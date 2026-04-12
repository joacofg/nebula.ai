# M008: Evidence Governance and Privacy Controls — Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

## Project Description

M008 is a trust-boundary milestone for Nebula’s evidence layer. Nebula’s adoption, routing, simulation, calibration, and operator evidence story is already credible and request-led, but operators still do not have deliberate control over what evidence metadata is persisted, how long that evidence survives, how much of that metadata is retained, or how to inspect the effective evidence boundary from the same policy and request-detail seams where Nebula already explains behavior.

The milestone is not about adding more evidence. It is about making Nebula’s evidence boundary governable without weakening its debugging and operator-trust value. Tenant policy should become the explicit place where operators govern evidence retention and metadata minimization. Those controls should be real backend behavior, not advisory copy. Retention should mean actual deletion. Historical request proof should remain trustworthy even when policy changes later, which means per-request governance markers must be persisted on the ledger row itself rather than inferred from current tenant policy after the fact.

## Why This Milestone

Nebula already gives operators useful request evidence, but the product still needs a stronger answer to a basic pilot question: what evidence is persisted, how long is it retained, how much metadata is captured, and where can an operator prove those boundaries? Right now the hosted plane already has a strong metadata-only allowlist contract, the usage ledger already persists request evidence, and tenant policy already carries advisory capture flags, but the full governance chain is not yet coherent or operator-governed.

This milestone matters now because M007 already clarified page identity and evidence hierarchy. The next highest-leverage move is not another UI role pass or a broader analytics surface. It is to strengthen Nebula’s trust story: useful request evidence remains available, but the evidence boundary is intentionally bounded, tenant-governed, retention-aware, and still subordinate to local operator control.

## User-Visible Outcome

### When this milestone is complete, the user can:

- configure explicit tenant evidence-retention and metadata-minimization policy and know those controls change real persistence behavior rather than just labels on the policy page
- inspect a request in request detail and see the historical governance markers that explain what evidence policy applied when that row was written, including whether data was suppressed or later removed by retention

### Entry point / environment

- Entry point: operator console policy page, request-detail surface in Observability, admin policy and usage-ledger APIs, hosted metadata contract docs
- Environment: browser / local dev / production-like self-hosted runtime
- Live dependencies involved: gateway admin APIs, PostgreSQL governance store, hosted metadata export contract, existing request-led operator surfaces

## Completion Class

- Contract complete means: tenant policy, admin APIs, ledger row shape, and hosted-boundary documentation expose a stable, typed governance model for retention and metadata minimization without widening into payload capture
- Integration complete means: tenant policy drives persistence/export behavior, request detail can explain historical governance truthfully, retention execution deletes expired evidence, and hosted metadata-only boundaries remain aligned
- Operational complete means: there is a real retention execution path that can be exercised and verified as actual deletion behavior rather than inferred or manually assumed

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- an operator can set tenant evidence governance policy, issue a real request, and then inspect request detail to see what evidence boundary applied when that row was persisted
- a retention window can expire and the corresponding evidence is actually deleted according to policy rather than merely hidden from the UI
- Nebula’s hosted metadata-only contract remains intact and visibly consistent with the new tenant-governed evidence boundary, without payload-capture creep or hosted-authority drift

## Architectural Decisions

### Tenant policy owns the evidence boundary

**Decision:** Express evidence governance as typed tenant-policy controls rather than implicit implementation behavior or deployment-wide defaults.

**Rationale:** Nebula’s existing governance model is already tenant-centric. Using typed tenant policy keeps the control surface bounded, visible, and consistent with how routing, cache, and budget controls already work.

**Alternatives Considered:**
- Deployment-wide governance only — rejected because it would weaken tenant-scoped operator control and fit the codebase less well.
- Implicit implementation behavior — rejected because operators need inspectable, explicit policy to trust the boundary.

### Historical request proof uses persisted governance markers

**Decision:** Persist per-request governance markers on each usage-ledger row so request detail can explain what policy applied when the row was written.

**Rationale:** M007 already established request detail as the authoritative persisted evidence seam. If governance is only inferred from current policy, historical request proof becomes muddy after policy changes.

**Alternatives Considered:**
- Show only current tenant policy — rejected because it weakens historical truthfulness.
- Prove governance mostly in docs/tests — rejected because this milestone needs request-led operator proof, not only external explanation.

### Retention means real deletion

**Decision:** Treat evidence retention as actual deletion of expired evidence, not visibility-only expiry.

**Rationale:** The milestone’s trust claim is that operators can deliberately bound what Nebula keeps. Hiding old rows without deleting them would undercut that claim.

**Alternatives Considered:**
- Visibility-only hiding — rejected because stored evidence would still exist.
- Summarize then age out — deferred because it adds a second lifecycle model before basic governed deletion is proven.

## Error Handling Strategy

Governance controls should fail closed. Invalid governance policy values should be rejected at the API/schema boundary with explicit validation errors. If a request cannot persist governed evidence safely, Nebula should surface a clear server-side failure rather than silently widening or ignoring the policy boundary. Retention execution should be idempotent and observable: repeated cleanup passes should not fail on already-removed rows, and health/detail surfaces should make it clear whether the retention path is operational or degraded. Hosted export should continue to rely on its explicit allowlist contract so any mismatch between tenant evidence governance and hosted metadata export becomes a visible contract bug, not an ambiguous runtime behavior.

## Risks and Unknowns

- Metadata minimization could cut too aggressively and weaken Nebula’s request-led debugging story — the milestone must prove suppression without collapsing operator explainability
- Historical policy truth could be misrepresented if request detail relies on current tenant policy instead of persisted per-request governance markers
- Real retention deletion needs a bounded execution seam; if the lifecycle path is hand-waved, the milestone trust claim will be weak
- Existing advisory prompt/response capture flags could tempt scope drift into payload capture or privacy-platform work if not kept explicitly out of scope
- Hosted trust-boundary language could drift if tenant-governed evidence policy is described as widening hosted authority or export scope

## Existing Codebase / Prior Art

- `src/nebula/models/governance.py` — `TenantPolicy` already carries advisory `prompt_capture_enabled` and `response_capture_enabled` flags, but no real evidence-governance model yet
- `src/nebula/db/models.py` — `TenantPolicyModel` and `UsageLedgerModel` show the current persistence seam; the ledger has no retention or per-request governance-marker fields today
- `src/nebula/services/governance_store.py` — current policy persistence and usage-ledger recording seam; likely source of truth for governed row shape and retention operations
- `src/nebula/services/chat_service.py` and `src/nebula/api/routes/embeddings.py` — current request-evidence write paths that will need governed persistence behavior
- `console/src/components/ledger/ledger-request-detail.tsx` — authoritative persisted-evidence seam established in M007; this is where historical governance markers should be explained without displacing the row as primary evidence
- `console/src/components/policy/policy-form.tsx` and `console/src/components/policy/policy-advanced-section.tsx` — existing bounded policy editor and the explicit placeholder that capture settings were deferred to a future governance/privacy phase
- `src/nebula/models/hosted_contract.py` and `docs/hosted-default-export.schema.json` — canonical hosted metadata-only allowlist contract that M008 must preserve and align with, not widen

## Relevant Requirements

- R056 — typed tenant evidence-retention policy
- R057 — typed tenant metadata-minimization policy without payload capture widening
- R058 — historical request explainability via persisted governance markers
- R059 — retention as real deletion
- R060 — effective evidence boundary visible in policy and request detail
- R061 — hosted metadata-only boundary stays aligned
- R062 — full end-to-end proof across policy, persistence, retention, operator surface, and hosted contract
- R063 — preserve request-led debugging value while tightening governance
- R064 — maintain anti-sprawl discipline

## Scope

### In Scope

- typed tenant-policy controls for evidence retention and metadata minimization
- governed persistence behavior on the usage-ledger path and any aligned export boundary seams
- persisted governance markers on request evidence rows so historical request detail remains truthful after later policy changes
- real retention execution with actual deletion of expired evidence
- bounded operator visibility for effective evidence policy in policy and request-detail surfaces
- integrated docs and proof showing how tenant evidence governance fits Nebula’s hosted metadata-only trust model

### Out of Scope / Non-Goals

- broad compliance platform features such as legal hold workflows, approval chains, or audit-report generation
- broad RBAC / enterprise permissions redesign
- raw prompt or raw response persistence expansion
- dashboard-heavy analytics work around governance
- hosted authority expansion or hosted policy enforcement
- unrelated product areas outside Nebula’s request/policy/evidence core

## Technical Constraints

- Keep governance controls tenant-centric unless execution proves that model fundamentally insufficient
- Preserve request detail as the authoritative persisted evidence record; do not replace it with policy summaries or dashboard framing
- Keep hosted export metadata-only by default and treat the explicit allowlist contract as canonical
- Make retention verifiably real; visibility-only hiding is not enough
- Do not silently reinterpret the existing advisory capture booleans into payload-persistence scope creep
- Keep policy UX consistent with the M007 compare-before-save decision flow rather than turning the policy page into a second governance dashboard

## Integration Points

- `PUT /v1/admin/tenants/{tenant_id}/policy` — tenant-governed evidence controls live here
- `GET /v1/admin/policy/options` — should expose which governance fields are runtime-enforced vs advisory
- `GET /v1/admin/usage/ledger` — request evidence read path that must reflect governed row shape and deletion outcomes
- `console/src/components/ledger/ledger-request-detail.tsx` — operator surface for historical governance markers on the selected row
- `src/nebula/services/chat_service.py` / `src/nebula/api/routes/embeddings.py` — real request paths that must persist governed evidence
- `src/nebula/models/hosted_contract.py` and `docs/hosted-default-export.schema.json` — hosted metadata-only contract that must remain intact

## Testing Requirements

M008 needs backend unit/integration tests for policy validation, governed ledger persistence, per-request governance markers, and retention deletion behavior. It also needs focused admin API tests proving the typed policy and request-evidence read path, plus focused console Vitest coverage for policy and request-detail governance visibility. If retention execution uses an app lifecycle or explicit cleanup path, that path must be exercised directly in tests rather than left as an implied future operational behavior. Final milestone proof should include integrated contract checks tying tenant policy to a real persisted request, request-detail explanation, retention expiration/deletion, and hosted-boundary alignment.

## Acceptance Criteria

- tenant policy exposes explicit evidence-retention and metadata-minimization controls as typed enforced fields
- governed requests persist only the allowed metadata shape and record governance markers needed for later historical explanation
- retention windows cause real deletion of expired evidence
- policy and request-detail surfaces clearly show the effective evidence boundary without replacing request-led proof with dashboard framing
- hosted metadata-only contract remains aligned and explicitly bounded after governance changes
- one integrated proof path demonstrates policy → persistence → request inspection → retention deletion → hosted-boundary consistency

## Open Questions

- Which exact evidence fields remain mandatory for Nebula’s request-led debugging story even under metadata minimization — current thinking: keep enough route/provider/policy/request-correlation evidence to preserve explainability while suppressing non-essential detail
- What is the cleanest bounded execution seam for retention deletion in this codebase — current thinking: treat it as an explicit governed-store lifecycle path rather than an external manual process
- Whether existing advisory capture flags should remain visible as deferred/non-active markers or be folded into the new typed governance model more explicitly — current thinking: keep payload capture out of scope and avoid implying future widening by accident
