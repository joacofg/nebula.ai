# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. v3.x established Nebula's adoption and hosted-reinforcement story. v4.x turned Nebula’s existing evidence, policy, routing, and cache surfaces into a stronger decisioning control plane. The next planned milestone is M006, which closes the remaining routing gap by making route choice outcome-aware, calibrated, and still interpretable.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and now increasingly trustworthy routing decisions.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, embeddings, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract.

M001 through M004 are complete in the assembled worktree and establish the adoption, production-structuring, embeddings, and hosted-reinforcement stories. M005 is also complete and passed milestone close-out verification, delivering Nebula’s first real decisioning control plane: interpretable route signals and route-score exposure, replay-only policy simulation, hard cumulative budget guardrails, bounded recommendation-grade feedback, semantic-cache runtime summaries and tenant-scoped cache tuning controls, and a final integrated proof in `docs/v4-integrated-proof.md` with discoverability links from `README.md` and `docs/architecture.md`.

One active requirement remains: R039. Nebula’s routing evidence is materially better than before, but the scoring model is still heuristic-first rather than fully outcome-aware. M006 is planned to close that gap with calibrated routing grounded in tenant-scoped ledger evidence while preserving Nebula’s anti-sprawl and trust-boundary guardrails.

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
