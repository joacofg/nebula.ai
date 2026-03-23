# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. The current planning track is v3.x, focused on API adoption and developer experience: making it easy for application teams to replace direct provider calls with Nebula, understand the integration contract quickly, and see clear operational value on day 1.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, and provider abstraction immediately.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract. S01 and S02 of M001 are now complete: the public `POST /v1/chat/completions` adoption boundary is explicit, test-backed, and documented in `docs/adoption-api-contract.md`, and the repo now has a canonical self-hosted quickstart (`docs/quickstart.md`) plus a canonical production-model reference (`docs/production-model.md`) that explain the supported first-request path, admin-vs-client credential split, tenant-header rules, and the current runtime truth that tenant/policy/API key/operator are real entities while app/workload remain conceptual guidance in M001. What remains weak is the realistic migration proof in S03 and the joined-up day-1 value proof across docs, runtime, and operator surfaces in S04/S05. Verification in this worktree confirmed the documentation integrity layer, but backend and console executable checks still need rerun in a provisioned environment because local `pytest` and `vitest` tooling were missing.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing product proof is benchmark- and operator-surface-heavy; v3.x shifts emphasis toward real developer adoption proof.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: API Adoption Happy Path — Make Nebula easy to plug into for common chat-completions usage, define the compatibility boundary clearly, and prove migration with a real reference integration.
- [ ] M002: Production Structuring Model — Clarify how teams should structure tenant, app, workload, and operator boundaries across docs and product surfaces.
- [ ] M003: Broader Adoption Surface — Expand the adoption surface beyond the initial happy path only where real demand and proof justify it.
- [ ] M004: Hosted Adoption Reinforcement — Improve hosted/control-plane touches only where they strengthen onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
