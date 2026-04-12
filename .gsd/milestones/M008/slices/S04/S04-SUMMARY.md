---
id: S04
parent: M008
milestone: M008
provides:
  - A shared operator vocabulary for retained, suppressed, deleted, and not-hosted evidence states that downstream S05 can reuse in the integrated governance proof.
  - Verified policy/request-detail/hosted seams that now tell one bounded evidence-governance story without introducing new APIs or dashboards.
requires:
  []
affects:
  - S05
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/lib/hosted-contract.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/hosted/trust-boundary-card.tsx
  - console/src/app/trust-boundary/page.tsx
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Reused one schema-backed hosted-contract module as the shared source for retained/suppressed/deleted/not-hosted evidence vocabulary and hosted raw-ledger exclusion wording across policy, request detail, and hosted trust-boundary surfaces.
  - Kept the selected persisted ledger row authoritative while it exists and described deletion truthfully as full row removal at expiration rather than soft-delete, archive recovery, or hosted substitution.
patterns_established:
  - Keep evidence-governance wording centralized in `console/src/lib/hosted-contract.ts` and reuse it across local and hosted surfaces to prevent drift.
  - Treat the selected persisted ledger row as the authoritative request-level evidence seam while it exists; tenant-wide or hosted summaries are supporting context, not substitutes.
  - Use focused positive and negative copy assertions to prevent UI trust-boundary regressions such as soft-delete recovery claims, hosted raw-ledger export claims, or hosted runtime-authority drift.
observability_surfaces:
  - Policy editor effective evidence-boundary panel in `console/src/components/policy/policy-form.tsx`.
  - Request-detail effective evidence-boundary panel in `console/src/components/ledger/ledger-request-detail.tsx`.
  - Hosted trust-boundary card/page shared evidence-vocabulary sections in `console/src/components/hosted/trust-boundary-card.tsx` and `console/src/app/trust-boundary/page.tsx`.
  - Focused Vitest and hosted-contract regression suites as wording-drift failure signals.
drill_down_paths:
  - .gsd/milestones/M008/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008/slices/S04/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-12T17:20:54.932Z
blocker_discovered: false
---

# S04: Operator evidence-boundary surfaces

**S04 made Nebula’s effective evidence boundary explicit across policy, request-detail, and hosted trust-boundary surfaces using one shared retained/suppressed/deleted/not-hosted vocabulary.**

## What Happened

S04 completed the operator-facing evidence-governance story by aligning three existing seams around one bounded vocabulary instead of adding a new governance dashboard. On the policy page, Nebula now synthesizes an explicit effective evidence boundary from the runtime-enforced `evidence_retention_window` and `metadata_minimization_level` controls, explaining how long governed metadata remains inspectable, what strict minimization suppresses at write time, and that hosted export still excludes raw usage-ledger rows. On request detail, the selected persisted ledger row remains the authoritative request-level evidence while it exists, and the UI now states plainly what retained, suppressed, deleted, and not-hosted mean using the row’s persisted governance markers, without implying soft-delete recovery, archive lookup, or hosted raw export. On hosted surfaces, the public trust-boundary card and page now reuse the same shared evidence vocabulary and keep the metadata-only contract visibly aligned with local operator evidence language. The slice’s main implementation pattern was to centralize that vocabulary in `console/src/lib/hosted-contract.ts`, making hosted trust-boundary wording schema-backed and shared rather than duplicated. This gives S05 a coherent operator-readable chain from policy choice to persisted row truth to hosted boundary guardrail, while preserving M008’s scope constraint against compliance-platform sprawl, analytics drift, or hosted runtime authority.

## Verification

All slice-plan verification passed. Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` (17/17 passing), `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` (36/36 passing), and `./.venv/bin/pytest tests/test_hosted_contract.py` (11/11 passing). I also confirmed the slice observability surfaces exist in the assembled worktree by reviewing `console/src/components/policy/policy-form.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/hosted/trust-boundary-card.tsx`, and `console/src/app/trust-boundary/page.tsx`: policy now derives an explicit evidence-boundary summary from retention/minimization controls, request detail explains retained/suppressed/deleted/not-hosted states from persisted row-level markers, and hosted trust surfaces reuse the same shared metadata-only vocabulary. This gives immediate failure visibility through focused Vitest assertions and hosted-contract regression instead of latent wording drift.

## Requirements Advanced

- R060 — Validated operator inspection of the effective evidence boundary on the policy and request-detail surfaces through shared copy and focused tests.
- R061 — Validated that hosted trust-boundary wording stays metadata-only and visibly consistent with the new evidence vocabulary.
- R062 — Materially advanced the end-to-end governance proof by aligning policy, request-detail, and hosted trust seams around one bounded story.
- R063 — Strengthened operator trust by making retained vs suppressed vs deleted evidence legible while preserving the request-led debugging model.
- R064 — Preserved milestone scope discipline by reusing existing surfaces and rejecting dashboard/compliance/hosted-authority drift.

## Requirements Validated

- R060 — Passing focused console verification (`policy-form.test.tsx`, `policy-page.test.tsx`, `ledger-request-detail.test.tsx`) proves operators can inspect the effective evidence boundary on policy and request-detail surfaces.
- R061 — Passing hosted trust-boundary Vitest suites plus `./.venv/bin/pytest tests/test_hosted_contract.py` proves hosted export remains metadata-only and wording stays aligned with the shared evidence contract.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Expanded verification slightly beyond the minimum listed commands by also reading the shared hosted-contract module and recording the new vocabulary pattern in KNOWLEDGE.md, because the shared copy contract is now the main drift-prevention seam for this slice. No product-scope deviation.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx` — Added effective evidence-boundary guidance derived from retention/minimization controls and reused shared hosted metadata-only exclusion copy.
- `console/src/components/policy/policy-form.test.tsx` — Locked policy-side evidence-boundary wording, strict-minimization behavior, and runtime-enforced vs advisory framing.
- `console/src/components/policy/policy-page.test.tsx` — Verified policy page still presents the new boundary vocabulary without drifting into a dashboard or advisory-only framing.
- `console/src/lib/hosted-contract.ts` — Centralized shared hosted metadata-only contract and retained/suppressed/deleted/not-hosted evidence vocabulary.
- `console/src/components/ledger/ledger-request-detail.tsx` — Added an effective evidence boundary panel that explains row-level retained, suppressed, deleted, and not-hosted semantics from persisted governance markers.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Locked request-detail evidence-boundary wording and guardrails against soft-delete recovery or hosted raw-export implications.
- `console/src/components/hosted/trust-boundary-card.tsx` — Reused the shared evidence vocabulary on the hosted trust-boundary card while preserving metadata-only posture.
- `console/src/components/hosted/trust-boundary-card.test.tsx` — Verified hosted trust card copy stays aligned to the shared contract and excludes hosted authority drift.
- `console/src/app/trust-boundary/page.tsx` — Reinforced the public hosted trust-boundary page with the same shared evidence vocabulary and guardrails.
- `console/src/app/trust-boundary/page.test.tsx` — Locked public trust-boundary copy against raw-ledger export and runtime-authority drift.
- `console/src/lib/hosted-contract.test.ts` — Added contract-level tests for shared hosted evidence vocabulary and wording guardrails.
- `.gsd/DECISIONS.md` — Recorded the slice-level copy-alignment decision.
- `.gsd/KNOWLEDGE.md` — Captured the shared evidence vocabulary pattern for future slices.
- `.gsd/PROJECT.md` — Refreshed project state to mark S04 complete and describe the new operator evidence-boundary surfaces.
