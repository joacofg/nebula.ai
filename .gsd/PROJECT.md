# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. v3.x established Nebula's adoption and hosted-reinforcement story. v4.x turned Nebula’s existing evidence, policy, routing, and cache surfaces into a stronger decisioning control plane, and M007 clarified the operator console into a more coherent request-led decision system.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and interpretable operator evidence that stays under local operator control.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, embeddings, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract.

M001 through M007 are complete in the assembled worktree. M007 closed the operator-decision-clarity milestone: Observability is request-investigation-first, `ledger-request-detail` remains the authoritative persisted evidence seam for the selected request, and policy preview is a compare-before-save decision surface rather than a blended analytics/settings page. The current product can explain routed requests, policy outcomes, replay consequences, cache posture, calibration posture, and hosted deployment posture without widening into dashboard sprawl or hosted authority.

What is still missing is explicit governance over Nebula’s evidence boundary. Tenant policy already contains advisory capture flags, the usage ledger persists request evidence, and the hosted plane already enforces a metadata-only allowlist contract, but operators still cannot deliberately govern evidence retention windows, metadata minimization, historical request-level governance markers, or real evidence deletion behavior through one bounded product story. M008 is the next planned milestone to close that gap.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing decisioning work favors stable typed evidence, bounded operator-facing read models, request-led operator proof, and pointer-only integrated proof docs over duplicated contracts or opaque optimization claims.

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
