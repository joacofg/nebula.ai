---
estimated_steps: 4
estimated_files: 4
skills_used:
  - react-best-practices
---

# T01: Publish the canonical day-1 value proof path

**Slice:** S04 — Day-1 value proof surface
**Milestone:** M001

## Description

Create the single canonical document that explains Nebula's day-1 value after a successful adoption request. The task must reuse the S03 migration proof pattern instead of inventing a parallel story: public `POST /v1/chat/completions` first, `X-Nebula-*` plus `X-Request-ID` second, then Playground/usage-ledger/Observability as operator corroboration. The touched entry docs should link to this new artifact, but they must not duplicate S01 contract semantics or S02 setup guidance.

## Steps

1. Write `docs/day-1-value.md` as the canonical S04 artifact that explains the day-1 proof sequence from public request headers to persisted operator evidence and dependency-health validation.
2. Link the new artifact from `docs/quickstart.md` at the point where the first request is confirmed and from `docs/reference-migration.md` where the migration proof transitions into operator-visible value.
3. Add one concise README link/path so repository entrypoints expose the new day-1 value proof without duplicating detailed contract or setup content.
4. Review the touched docs for boundary discipline: public adoption path remains `POST /v1/chat/completions`, Playground stays admin-only corroboration, and Observability stays the persisted explanation surface.

## Must-Haves

- [ ] `docs/day-1-value.md` explicitly ties together public `X-Nebula-*` headers, `X-Request-ID`, usage-ledger correlation, Playground immediate evidence, and Observability dependency-health context.
- [ ] `README.md`, `docs/quickstart.md`, and `docs/reference-migration.md` link to the new artifact in a way that preserves the existing canonical roles of `docs/adoption-api-contract.md`, `docs/quickstart.md`, and `docs/reference-migration.md`.

## Verification

- `test -f docs/day-1-value.md`
- `rg -n "day-1 value|X-Request-ID|Playground|Observability|route reason|policy" README.md docs/day-1-value.md docs/quickstart.md docs/reference-migration.md`

## Inputs

- `docs/quickstart.md` — current first-request and operator-confirmation flow that the new value-proof doc must extend.
- `docs/reference-migration.md` — canonical S03 migration proof that must remain the public request baseline.
- `README.md` — repository entrypoint that needs one stable link to the S04 artifact.
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — slice-level goal, scope, and verification expectations for this task.

## Expected Output

- `docs/day-1-value.md` — new canonical day-1 value proof walkthrough for adopters and operators.
- `docs/quickstart.md` — linked handoff from first-request confirmation to the day-1 value proof.
- `docs/reference-migration.md` — linked handoff from migration proof to day-1 operator-visible value.
- `README.md` — updated documentation map/entrypoint link to the new day-1 value proof.

## Observability Impact

- Signals clarified: the documentation now names the exact public proof signals (`X-Nebula-*` headers plus `X-Request-ID`) and the operator corroboration surfaces (Playground, usage ledger, Observability dependency health) that future tasks must keep aligned.
- Inspection path for future agents: start from `docs/day-1-value.md`, then confirm the linked public and operator evidence against `docs/quickstart.md`, `docs/reference-migration.md`, and the slice verification grep that checks `day-1 value`, `X-Request-ID`, `Playground`, `Observability`, `route reason`, and `policy` references.
- Failure state made visible: if docs drift, agents can detect it through missing or inconsistent references to request correlation, route reason, policy outcome, Playground's admin-only role, or Observability's dependency-health framing.
