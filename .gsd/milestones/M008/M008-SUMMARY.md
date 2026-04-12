---
id: M008
title: "Evidence Governance and Privacy Controls"
status: complete
completed_at: 2026-04-12T17:35:53.623Z
key_decisions:
  - D045 — Keep evidence governance as typed runtime-enforced tenant policy fields plus per-row governance markers on the existing usage ledger, rendered through existing policy and request-detail surfaces rather than raw payload capture or a separate governance product.
  - D046 — Keep evidence aging on the existing usage-ledger seam by adding explicit GovernanceStore cleanup keyed by persisted evidence_expires_at and treating request detail as authoritative only while the row exists.
  - D047 — Operationalize governed evidence deletion as a small background lifecycle service wired into startup/health/observability seams rather than adding a retention-specific endpoint or dashboard.
  - D048 — Centralize retained/suppressed/deleted/not-hosted evidence vocabulary and hosted raw-export exclusion copy in a shared console hosted-contract module reused across policy, request-detail, and hosted trust-boundary surfaces.
  - D049 — Close M008 with a pointer-only integrated walkthrough in docs/m008-integrated-proof.md, preserving the strict proof order policy/options → persisted request row/request detail → deletion plus supporting retention health → hosted metadata-only boundary.
key_files:
  - src/nebula/services/governance_store.py
  - src/nebula/services/retention_lifecycle_service.py
  - src/nebula/services/runtime_health_service.py
  - src/nebula/services/heartbeat_service.py
  - src/nebula/core/config.py
  - src/nebula/core/container.py
  - src/nebula/main.py
  - console/src/components/policy/policy-form.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/health/runtime-health-cards.tsx
  - console/src/components/hosted/trust-boundary-card.tsx
  - console/src/lib/admin-api.ts
  - console/src/lib/hosted-contract.ts
  - docs/m008-integrated-proof.md
  - docs/architecture.md
  - README.md
  - tests/test_governance_api.py
  - tests/test_retention_lifecycle_service.py
  - tests/test_health.py
  - tests/test_hosted_contract.py
lessons_learned:
  - Bounded governance work is safest when write-time policy enforcement, persisted historical markers, and later lifecycle behavior are separated into explicit seams rather than recomputed ad hoc across routes and UI surfaces.
  - For privacy/evidence features, the existing operator read seams (`/v1/admin/usage/ledger`, request detail, runtime health) can usually carry proof more credibly than new specialized dashboards or endpoints.
  - Historical explainability stays truthful only when deletion eligibility follows persisted row markers rather than current tenant policy; cleanup semantics should never silently rewrite the past.
  - Shared UI vocabulary modules are valuable whenever multiple local and hosted surfaces must stay aligned to one trust boundary without copy drift.
---

# M008: Evidence Governance and Privacy Controls

**Nebula’s evidence layer is now tenant-governed, retention-aware, historically explainable, and visibly bounded end to end without widening into payload capture, compliance-platform sprawl, or hosted authority.**

## What Happened

M008 closed Nebula’s bounded evidence-governance story across five completed slices. S01 introduced typed tenant policy controls for evidence retention and metadata minimization, centralized governed write-time enforcement in GovernanceStore.record_usage(), and persisted request-time governance markers on usage-ledger rows for both chat and embeddings. S02 added real deletion semantics through GovernanceStore.delete_expired_usage_records(now=...), proving that cleanup follows persisted evidence_expires_at markers rather than current-policy inference and that request detail remains authoritative only while the row exists. S03 operationalized deletion as a running retention lifecycle service wired into app startup and runtime health, exposing truthful bounded diagnostics through existing readiness, dependency, heartbeat, and observability seams. S04 aligned operator and hosted trust-boundary wording around one retained/suppressed/deleted/not-hosted evidence vocabulary, making the effective local evidence boundary legible in policy and request-detail surfaces while preserving the hosted metadata-only contract. S05 assembled the final pointer-only integrated proof in docs/m008-integrated-proof.md, linked it from README.md and docs/architecture.md, and reverified the joined backend and console seams so the canonical review path is policy/options → persisted request row/request detail → deletion by persisted evidence_expires_at with supporting retention_lifecycle health → hosted metadata-only boundary. Milestone verification confirmed non-.gsd code changes exist, all slices and task summaries are complete, the acceptance criteria are met with passing slice-level and milestone validation evidence, and the assembled work remains bounded to request/policy/evidence governance rather than expanding into a broader privacy or compliance platform.

## Success Criteria Results

