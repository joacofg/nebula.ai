# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. v3.x established Nebula's adoption and hosted-reinforcement story. v4.x turned Nebula’s existing evidence, policy, routing, and cache surfaces into a stronger decisioning control plane. M006 has now assembled the calibrated-routing close-out story in the worktree.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and now stronger calibrated-routing evidence that remains interpretable to operators.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, embeddings, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract.

M001 through M006 are complete in the assembled worktree. M006 closed the calibrated-routing milestone end to end: live routing and replay now share a calibrated scoring contract; route evidence exposes calibrated-versus-degraded mode plus additive score components; tenant policy includes a bounded `calibrated_routing_enabled` rollout valve; tenant-scoped calibration evidence is derived from existing usage-ledger metadata with explicit sufficient/thin/stale/gated/degraded classification; policy simulation changed-request samples report the same calibrated/degraded/rollout-disabled routing semantics as live runtime; Observability and request-detail keep the selected persisted request authoritative; and `docs/m006-integrated-proof.md` joins the public request, `X-Request-ID` / `X-Nebula-*` headers, usage-ledger correlation, replay parity, bounded degraded or rollout-disabled semantics, and selected-request-first operator inspection into one pointer-only close-out path.

M007 has S01 through S03 complete. The console still follows the explicit operator-surface role contract from S01, S02 tightened the supporting seams underneath it, and S03 has now reworked Observability into a selected-request-first investigation flow. Operators now land on one selected persisted ledger row as the clear lead object, `LedgerRequestDetail` remains the authoritative evidence seam, recommendations/calibration/cache/dependency health are visibly subordinate follow-up context for that same request, and the request table uses bounded `aria-selected` / pressed-button affordances plus a `Current investigation` cue instead of drifting into a second explorer surface. Fresh focused Vitest coverage guards page order, scoped supporting-card hierarchy, selector semantics, and anti-drift boundaries before the remaining policy-preview flow work in S04/S05.

R039-R049 are now represented and validated in the requirement contract. The routed-request story is stronger without widening Nebula into a black-box optimizer, analytics product, hosted-authority expansion, or unrelated platform program. The next planned work is M007: Operator Decision Clarity, which treats Nebula’s current weakness as page-identity blur across operator surfaces and focuses on making the console feel like a coherent decision system rather than a collection of proof surfaces.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing decisioning work favors stable typed evidence, bounded operator-facing read models, and pointer-only integrated proof docs over duplicated contracts or opaque optimization claims.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: API Adoption Happy Path — Established the bounded public chat-completions adoption contract, canonical self-hosted quickstart and production model, realistic reference migration proof, and the integrated day-1 operator-visible value story across Playground, usage-ledger correlation, and Observability.
- [x] M002: Production Structuring Model — Clarified the runtime-truth production model across API Keys, Tenants, Playground, Observability, and the integrated walkthrough so operators can structure production around real tenants and API keys without inventing app/workload runtime objects.
- [x] M003: Broader Adoption Surface — Extended Nebula beyond chat completions through a narrow public embeddings adoption path with tight compatibility boundaries, realistic migration proof, durable evidence correlation, and a final integrated adoption walkthrough.
- [x] M004: Hosted Adoption Reinforcement — Improved hosted/control-plane touches where they strengthened onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
- [x] M005: Adaptive Decisioning Control Plane — Turned Nebula’s existing routing, ledger, cache, and policy surfaces into a safer, more effective operator decisioning system through adaptive routing, simulation, hard guardrails, and recommendation-grade feedback.
- [x] M006: Outcome-Aware Routing Calibration — Completed the calibrated-routing milestone with shared runtime/replay semantics, bounded rollout control, tenant-scoped ledger-backed calibration evidence, selected-request-first operator inspection, and a pointer-only close-out walkthrough that validates the assembled outcome-aware-routing proof.
- [ ] M007: Operator Decision Clarity — Clarify page identity, evidence hierarchy, and operator decision workflow across Observability, request detail, and policy preview without drifting into dashboard sprawl or a broad redesign.
