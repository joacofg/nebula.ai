# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. v3.x established Nebula's adoption and hosted-reinforcement story. v4.x turned Nebula’s existing evidence, policy, routing, and cache surfaces into a stronger decisioning control plane, and M007 clarified the operator console into a more coherent request-led decision system.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and interpretable operator evidence that stays under local operator control.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, embeddings, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract.

M001 through M007 are complete in the assembled worktree. M007 closed the operator-decision-clarity milestone: Observability is request-investigation-first, `ledger-request-detail` remains the authoritative persisted evidence seam for the selected request, and policy preview is a compare-before-save decision surface rather than a blended analytics/settings page.

M008 is in progress with S01 and S02 complete. S01 established the typed evidence-governance contract across backend persistence and operator policy surfaces: tenant policy now includes explicit `evidence_retention_window` and `metadata_minimization_level` fields, governed usage-ledger writes stamp each row with request-time governance markers such as message type, expiration, suppressed metadata fields, and governance source, and the console policy/request-detail surfaces expose those controls and markers as runtime-enforced evidence boundaries rather than advisory capture settings. S02 completed the next runtime leg of that contract: `GovernanceStore` now has an explicit `delete_expired_usage_records(now=...)` lifecycle seam that deletes rows using the persisted `evidence_expires_at` marker rather than current-policy inference, admin ledger tests prove surviving rows keep their historical governance markers while expired rows disappear from `/v1/admin/usage/ledger`, and request-detail copy now explains that a persisted row is authoritative only while it exists and may later vanish when governed cleanup removes expired evidence. Hosted export remains metadata-only and no raw prompt/response capture was added.

What remains for M008 is to build on that contract: S03 must operationalize retention cleanup execution beyond the callable store seam, S04 must make the effective evidence boundary clearer in operator inspection surfaces, and S05 must assemble the end-to-end proof that tenant policy governs persistence/deletion without widening Nebula into payload capture, compliance-platform sprawl, or hosted authority.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing decisioning work favors stable typed evidence, bounded operator-facing read models, request-led operator proof, and pointer-only integrated proof docs over duplicated contracts or opaque optimization claims.

M008 extends those patterns by keeping evidence governance inside the existing policy and ledger boundaries. The central write-time enforcement seam remains `GovernanceStore.record_usage()`, which applies tenant retention/minimization policy at write time for both chat and embeddings and persists historically truthful governance markers on each ledger row for later inspection. The central lifecycle seam is now `GovernanceStore.delete_expired_usage_records(now=...)`, which performs explicit local deletion using persisted row-level expiration markers; operator read paths continue to rely on `/v1/admin/usage/ledger` and request detail rather than a separate retention dashboard or export path.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: API Adoption Happy Path — Established the bounded public chat-completions adoption contract, canonical self-hosted quickstart and production model, realistic reference migration proof, and the integrated day-1 operator-visible value story across Playground, usage-ledger correlation, and Observability.
- [x] M002: Production Structuring Model — Clarified the runtime-truth production model across API Keys, Tenants, Playground, Observability, and the integrated walkthrough so operators can structure production around real tenants and API keys without inventing app/workload runtime objects.
- [x] M003: Broader Adoption Surface — Extended Nebula beyond chat completions through a narrow public embeddings adoption path with tight compatibility boundaries, realistic migration proof, durable evidence correlation, and a final integrated adoption walkthrough.
- [x] M004: Hosted Adoption Reinforcement — Improved hosted/control-plane touches where they strengthened onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
- [x] M005: Adaptive Decisioning Control Plane — Turned Nebula’s existing routing, ledger, cache, and policy surfaces into a safer, more effective operator decisioning system through adaptive routing, simulation, hard guardrails, and recommendation-grade feedback.
- [x] M006: Outcome-Aware Routing Calibration — Completed the calibrated-routing milestone with shared runtime/replay semantics, bounded rollout control, tenant-scoped ledger-backed calibration evidence, selected-request-first operator inspection, and a pointer-only close-out walkthrough that validates the assembled outcome-aware-routing proof.
- [x] M007: Operator Decision Clarity — Clarified page identity, evidence hierarchy, and operator decision workflow across Observability, request detail, and policy preview without drifting into dashboard sprawl or a broad redesign.
- [ ] M008: Evidence Governance and Privacy Controls — Make Nebula’s evidence layer tenant-governed, retention-aware, historically explainable, and visibly bounded without widening into payload capture, compliance-platform sprawl, or hosted authority.
  - [x] S01: Typed evidence governance policy — Tenant policy, admin APIs, governed ledger persistence, and console policy/request-detail surfaces now share typed retention/minimization controls and request-time governance markers.
  - [x] S02: Governed ledger persistence and request markers — Explicit local cleanup now deletes expired rows via persisted `evidence_expires_at`, surviving rows retain historical governance markers through the admin ledger seam, and request detail explains that governed evidence may disappear after cleanup rather than soft-delete.
  - [ ] S03: Retention lifecycle enforcement
  - [ ] S04: Operator evidence-boundary surfaces
  - [ ] S05: Integrated governance proof
