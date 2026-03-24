---
estimated_steps: 4
estimated_files: 2
skills_used:
  - react-best-practices
  - best-practices
---

# T01: Lock shared hosted reinforcement guardrails in the canonical content module

**Slice:** S01 — Hosted reinforcement boundary
**Milestone:** M004

## Description

Extend the existing schema-backed `console/src/lib/hosted-contract.ts` module so it becomes the single source of truth for hosted reinforcement vocabulary, explicit non-authority guardrails, and bounded-action phrasing hooks. This task should strengthen the contract without widening the hosted metadata export or introducing a parallel wording module.

## Steps

1. Inspect the current exports in `console/src/lib/hosted-contract.ts` and add structured reinforcement content for allowed descriptive framing, prohibited authority implications, and operator-reading guidance while preserving the schema-backed exported-field behavior.
2. Keep the new content clearly scoped to metadata-backed hosted reinforcement: it may describe fleet posture, freshness meaning, onboarding, and bounded action availability, but it must not imply authority over serving-time health, routing, fallback, or policy enforcement.
3. Update `console/src/lib/hosted-contract.test.ts` to lock the new exports, phrases, and boundary semantics alongside the existing schema parity and excluded-data checks.
4. Confirm the module still fails fast on schema drift and now also fails fast on reinforcement-vocabulary drift.

## Must-Haves

- [ ] `console/src/lib/hosted-contract.ts` remains the canonical wording seam; do not create a second deployments-specific constants file for the same trust-boundary semantics.
- [ ] The new shared exports explicitly distinguish allowed hosted descriptive claims from authority claims that downstream UI must avoid.
- [ ] No backend contract widening is introduced; the task only hardens wording and shared frontend contract shape.

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts`
- `pytest tests/test_hosted_contract.py -q`

## Inputs

- `console/src/lib/hosted-contract.ts` — existing shared hosted trust-boundary copy and schema-backed exported-field logic
- `console/src/lib/hosted-contract.test.ts` — current focused tests for schema parity and trust-boundary copy
- `docs/hosted-default-export.schema.json` — canonical hosted metadata export schema consumed by the frontend module
- `tests/test_hosted_contract.py` — backend contract guard that must remain aligned with the metadata-only export

## Expected Output

- `console/src/lib/hosted-contract.ts` — extended shared reinforcement vocabulary and guardrail exports
- `console/src/lib/hosted-contract.test.ts` — focused tests locking the new shared guardrails and wording

## Observability Impact

- Signals changed: focused Vitest failures now surface drift in hosted reinforcement vocabulary, allowed descriptive framing, prohibited authority claims, and operator-reading guidance in addition to schema parity.
- Inspection surfaces: future agents should inspect `console/src/lib/hosted-contract.ts` for the canonical exports and `console/src/lib/hosted-contract.test.ts` for the exact locked phrases and guardrail assertions.
- Failure visibility: copy drift becomes visible as exact string or array assertion failures, while schema drift continues to fail fast through the shared contract helper.
