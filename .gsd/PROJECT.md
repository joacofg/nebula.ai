# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. The current planning track is v3.x, focused on API adoption and developer experience: making it easy for application teams to replace direct provider calls with Nebula, understand the integration contract quickly, and see clear operational value on day 1.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, and provider abstraction immediately.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract. M001 is complete in this worktree and passed close-out verification after the canonical adoption artifacts were restored into the assembled branch. Nebula now has a bounded public `POST /v1/chat/completions` contract, a supported self-hosted quickstart, a production-model explanation, a realistic reference migration proof, and day-1/operator-visible value surfaces across Playground, usage-ledger correlation, and Observability.

M002 is complete in this worktree and passed milestone close-out verification. The highest-impact operator-facing console surfaces now align to the runtime-truth tenant/API-key model: API Keys explains tenant inference versus explicit `X-Nebula-Tenant-ID`, Playground is framed as an admin-only non-streaming corroboration surface, Observability is framed as persisted request evidence plus dependency-health context, and the Tenants page/drawer explain how teams should map conceptual apps and workloads through real tenants, API keys, and optional notes without inventing app/workload product objects. The integrated walkthrough in `docs/integrated-adoption-proof.md` now composes the final production-structuring story in the correct order: tenant/API-key structuring, conditional tenant-header decision, public request, `X-Request-ID`/`X-Nebula-*` header capture, usage-ledger correlation, then admin corroboration via Tenants, Playground, and Observability. Focused Vitest coverage for those truth surfaces passed again during close-out (`6 files, 16 tests`), locking the operator-boundary and pseudo-entity guardrails in the assembled worktree.

M003 is complete in this worktree and passed milestone close-out verification. Nebula now exposes a real authenticated `POST /v1/embeddings` path under the existing `/v1` prefix, backed by a deliberately narrow OpenAI-style contract: `model` plus `input` as either a string or flat list of strings, returning standard float-vector embeddings output. The embeddings service forwards caller-supplied models, preserves batch ordering, and distinguishes validation, upstream, and empty-result failures explicitly. The public route reuses existing tenant/API-key auth and emits `X-Request-ID` that correlates directly to metadata-only usage-ledger evidence (`final_route_target="embeddings"`, provider/status/reason/policy fields) without storing raw inputs or vectors. `docs/embeddings-adoption-contract.md` is now the single canonical embeddings contract, `docs/embeddings-reference-migration.md` plus `tests/test_embeddings_reference_migration.py` provide the realistic minimal-change migration proof, and `docs/embeddings-integrated-adoption-proof.md` assembles the full proof path in the correct order: public request, `X-Request-ID`/`X-Nebula-*` headers, `GET /v1/admin/usage/ledger?request_id=...`, then Observability corroboration. Shared Observability ledger surfaces now intentionally support embeddings correlation through route-target filtering, visible `request_id`, and persisted outcome details without introducing new storage, helper SDKs, hosted-plane expansion, or unrelated infrastructure work. Close-out reverified the assembled milestone with passing focused pytest runs for `tests/test_embeddings_reference_migration.py`, `tests/test_embeddings_api.py`, and `tests/test_governance_api.py -k embeddings`.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing product proof is benchmark- and operator-surface-heavy; v3.x shifts emphasis toward real developer adoption proof. Internal embeddings capability already exists through `src/nebula/services/embeddings_service.py` and is used by semantic cache and runtime health, but it is not yet exposed as a public adoption surface.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: API Adoption Happy Path — Established the canonical public chat-completions adoption path, self-hosted quickstart, production model, realistic migration proof, and day-1 operator-visible value story.
- [x] M002: Production Structuring Model — Clarified the runtime-truth production model across API Keys, Tenants, Playground, Observability, and the integrated walkthrough so operators can structure production around real tenants and API keys without inventing app/workload runtime objects.
- [x] M003: Broader Adoption Surface — Extended Nebula beyond chat completions through a narrow public embeddings adoption path with tight compatibility boundaries, realistic migration proof, durable evidence correlation, and a final integrated adoption walkthrough.
- [ ] M004: Hosted Adoption Reinforcement — Improve hosted/control-plane touches only where they strengthen onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