- ✅ **Tenant policy exposes explicit evidence-retention and metadata-minimization controls as typed enforced fields.** S01 added explicit `evidence_retention_window` and `metadata_minimization_level` fields to the tenant-policy contract, exposed them through backend/admin and console policy surfaces, and verified them with passing targeted pytest and Vitest coverage recorded in S01 and M008 validation.
- ✅ **Governed requests persist only the allowed metadata shape and record governance markers needed for later historical explanation.** S01 centralized governed write-time enforcement in `GovernanceStore.record_usage()` for chat and embeddings and persisted row markers such as `evidence_expires_at`, `metadata_fields_suppressed`, and `governance_source`; S02 reverified surviving-row visibility through `/v1/admin/usage/ledger` and request-detail coverage.
- ✅ **Retention windows cause real deletion of expired evidence.** S02 added `GovernanceStore.delete_expired_usage_records(now=...)` and proved expired rows disappear from `/v1/admin/usage/ledger`; S03 operationalized cleanup as `RetentionLifecycleService` and verified runtime health/heartbeat observability around real deletion.
- ✅ **Policy and request-detail surfaces clearly show the effective evidence boundary without replacing request-led proof with dashboard framing.** S04 added shared retained/suppressed/deleted/not-hosted vocabulary across policy and request-detail surfaces, while S05 verified request evidence remains primary and runtime health stays supporting context.
- ✅ **Hosted metadata-only contract remains aligned and explicitly bounded after governance changes.** S01, S03, S04, and S05 all reverified the hosted metadata-only boundary; hosted surfaces reuse the shared evidence vocabulary while excluding raw payload/ledger authority claims.
- ✅ **One integrated proof path demonstrates policy → persistence → request inspection → retention deletion → hosted-boundary consistency.** S05 assembled `docs/m008-integrated-proof.md` in the required proof order, added discoverability links in `README.md` and `docs/architecture.md`, and passed focused backend/console verification covering ledger, retention lifecycle, health, and hosted seams.

## Definition of Done Results

- ✅ **All roadmap slices are complete.** `gsd_milestone_status` reports S01–S05 all `complete`, with every slice showing all tasks done.
- ✅ **All slice summaries exist.** Filesystem verification found all five slice summaries at `.gsd/milestones/M008/slices/S01` through `S05` and all ten task summaries under their `tasks/` directories.
- ✅ **Milestone produced real code changes outside `.gsd/`.** `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` returned successfully with no empty-tree failure, and the assembled worktree contains milestone artifacts in backend, console, docs, and tests including `src/nebula/services/governance_store.py`, `src/nebula/services/retention_lifecycle_service.py`, `src/nebula/services/runtime_health_service.py`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/health/runtime-health-cards.tsx`, `console/src/lib/hosted-contract.ts`, `docs/m008-integrated-proof.md`, `README.md`, and `docs/architecture.md`.
- ✅ **Cross-slice integrations work correctly.** Milestone validation confirms S01→S02 marker handoff, S01+S02→S03 operational cleanup, S03→S04 operator-legibility alignment, and S04→S05 integrated-proof vocabulary/ordering are all honored. No cross-slice mismatches were identified.
- ✅ **Horizontal checklist coverage.** The roadmap/validation artifacts contain no separate unchecked horizontal-checklist items; verification found no omitted checklist obligations.

## Requirement Outcomes

- **R056 — validated (confirmed).** Evidence from S01 shows typed retention policy fields and persisted expiration markers were implemented and verified by passing targeted backend and console checks.
- **R057 — validated (confirmed).** Evidence from S01 shows metadata minimization is explicitly tenant-governed, enforced at write time, and rendered through existing operator surfaces without widening into raw payload capture.
- **R058 — validated (confirmed).** Evidence from S02 shows persisted row-level governance markers remain inspectable while the row exists and cleanup uses persisted `evidence_expires_at` rather than current-policy inference.
- **R059 — validated (confirmed).** Evidence from S03 shows retention is enforced as real deletion by a running lifecycle service with readiness/dependency/heartbeat diagnostics, not as UI-only hiding.
- **R060 — validated (confirmed).** Evidence from S04 shows policy and request-detail surfaces render the effective evidence boundary clearly via shared retained/suppressed/deleted semantics.
- **R061 — validated (confirmed).** Evidence from S04 and S05 shows hosted trust-boundary surfaces remain metadata-only while staying visibly aligned with local evidence-governance vocabulary.
- **R062 — validated (confirmed).** Evidence from S05 shows the integrated pointer-only proof and focused verification cover the full governance chain from tenant policy through operator evidence surfaces to hosted trust-boundary consistency.
- **R063 — validated (confirmed).** Evidence from S05 shows request-led debugging remains primary while governance improves operator trust through explicit deletion semantics and bounded supporting runtime health context.
- **R064 — validated (status changed from active to validated).** Milestone validation and slice summaries show M008 stayed bounded to request/policy/evidence governance throughout, reusing existing policy, ledger, health, and hosted seams instead of expanding into a compliance platform, analytics product, or hosted authority layer.

## Deviations

Most milestone work stayed within the roadmap boundaries. The notable execution deviation was that several slices finished by tightening and verifying partially pre-existing workspace changes rather than implementing every surface from scratch; close-out therefore emphasized verification-driven hardening, integrated proof assembly, and operator-wording alignment rather than greenfield feature breadth.

## Follow-ups

Future milestones can revisit broader privacy/compliance workflows only if product evidence justifies them. Specifically deferred areas include automated policy workflows or approvals (R065), configurable raw prompt/response capture (R066), and broader fleet- or deployment-wide inheritance of evidence governance beyond tenant-scoped controls (R067). If retention execution needs richer operations later, build on the existing lifecycle/health seams rather than adding a parallel governance subsystem.
