# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing behavior, fallback handling, or operator-visible evidence. v1.0 and v2.0 are complete. v3.x established Nebula’s bounded public adoption path and hosted metadata-only trust story. v4.x strengthened Nebula’s operator control plane through simulation, guardrails, recommendation-grade feedback, calibrated routing, operator-surface clarity, and governed evidence retention. M009 now focuses on Outcome-Grounded Routing Quality: improving the routing core itself using bounded recent tenant-scoped outcome evidence while preserving Nebula’s explainability, replay credibility, request-first operator inspection, and local authority.

## Core Value

A team can point real application traffic at Nebula and get lower-cost, more reliable model routing decisions that remain interpretable, replayable, and operator-controlled rather than opaque or hosted-authoritative.

## Current State

Nebula already ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, public chat completions and embeddings routes, policy simulation, hard budget guardrails, bounded recommendation surfaces, calibrated routing evidence, request-first Observability, and tenant-governed evidence retention with a metadata-only hosted boundary. M001 through M008 are complete. In M009, S01 and S02 are now complete. S01 locked the shared backend outcome-evidence contract through deterministic tenant-scoped GovernanceStore summarization, explicit `sufficient`/`thin`/`stale`/`degraded` state semantics, and replay/admin-safe typed artifacts and tests. S02 wired that contract into live route choice and request persistence: `PolicyService.evaluate()` now fetches bounded tenant-scoped outcome evidence immediately before route selection, runtime routing can change because of recent evidence, and the correlated usage-ledger row persists the exact outcome-grounded factors and additive score components used for the live decision. Remaining M009 work is to reuse the same semantics for replay parity (S03), expose the grounded/thin/stale/degraded story on existing request-first operator surfaces (S04), and close the milestone with integrated proof and anti-drift artifacts (S05).

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths and persists operator-visible usage outcomes in a governance ledger. The backend is FastAPI with typed Pydantic models and service-container dependency injection. The console is a Next.js App Router operator UI that proxies same-origin admin traffic to backend APIs and keeps request evidence primary on Observability surfaces. Existing control-plane work prefers typed evidence contracts, bounded additive scoring, deterministic replay, request-first operator proof, and pointer-only integrated proof docs over duplicated contracts, dashboard sprawl, hidden optimization, or hosted decision authority. For M009 specifically, `GovernanceStore.summarize_calibration_evidence()` is the authoritative seam for tenant-scoped outcome-evidence classification in both live and replay-oriented flows, the compatibility field name `calibration_summary` remains the shared serialized carrier for the richer state vocabulary, and request-level route diagnostics should be extended additively rather than replaced so headers, ledger rows, and operator reads stay correlatable.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: API Adoption Happy Path — Established the bounded public chat-completions adoption contract, canonical self-hosted quickstart and production model, realistic reference migration proof, and the integrated day-1 operator-visible value story across Playground, usage-ledger correlation, and Observability.
- [x] M002: Production Structuring Model — Clarified the runtime-truth production model across API keys, tenants, Playground, Observability, and the integrated walkthrough so operators can structure production around real tenants and API keys without inventing app/workload runtime objects.
- [x] M003: Broader Adoption Surface — Extended Nebula beyond chat completions through a narrow public embeddings adoption path with tight compatibility boundaries, realistic migration proof, durable evidence correlation, and a final integrated adoption walkthrough.
- [x] M004: Hosted Adoption Reinforcement — Improved hosted/control-plane surfaces where they strengthened onboarding, fleet understanding, and operator confidence without violating the metadata-only trust boundary.
- [x] M005: Adaptive Decisioning Control Plane — Turned Nebula’s existing routing, ledger, cache, and policy surfaces into a safer, more effective operator decisioning system through adaptive routing, simulation, hard guardrails, and recommendation-grade feedback.
- [x] M006: Outcome-Aware Routing Calibration — Completed the calibrated-routing milestone with shared runtime/replay semantics, bounded rollout control, tenant-scoped ledger-backed calibration evidence, selected-request-first operator inspection, and a pointer-only close-out walkthrough.
- [x] M007: Operator Decision Clarity — Clarified page identity, evidence hierarchy, and operator decision workflow across Observability, request detail, and policy preview without drifting into dashboard sprawl or a broad redesign.
- [x] M008: Evidence Governance and Privacy Controls — Made Nebula’s evidence layer tenant-governed, retention-aware, historically explainable, visibly bounded, and assembled into one end-to-end reviewable proof without widening into payload capture, compliance-platform sprawl, or hosted authority.
- [ ] M009: Outcome-Grounded Routing Quality — Improve live routing decisions using bounded recent tenant-scoped outcome evidence, preserve runtime/replay parity, and expose request-level route factors on existing operator surfaces without drifting into analytics, black-box optimization, or hosted decision authority. Current progress: S01-S02 complete; S03-S05 remain open.