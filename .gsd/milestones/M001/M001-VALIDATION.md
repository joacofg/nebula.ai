---
verdict: needs-attention
remediation_round: 0
---

# Milestone Validation: M001

## Success Criteria Checklist
- [x] A developer can integrate a common chat-completions use case with Nebula using the documented happy path in under 30 minutes — evidence: S02 established the canonical quickstart and production model, and S05 assembled the integrated adoption proof across `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, and `docs/integrated-adoption-proof.md`, with R003 marked validated.
- [x] Nebula exposes a stable and clearly bounded OpenAI-compatible inference path for the most common chat-completions app flows — evidence: S01 delivered the canonical `POST /v1/chat/completions` contract, explicit unsupported/deferred boundary, and focused contract/header tests; R001, R002, and R010 are validated.
- [x] The product documentation makes it obvious where compatibility ends and where Nebula-specific value begins — evidence: S01 locked the canonical adoption contract boundary, S02 preserved that composition rule in quickstart/production docs, and S04 added `docs/day-1-value.md` to show Nebula-native value without widening compatibility claims.
- [x] At least one realistic reference integration proves an app can call Nebula instead of a provider directly with minimal code changes — evidence: S03 added `tests/test_reference_migration.py` and `docs/reference-migration.md`, proving an OpenAI-style caller can switch via base URL plus `X-Nebula-API-Key` with optional tenant header only for ambiguous multi-tenant keys; R004 and R008 are validated.
- [x] The tenant / app / workload / operator model is explicit enough that teams know how to structure production usage — evidence: S02 established the runtime-truth framing in `docs/production-model.md`, including tenant/policy/API key/operator boundaries and the explicit note that app/workload remain conceptual in M001; R006 is validated.
- [x] The adoption story is credible for startup product teams, platform teams, and enterprise/self-hosted operators — evidence: S02 explicitly targeted those audiences in the canonical documentation set, and R007 is validated.
- [x] Routing, policy, observability, and provider abstraction value are visible immediately during adoption, not buried behind later setup — evidence: S04 connected public headers, `X-Request-ID`, usage ledger, Playground, and Observability into one day-1 proof path, while S05 preserved that ordering in the final integrated proof; R005 and R009 are validated.

## Slice Delivery Audit
| Slice | Claimed | Delivered | Status |
|-------|---------|-----------|--------|
| S01 | Clearly bounded adoption API contract and compatibility boundary | Summary substantiates canonical public contract, request-boundary validation, focused tests, admin Playground non-equivalence, and canonical docs in `docs/adoption-api-contract.md` | pass |
| S02 | Happy-path quickstart and production model so teams can integrate without guessing | Summary substantiates canonical `docs/quickstart.md` and `docs/production-model.md`, entry-doc cross-links, runtime-truth language, and composition rules; executable reruns were blocked by missing local tooling | pass |
| S03 | Realistic reference migration with minimal code changes and working proof | Summary substantiates executable proof in `tests/test_reference_migration.py`, canonical migration guide, request/ledger correlation, and passing focused pytest evidence | pass |
| S04 | Day-1 value proof surface showing routing, policy, observability, and provider abstraction immediately | Summary substantiates `docs/day-1-value.md`, strengthened console proof surfaces, and aligned test coverage; local execution was blocked by missing pytest/vitest/playwright toolchains | pass |
| S05 | Final integrated adoption proof tying docs, migration path, live proof flow, and operator evidence together | Summary substantiates `docs/integrated-adoption-proof.md`, final doc cross-links, backend/console proof alignment, and closure of the missing Observability test seam; remaining blocked checks are environment/unrelated-worktree issues | pass |

## Cross-Slice Integration
Boundary-map integration is consistent with what the slices actually produced:

- **S01 → S02 / S03 / S04**: S01 produced the bounded public contract, auth/header rules, and supported/unsupported behavior that S02 reused compositionally, S03 targeted for migration proof, and S04 used to distinguish compatibility from Nebula-native value.
- **S02 → S03 / S05**: S02 produced the canonical quickstart and production-model framing that S03 explicitly followed in the migration guide and that S05 composed into the final integrated walkthrough.
- **S03 → S04 / S05**: S03 produced the public-request + `X-Request-ID` + ledger-correlation seam that S04 turned into a day-1 value surface and that S05 preserved as the backbone of the integrated proof.
- **S04 → S05**: S04 produced the operator corroboration pattern (Playground immediate metadata, ledger persistence, Observability explanation/dependency health) that S05 reused without re-scoping the proof.

No material produce/consume mismatches were found.

One non-blocking integration caveat remains: several slice summaries record that fresh executable reruns in this worktree were partially blocked by missing Python/console runners or an unrelated console compile error, so final integration evidence is strong but not fully re-executed green inside this exact validation environment.

## Requirement Coverage
All roadmap-covered active requirements are addressed by at least one delivered slice and are recorded as validated in `.gsd/REQUIREMENTS.md`:

- R001, R002, R010 → S01
- R003, R006, R007 → S02 with S03/S05 support for R003
- R004, R008 → S03
- R005, R009 → S04 with S05 support

No unaddressed active requirements were found.

Partial-coverage requirements remain correctly deferred rather than missing:
- R011 and R012 are intentionally left for later milestones, matching the roadmap.

## Verdict Rationale
Verdict: **needs-attention**.

M001's planned slices are delivered, their summaries substantiate the roadmap claims, the cross-slice integration story is coherent, and the roadmap-covered active requirements are all addressed with recorded validation evidence. That is enough to avoid remediation.

However, the milestone definition of done and proof strategy both emphasize re-checking success criteria against live behavior, not just artifacts. Multiple slice summaries record that some verification reruns in this worktree were blocked by environment/tooling gaps (`pytest`, `vitest`, `playwright`) or by an unrelated existing console compile error outside the slice scope. Those blockers do not indicate product regressions, but they do leave the milestone with residual attention items before a fully clean seal in this exact environment.

Because the gaps are environmental/non-product and no roadmap deliverable is missing, remediation slices are not warranted. The milestone is functionally complete but should carry an explicit note that blocked verification commands still need rerun in a provisioned or cleaned worktree.

## Remediation Plan
None. No new remediation slices are required for round 0.

Follow-up attention items outside roadmap remediation:
- rerun the blocked Python suites in a worktree with `pytest` provisioned
- rerun the blocked console Playwright flow after the unrelated `console/src/components/deployments/remote-action-card.tsx` compile error is cleared
- preserve the distinction between product regression and environment/worktree blockers when sealing milestone status
