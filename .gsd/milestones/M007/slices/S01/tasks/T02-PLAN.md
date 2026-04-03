---
estimated_steps: 3
estimated_files: 4
skills_used:
  - react-best-practices
  - frontend-design
---

# T02: Lock request-detail authority and policy-role guardrails

**Slice:** S01 — Define page roles and evidence boundaries
**Milestone:** M007

## Description

Preserve `LedgerRequestDetail` as the authoritative persisted evidence surface and add guardrails that later M007 slices must preserve: interpretation stays secondary, policy preview stays preview-before-save, and no new analytics/dashboard drift appears in these bounded surfaces.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `UsageLedgerRecord` and optional calibration evidence rendered by `console/src/components/ledger/ledger-request-detail.tsx` | Keep the existing neutral empty state and evidence-first layout; do not patch over missing data with speculative summaries. | N/A for direct component rendering, but tests should keep null-entry behavior explicit. | Preserve `N/A` / explicit fallback handling instead of widening interpretation. |
| Policy simulation preview state rendered by `console/src/components/policy/policy-form.tsx` and `console/src/components/policy/policy-page.tsx` tests | Keep preview error and zero-result states explicitly non-saving and bounded. | Preserve existing pending/preview sequencing; do not add alternate workflows. | Keep changed-request samples and replay notes bounded to decision review rather than analytics commentary. |

## Load Profile

- **Shared resources**: Admin evidence components reused across request investigation and policy decision flows.
- **Per-operation cost**: Static component render plus focused Vitest assertions; no new network calls or data joins.
- **10x breakpoint**: Contract drift in wording and section emphasis, not throughput; the risk is later slices adding interpretation that overshadows persisted evidence.

## Negative Tests

- **Malformed inputs**: Null request detail, absent optional fields, and zero-row policy preview states must remain explicit without invented analytics copy.
- **Error paths**: Preview error messaging must remain clearly non-saving; request detail must not imply authority from supporting interpretation when evidence is partial.
- **Boundary conditions**: Dashboard, routing-studio, or analytics-product terms should remain absent from the bounded request-detail and preview seams.

## Steps

1. Review `console/src/components/ledger/ledger-request-detail.tsx` and tighten wording or ordering only if needed to keep persisted evidence primary and interpretation secondary.
2. Extend `console/src/components/ledger/ledger-request-detail.test.tsx` with assertions that request fields remain authoritative and supporting explanations stay bounded.
3. Add or harden role-boundary assertions in `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` so preview-before-save remains explicit and analytics/dashboard drift is rejected.

## Must-Haves

- [ ] Request detail still leads with persisted request fields and keeps calibration, budget, and routing explanations supplementary.
- [ ] Policy preview remains explicitly non-saving until the operator chooses save.
- [ ] Focused tests reject dashboard, routing-studio, or analytics-product framing on these bounded surfaces.

## Verification

- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
- `rg -n "Preview before save|Save remains explicit|Request detail|Calibration evidence|Routing inspection" console/src/components/ledger/ledger-request-detail.tsx console/src/components/policy/policy-form.tsx`

## Observability Impact

- Signals added/changed: Authority and boundary semantics are encoded in focused component tests rather than left as informal copy intent.
- How a future agent inspects this: Run the request-detail and policy-focused Vitest files and inspect the bounded wording in the component sources.
- Failure state exposed: Regressions surface as failing assertions when supporting interpretation overtakes persisted evidence or when preview copy drifts toward analytics/dashboard framing.

## Inputs

- `console/src/components/ledger/ledger-request-detail.tsx` — Current authoritative evidence surface that needs explicit guardrails preserved.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Baseline evidence-boundary tests to extend.
- `console/src/components/policy/policy-form.test.tsx` — Preview-before-save contract tests for the form seam.
- `console/src/components/policy/policy-page.test.tsx` — Route-level preview contract tests that should stay aligned with the form.

## Expected Output

- `console/src/components/ledger/ledger-request-detail.tsx` — Authority wording and ordering kept explicitly evidence-first if any adjustment is needed.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Stronger request-detail authority assertions.
- `console/src/components/policy/policy-form.test.tsx` — Hardened preview-before-save boundary assertions.
- `console/src/components/policy/policy-page.test.tsx` — Page-level preview contract guardrails against analytics/dashboard drift.
