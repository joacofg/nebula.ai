# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. v3.x established Nebula's adoption and hosted-reinforcement story. v4.x turned Nebula’s existing evidence, policy, routing, and cache surfaces into a stronger decisioning control plane. M006 has now assembled the calibrated-routing close-out story in the worktree.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and now stronger calibrated-routing evidence that remains interpretable to operators.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, embeddings, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract.

M001 through M007 are complete in the assembled worktree. M006 closed the calibrated-routing milestone end to end: live routing and replay now share a calibrated scoring contract; route evidence exposes calibrated-versus-degraded mode plus additive score components; tenant policy includes a bounded `calibrated_routing_enabled` rollout valve; tenant-scoped calibration evidence is derived from existing usage-ledger metadata with explicit sufficient/thin/stale/gated/degraded classification; policy simulation changed-request samples report the same calibrated/degraded/rollout-disabled routing semantics as live runtime; Observability and request-detail keep the selected persisted request authoritative; and `docs/m006-integrated-proof.md` joins the public request, `X-Request-ID` / `X-Nebula-*` headers, usage-ledger correlation, replay parity, bounded degraded or rollout-disabled semantics, and selected-request-first operator inspection into one pointer-only close-out path.

M007 has now closed the operator-decision-clarity milestone. Observability is assembled and verified as a selected-request-first investigation surface, `LedgerTable` keeps request selection bounded to an explicit current-investigation affordance, `ledger-request-detail` remains the authoritative persisted evidence seam for the selected request, and policy preview stays a compare-before-save decision surface that clears stale preview state on tenant switch and save success. `docs/m007-integrated-proof.md` now gives one pointer-only review path across those shipped seams, `README.md` and `docs/architecture.md` make that proof discoverable, and the focused six-file console Vitest bundle passed unchanged at close-out (`page.test.tsx`, `observability-page.test.tsx`, `ledger-request-detail.test.tsx`, `ledger-table.test.tsx`, `policy-form.test.tsx`, `policy-page.test.tsx`, 39/39 tests). The assembled story clarifies page identity and next-step decision flow without widening Nebula into a dashboard, routing studio, analytics product, redesign-sprawl effort, or parallel operator workflow.

R039-R049 remain represented and validated in the requirement store. M007 evidence for R050-R055 is fully assembled and recorded in `M007-SUMMARY.md`, but the current GSD requirement store rejected `gsd_requirement_update` for all five IDs with `Requirement R05x not found` even though the rendered `.gsd/REQUIREMENTS.md` includes them. Treat that as a requirement-store synchronization mismatch, not missing milestone proof. The next planned work should build on the now-closed operator decision system rather than re-opening page identity or proof-order questions already locked in M007.

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
- [x] M007: Operator Decision Clarity — Clarified page identity, evidence hierarchy, and operator decision workflow across Observability, request detail, and policy preview without drifting into dashboard sprawl or a broad redesign.
