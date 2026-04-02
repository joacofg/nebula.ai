# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. v3.x established Nebula's adoption and hosted-reinforcement story. v4.x turned Nebula’s existing evidence, policy, routing, and cache surfaces into a stronger decisioning control plane. The next planned milestone is M006, which closes the remaining routing gap by making route choice outcome-aware, calibrated, and still interpretable.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and now increasingly trustworthy routing decisions.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, embeddings, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract.

M001 through M005 are complete in the assembled worktree and establish the adoption, production-structuring, embeddings, hosted-reinforcement, and first decisioning-control-plane stories. M006 is underway with S01 and S02 complete: live routing and replay share a calibrated scoring contract; route evidence exposes calibrated-versus-heuristic/degraded mode plus additive score components; tenant policy includes a bounded `calibrated_routing_enabled` rollout valve; and tenant-scoped calibration evidence is now derived from existing usage-ledger metadata with explicit sufficient/thin/stale/gated/degraded classification reused across simulation payloads, Observability, and ledger request detail surfaces.

One active requirement remains: R039. Nebula’s route evidence, calibration vocabulary, and operator control are materially stronger, but outcome-aware calibration is still only partially assembled. Later M006 slices still need full runtime/simulation parity proof, broader operator inspection closure, and integrated milestone proof before R039 can move to validated.

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
- [ ] M006: Outcome-Aware Routing Calibration — Close the remaining routing gap by adding interpretable, ledger-backed calibration to live routing and replay, explicit degraded-mode behavior, bounded operator inspection, and final proof that validates R039 without black-box or analytics drift.
