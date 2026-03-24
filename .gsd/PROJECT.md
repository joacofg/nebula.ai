# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. The current planning track is v3.x, focused on API adoption and developer experience: making it easy for application teams to replace direct provider calls with Nebula, understand the integration contract quickly, and see clear operational value on day 1.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, and provider abstraction immediately.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract. M001 slice work established the intended API-adoption story: a bounded public `POST /v1/chat/completions` contract, a self-hosted quickstart, a production-model explanation, a reference migration proof, and day-1/operator-visible value surfaces across Playground, ledger, and Observability. However, milestone close-out in this worktree did **not** pass integrated verification: the current diff against `main` shows several milestone-critical deliverables deleted from the assembled state (`docs/adoption-api-contract.md`, `docs/quickstart.md`, `docs/production-model.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, `docs/integrated-adoption-proof.md`, and `tests/test_reference_migration.py`). As a result, M001 is historically implemented but presently incomplete in this worktree snapshot and needs those canonical adoption artifacts restored before it can be treated as cleanly complete.

M002 is now in progress with S01 and S02 complete in this worktree. The highest-impact operator-facing console surfaces now align to the runtime-truth tenant/API-key model: API Keys explains tenant inference versus explicit `X-Nebula-Tenant-ID`, Playground is framed as an admin-only non-streaming corroboration surface, Observability is framed as persisted request evidence plus dependency-health context, and the Tenants page/drawer now explain how teams should map conceptual apps and workloads through real tenants, API keys, and optional notes without inventing app/workload product objects. S03 remains to assemble the integrated production-structuring walkthrough.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing product proof is benchmark- and operator-surface-heavy; v3.x shifts emphasis toward real developer adoption proof.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: API Adoption Happy Path — Slice work is complete, but milestone close-out failed integrated verification in this worktree because several canonical adoption docs and the reference-migration proof file are currently absent from the assembled state.
- [ ] M002: Production Structuring Model — Clarify how teams should structure tenant, app, workload, and operator boundaries across docs and product surfaces.
- [ ] M003: Broader Adoption Surface — Expand the adoption surface beyond the initial happy path only where real demand and proof justify it.
- [ ] M004: Hosted Adoption Reinforcement — Improve hosted/control-plane touches only where they strengthen onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
