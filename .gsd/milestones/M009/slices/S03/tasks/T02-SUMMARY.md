---
id: T02
parent: S03
milestone: M009
key_files:
  - tests/test_governance_api.py
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.test.tsx
key_decisions:
  - Split admin replay verification into unchanged-policy parity assertions and changed-policy drift assertions so route-score/mode parity and degraded replay honesty can be proven independently.
  - Keep the console contract additive by extending the existing `calibration_summary.state` union with `degraded` instead of introducing a new preview-only evidence field.
duration: 
verification_result: passed
completed_at: 2026-04-27T21:09:54.936Z
blocker_discovered: false
---

# T02: Proved admin replay parity with non-mutating API coverage and aligned console preview types with degraded evidence state.

**Proved admin replay parity with non-mutating API coverage and aligned console preview types with degraded evidence state.**

## What Happened

Extended `tests/test_governance_api.py` to close the public replay boundary with a two-pass simulation check. The updated coverage now first replays the same tenant traffic class under an unchanged candidate policy to prove outcome-grounded route target/reason/mode/score parity against live runtime for calibrated rows, while still surfacing honest degraded behavior for rows whose persisted route signals were suppressed. The same test then runs a changed-policy replay to preserve the existing premium-only drift assertions without conflating them with parity semantics. I also made the test explicitly assert that simulation leaves the saved tenant policy untouched and introduces no provider execution side effects by snapshotting provider call counts before and after replay. On the console side, I updated `console/src/lib/admin-api.ts` so `CalibrationEvidenceSummary.state` accepts `"degraded"`, then added a focused policy-form regression test proving degraded replay evidence can flow through the preview without crashing or hiding routing/policy clues.

## Verification

Ran the focused backend replay command `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)"`, which passed and exercised the tightened admin replay semantics. Ran the focused console command `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`, which passed and confirmed the request-first preview remains stable when degraded calibration evidence is present.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)"` | 0 | ✅ pass | 850ms |
| 2 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx` | 0 | ✅ pass | 1690ms |

## Deviations

Adjusted the existing broad admin simulation test into a two-pass structure instead of adding a brand-new separate test file. This kept the verification localized while separating unchanged-policy parity guarantees from changed-policy drift assertions.

## Known Issues

None.

## Files Created/Modified

- `tests/test_governance_api.py`
- `console/src/lib/admin-api.ts`
- `console/src/components/policy/policy-form.test.tsx`
