---
id: T02
parent: S01
milestone: M002
provides:
  - Operator-only framing for Playground and Observability so console evidence surfaces match the admin contract and persisted-ledger model.
key_files:
  - console/src/app/(console)/playground/page.tsx
  - console/src/components/playground/playground-form.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/components/playground/playground-form.test.tsx
  - console/src/components/playground/playground-page.test.tsx
  - console/src/app/(console)/observability/page.test.tsx
key_decisions:
  - Preserved the existing immediate-response versus recorded-ledger split and changed only operator framing copy plus tests, because the admin Playground contract already enforces non-streaming and selected tenant context.
patterns_established:
  - When a console surface explains operator evidence, anchor the wording to the concrete admin route contract and lock the trust boundary with focused vitest assertions.
observability_surfaces:
  - Focused vitest assertions for Playground and Observability copy; existing request id, route metadata, recorded ledger rows, and dependency-health cards remain the diagnostic anchors.
duration: 28m
verification_result: passed
completed_at: 2026-03-23T21:00:00-03:00
blocker_discovered: false
---

# T02: Reframe Playground and Observability as operator evidence surfaces

**Reframed Playground and Observability so operators see admin-session corroboration in Playground and persisted request evidence plus dependency-health context in Observability.**

## What Happened

I first verified `src/nebula/api/routes/admin.py` to confirm the local truth boundary before touching copy. That route is admin-only via `require_admin`, resolves an explicit playground tenant context, and rejects `stream=true`, so the implementation work stayed narrowly focused on wording and tests rather than adding any new behavior.

On `console/src/app/(console)/playground/page.tsx`, I changed the page header from a generic routing sandbox to an operator corroboration surface. The updated copy now says the active admin session runs a non-streaming corroboration request for the tenant chosen in the page, and explicitly says this is not the public `POST /v1/chat/completions` integration boundary.

On `console/src/components/playground/playground-form.tsx`, I rewrote the form intro so the operator is told to choose tenant context on purpose and send one admin-session prompt through the non-streaming playground path. I also preserved and clarified the immediate-response-versus-recorded-ledger split by changing the footer guidance: the first response remains immediate and limited to completion content plus request id, and the recorded ledger evidence appears only after Nebula persists the outcome for that same request.

On `console/src/app/(console)/observability/page.tsx`, I reframed the page around persisted request evidence instead of a generic usage screen. The usage-ledger section now describes itself as the persisted explanation surface for recorded outcomes, and the dependency-health section now explicitly says those states are supporting runtime context rather than a replacement for the ledger record.

I then extended `console/src/components/playground/playground-form.test.tsx` and `console/src/components/playground/playground-page.test.tsx` to lock the new operator-only, selected-tenant, non-streaming, and non-public-boundary wording. I also added the missing `console/src/app/(console)/observability/page.test.tsx` to lock the persisted-ledger and dependency-health-context framing called for by the slice plan.

## Verification

I ran the task-level focused Vitest suite for Playground and Observability through an async job. The Playground form and page specs passed, confirming the operator/admin framing and the preserved immediate-versus-recorded evidence distinction. The shell environment in this worktree was inconsistent for subsequent direct `npm --prefix console run test` invocations: the same script sometimes failed before execution with `sh: vitest: command not found`, even though `console/package.json` correctly declares `vitest` and the earlier async job successfully executed it.

Because of that environment inconsistency, I treated the successful async test run as the authoritative automated verification signal, and I manually reviewed the three updated UI files to confirm the final wording stays inside the real admin-only and non-streaming boundaries defined by the backend route contract.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx src/app/'(console)'/observability/page.test.tsx` | 0 | ✅ pass | 2.3s |
| 2 | `npm --prefix console run test -- --run "src/app/(console)/observability/page.test.tsx"` | 127 | ❌ fail | 0.00s (shell reported `vitest: command not found` before test execution) |
| 3 | `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx && npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx && npm --prefix console run test -- --run src/app/\(console\)/observability/page.test.tsx` | 127 | ❌ fail | 0.00s (same shell-path inconsistency; script failed before running Vitest) |
| 4 | Manual review — `console/src/app/(console)/playground/page.tsx`, `console/src/components/playground/playground-form.tsx`, and `console/src/app/(console)/observability/page.tsx` | 0 | ✅ pass | 0.00s |

## Diagnostics

Inspect `src/nebula/api/routes/admin.py` to confirm the source-of-truth constraints: admin-only access, explicit playground tenant resolution, and non-streaming enforcement. Then compare that contract with the operator copy in `console/src/app/(console)/playground/page.tsx` and `console/src/components/playground/playground-form.tsx`. For Observability, read `console/src/app/(console)/observability/page.tsx` and confirm the ledger remains the persisted request-outcome surface while dependency health is only supporting runtime context. Future wording drift should surface in `console/src/components/playground/playground-form.test.tsx`, `console/src/components/playground/playground-page.test.tsx`, and `console/src/app/(console)/observability/page.test.tsx`.

## Deviations

None in the shipped feature. The only execution deviation was verification-related: the direct shell environment for some `npm --prefix console run test` invocations could not resolve `vitest`, so I relied on the passing async-runner evidence plus manual review instead of trying to patch tooling during a copy-focused task.

## Known Issues

- Direct shell execution of some console test commands in this worktree is inconsistent and may fail with `sh: vitest: command not found` even though the package script and local dependency are present and the same test command can succeed through the async runner.

## Files Created/Modified

- `console/src/app/(console)/playground/page.tsx` — reframed Playground as an admin-session corroboration surface rather than a generic sandbox or public integration path.
- `console/src/components/playground/playground-form.tsx` — clarified selected-tenant, operator-only, non-streaming guidance and preserved the immediate-versus-recorded evidence split.
- `console/src/app/(console)/observability/page.tsx` — reframed Observability around persisted request evidence and dependency-health context.
- `console/src/components/playground/playground-form.test.tsx` — added assertions for operator-only, tenant-selected, non-streaming Playground guidance.
- `console/src/components/playground/playground-page.test.tsx` — added assertions that Playground is not the public integration boundary while keeping the existing response-versus-ledger distinction covered.
- `console/src/app/(console)/observability/page.test.tsx` — added the missing focused test for persisted ledger evidence and dependency-health context wording.
