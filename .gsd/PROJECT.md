# Project

## What This Is

Nebula is a self-hosted semantic AI gateway for teams that want to reduce premium LLM spend without losing control over routing behavior, fallback handling, or operator-visible evidence. v1.0 and v2.0 are complete. v3.x established Nebula’s bounded public adoption path and hosted metadata-only trust story. v4.x strengthened Nebula’s operator control plane through simulation, guardrails, recommendation-grade feedback, calibrated routing, operator-surface clarity, governed evidence retention, and now outcome-grounded routing quality. M009 focused on improving the routing core itself using bounded recent tenant-scoped outcome evidence while preserving explainability, replay credibility, request-first operator inspection, and local authority.

## Core Value

A team can point real application traffic at Nebula and get lower-cost, more reliable model routing decisions that remain interpretable, replayable, and operator-controlled rather than opaque or hosted-authoritative.

## Current State

Nebula ships a FastAPI gateway, a Next.js operator console, PostgreSQL-backed governance, Qdrant-backed semantic cache, public chat completions and embeddings routes, policy simulation, hard budget guardrails, bounded recommendation surfaces, calibrated routing evidence, request-first Observability, tenant-governed evidence retention, and a metadata-only hosted boundary. M001 through M009 are complete.

In M009, S01 locked the shared backend outcome-evidence contract through deterministic tenant-scoped GovernanceStore summarization, explicit `sufficient`/`thin`/`stale`/`degraded` state semantics, and replay/admin-safe typed artifacts and tests. S02 wired that contract into live route choice and request persistence so runtime routing can change because of recent tenant-scoped evidence and correlated usage-ledger rows persist exact outcome-grounded factors plus additive score components. S03 brought admin replay onto the same contract by injecting one tenant-window evidence summary into the shared policy evaluation path, preserving unchanged-policy route parity where evidence is available and surfacing degraded replay honestly when persisted route signals are incomplete. S04 aligned operator surfaces to that vocabulary so the selected request row remains authoritative while calibration context stays supporting. S05 closed the milestone with integrated proof and anti-drift coverage: `docs/m009-integrated-proof.md` now provides the pointer-first happy/degraded review path, shared documentation links expose the vocabulary without redefining contracts, backend tests prove public request -> persisted route evidence -> unchanged-policy replay parity and honest degraded replay handling, and console tests prove degraded inspection remains selected-request-first rather than widening into a new analytics workflow.

## Architecture / Key Patterns

Nebula routes `POST /v1/chat/completions` traffic across local, cache, premium, and fallback paths and persists operator-visible usage outcomes in a governance ledger. The backend is FastAPI with typed Pydantic models and service-container dependency injection. The console is a Next.js App Router operator UI that proxies same-origin admin traffic to backend APIs and keeps request evidence primary on Observability surfaces. Control-plane work prefers typed evidence contracts, bounded additive scoring, deterministic replay, request-first operator proof, and pointer-only integrated proof docs over duplicated contracts, dashboard sprawl, hidden optimization, or hosted decision authority.

For M009 specifically, `GovernanceStore.summarize_calibration_evidence()` is the authoritative seam for tenant-scoped outcome-evidence classification in both live and replay-oriented flows; the compatibility field name `calibration_summary` remains the shared serialized carrier for the richer state vocabulary; replay and runtime share `PolicyService.evaluate()` semantics by passing evidence explicitly rather than forking logic; request-level route diagnostics are extended additively so headers, ledger rows, replay outputs, and operator reads stay correlatable; and integrated proof docs remain pointer-first, linking existing runtime, ledger, simulation, and request-detail seams rather than duplicating contracts inline.

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
- [x] M009: Outcome-Grounded Routing Quality — Improved live routing decisions using bounded recent tenant-scoped outcome evidence, preserved runtime/replay parity, exposed request-level route factors on existing operator surfaces, and closed the milestone with a pointer-first integrated proof plus anti-drift tests for both happy and degraded review paths without drifting into analytics, black-box optimization, or hosted decision authority.
