# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. The current planning track is v3.x, focused on API adoption and developer experience: making it easy for application teams to replace direct provider calls with Nebula, understand the integration contract quickly, and see clear operational value on day 1.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, provider abstraction, and trustworthy operator visibility immediately.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract. M001 completed the canonical chat-completions adoption path, self-hosted quickstart, production model, realistic migration proof, and day-1 operator-visible value story. M002 completed the production-structuring clarification across API Keys, Tenants, Playground, Observability, and the integrated walkthrough so operators can structure production around real tenants and API keys without inventing app/workload runtime objects. M003 completed the broader adoption surface by adding a narrow public embeddings path, canonical contract docs, realistic migration proof, durable evidence correlation, and final integrated assembly without widening into parity, SDK sprawl, or hosted-plane expansion.

Nebula also already has meaningful hosted/control-plane groundwork in the console and backend. The hosted side exposes deployment inventory, enrollment-token flow, linked deployment detail, freshness states, dependency summaries, bounded remote action history, a public trust-boundary page, and a schema-backed metadata-only hosted export contract. The hosted plane remains optional, metadata-only by default, and non-authoritative for local runtime enforcement.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing product proof is benchmark- and operator-surface-heavy; v3.x shifts emphasis toward real developer adoption proof, durable request evidence, and truthful operator framing. Hosted console work should derive wording and semantics from the actual hosted contract and deployment models instead of inventing new authority or pseudo-runtime state.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: API Adoption Happy Path — Established the canonical public chat-completions adoption path, self-hosted quickstart, production model, realistic migration proof, and day-1 operator-visible value story.
- [x] M002: Production Structuring Model — Clarified the runtime-truth production model across API Keys, Tenants, Playground, Observability, and the integrated walkthrough so operators can structure production around real tenants and API keys without inventing app/workload runtime objects.
- [x] M003: Broader Adoption Surface — Extended Nebula beyond chat completions through a narrow public embeddings adoption path with tight compatibility boundaries, realistic migration proof, durable evidence correlation, and a final integrated adoption walkthrough.
- [ ] M004: Hosted Adoption Reinforcement — Improve hosted/control-plane touches only where they strengthen onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary or local runtime authority. S01, S02, and S03 are now complete: S01 centralized hosted reinforcement vocabulary, prohibited authority claims, bounded-action phrasing, and downstream acceptance rules in the shared hosted-contract seam, S02 added a real hosted fleet-posture reading layer on the deployments page via shared posture derivation, a top-of-page fleet summary, scan-time row cues for pending/linked/stale/offline/revoked/unlinked states, and aligned bounded-action availability semantics across the table and RemoteActionCard for S03 reuse, and S03 assembled the canonical hosted integrated proof doc plus focused Vitest and Playwright walkthrough coverage that proves the public trust-boundary page, deployments entrypoint, mixed-fleet interpretation, drawer trust disclosure, and bounded credential-rotation framing all reinforce confidence without shifting serving-time authority away from the local runtime.
