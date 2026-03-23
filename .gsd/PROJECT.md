# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing, fallback behavior, or operator visibility. v1.0 and v2.0 are already complete. The current planning track is v3.x, focused on API adoption and developer experience: making it easy for application teams to replace direct provider calls with Nebula, understand the integration contract quickly, and see clear operational value on day 1.

## Core Value

A team can adopt Nebula through a familiar inference path quickly, with minimal application changes, while gaining routing, policy, observability, and provider abstraction immediately.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, OpenAI-like chat completions, streaming support, tenant and API-key management, policy management, usage ledger recording, runtime health, and an optional hosted control plane with a metadata-only default export contract. M001 is now complete: the public `POST /v1/chat/completions` adoption boundary is explicit and test-backed in `docs/adoption-api-contract.md`; the supported self-hosted quickstart and operating-model references live in `docs/quickstart.md` and `docs/production-model.md`; the repo includes a canonical migration proof in `docs/reference-migration.md` plus executable request-to-ledger correlation coverage in `tests/test_reference_migration.py`; the day-1 value walkthrough lives in `docs/day-1-value.md` with aligned Playground, ledger, and Observability surfaces; and S05 added `docs/integrated-adoption-proof.md` as the final joined walkthrough tying together public request execution, `X-Nebula-*`/`X-Request-ID` response evidence, usage-ledger correlation, Playground corroboration, and Observability persisted explanation plus dependency health. Remaining verification gaps in this worktree are environmental or unrelated blockers (`pytest` missing locally and a pre-existing console compile error in `console/src/components/deployments/remote-action-card.tsx` that blocks Playwright startup), not open M001 scope.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths, returning `X-Nebula-*` metadata headers and persisting usage outcomes to the governance ledger. The backend is FastAPI with a service-container pattern; the operator console is Next.js and proxies same-origin admin traffic to gateway APIs. Governance is tenant-centric today. The hosted control plane is metadata-only by default and is not authoritative for local runtime enforcement. Existing product proof is benchmark- and operator-surface-heavy; v3.x shifts emphasis toward real developer adoption proof.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: API Adoption Happy Path — Make Nebula easy to plug into for common chat-completions usage, define the compatibility boundary clearly, and prove migration with a real reference integration.
- [ ] M002: Production Structuring Model — Clarify how teams should structure tenant, app, workload, and operator boundaries across docs and product surfaces.
- [ ] M003: Broader Adoption Surface — Expand the adoption surface beyond the initial happy path only where real demand and proof justify it.
- [ ] M004: Hosted Adoption Reinforcement — Improve hosted/control-plane touches only where they strengthen onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
