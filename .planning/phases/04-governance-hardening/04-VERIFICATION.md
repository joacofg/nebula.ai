---
phase: 04-governance-hardening
verified: 2026-03-17T03:13:30Z
status: human_needed
score: 10/10 must-haves verified
human_verification:
  - test: "Denied-path explanation clarity"
    expected: "A denied premium-model request and a fallback-blocked local-provider failure are both understandable from the API response plus the correlated usage-ledger row."
    why_human: "Automated tests prove headers, details, and ledger persistence, but not whether the combined explanation is semantically clear to an operator."
  - test: "Policy screen governance wording review"
    expected: "Every visible control on the policy screen reads as runtime-enforced, soft-signal, or deferred exactly as intended, with no misleading operator interpretation."
    why_human: "Playwright and component tests prove DOM content and save flow, but not final human judgment on policy wording clarity."
---

# Phase 4: Governance Hardening Verification Report

**Phase Goal:** Policy controls and runtime behavior are aligned well enough for real B2B internal use.
**Verified:** 2026-03-17T03:13:30Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | The policy contract distinguishes runtime-enforced, soft-signal, and advisory settings. | ✓ VERIFIED | [governance.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/models/governance.py#L102), [admin.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/admin.py#L108), [test_governance_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_api.py#L128) |
| 2 | Runtime policy changes alter routing, allowlists, cache, fallback, and hard spend guardrails, while soft budget stays non-blocking metadata. | ✓ VERIFIED | [policy_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/policy_service.py#L40), [test_governance_runtime_hardening.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_runtime_hardening.py#L63), [test_service_flows.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_service_flows.py#L348) |
| 3 | Invalid credentials, inactive tenants, and forbidden routing choices return stable status/detail pairs. | ✓ VERIFIED | [auth_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/auth_service.py#L25), [test_governance_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_api.py#L24), [test_admin_playground_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_admin_playground_api.py#L128) |
| 4 | Denied requests and fallback-blocked provider failures carry `X-Nebula-*` metadata. | ✓ VERIFIED | [policy_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/policy_service.py#L173), [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L174), [test_response_headers.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_response_headers.py#L160) |
| 5 | Usage-ledger rows retain route reason and policy outcome for denied and provider-error paths. | ✓ VERIFIED | [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L801), [test_governance_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_api.py#L374), [test_service_flows.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_service_flows.py#L272) |
| 6 | The operator policy screen shows only runtime-enforced controls as editable governance controls. | ✓ VERIFIED | [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L126), [policy-form.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.test.tsx#L66), [policy.spec.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/e2e/policy.spec.ts#L72) |
| 7 | `soft_budget_usd` is presented as a soft signal, not a runtime-enforced control. | ✓ VERIFIED | [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L227), [policy-page.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-page.test.tsx#L47), [policy.spec.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/e2e/policy.spec.ts#L75) |
| 8 | Prompt/response capture flags are removed from the editable Phase 4 policy surface while save flow is preserved. | ✓ VERIFIED | [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L83), [policy-advanced-section.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-advanced-section.tsx#L1), [policy.spec.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/e2e/policy.spec.ts#L81) |
| 9 | The console uses backend-authored policy metadata instead of a separate frontend truth table. | ✓ VERIFIED | [admin-api.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/lib/admin-api.ts#L56), [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L62), [admin.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/admin.py#L108) |
| 10 | Browser and component coverage fail if the Phase 4 policy wording drifts from the backend contract. | ✓ VERIFIED | [policy-form.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.test.tsx#L66), [policy-page.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-page.test.tsx#L8), [policy.spec.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/e2e/policy.spec.ts#L37) |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/nebula/models/governance.py` | Policy-options field buckets | ✓ VERIFIED | Declares `runtime_enforced_fields`, `soft_signal_fields`, `advisory_fields` in [governance.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/models/governance.py#L102) and is imported by [admin.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/admin.py#L10). |
| `src/nebula/services/policy_service.py` | Runtime enforcement and denial metadata | ✓ VERIFIED | Enforces routing/allowlist/guardrail rules and emits denial headers in [policy_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/policy_service.py#L40). |
| `tests/test_governance_runtime_hardening.py` | Requirement-level routing/policy matrix | ✓ VERIFIED | Covers routing modes, explicit-model denials, guardrails, and soft-budget behavior in [test_governance_runtime_hardening.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_runtime_hardening.py#L63). |
| `src/nebula/services/auth_service.py` | Stable auth and inactive-tenant detail strings | ✓ VERIFIED | Exact 401/403 details are centralized in [auth_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/auth_service.py#L25). |
| `src/nebula/services/chat_service.py` | Denied/provider-error ledger retention and fallback-blocked 502s | ✓ VERIFIED | Records denial metadata from exception headers and emits blocked-fallback 502 headers in [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L174) and [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L801). |
| `tests/test_response_headers.py` | Header coverage for denied and fallback-blocked paths | ✓ VERIFIED | Asserts `X-Nebula-*` metadata on denied and blocked-fallback responses in [test_response_headers.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_response_headers.py#L160). |
| `tests/test_admin_playground_api.py` | Inactive admin-playground behavior | ✓ VERIFIED | Confirms exact inactive-tenant detail and no successful ledger record in [test_admin_playground_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_admin_playground_api.py#L128). |
| `console/src/lib/admin-api.ts` | Typed console policy-options contract | ✓ VERIFIED | Mirrors backend field buckets in [admin-api.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/lib/admin-api.ts#L56). |
| `console/src/components/policy/policy-form.tsx` | Runtime-only policy surface driven by metadata | ✓ VERIFIED | Renders runtime section from `runtime_enforced_fields` and soft-budget separately in [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L126). |
| `console/src/components/policy/policy-advanced-section.tsx` | Deferred capture-copy only | ✓ VERIFIED | Contains non-editable deferred copy in [policy-advanced-section.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-advanced-section.tsx#L1). |
| `console/src/components/policy/policy-form.test.tsx` | Runtime section assertions | ✓ VERIFIED | Covers runtime grouping and soft-budget placement in [policy-form.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.test.tsx#L66). |
| `console/src/components/policy/policy-page.test.tsx` | Capture-setting removal assertions | ✓ VERIFIED | Verifies deferred copy and hidden capture controls in [policy-page.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-page.test.tsx#L8). |
| `console/e2e/policy.spec.ts` | Browser contract alignment and save flow | ✓ VERIFIED | Proves wording and successful save flow in [policy.spec.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/e2e/policy.spec.ts#L37). |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/nebula/api/routes/admin.py` | `src/nebula/models/governance.py` | `PolicyOptionsResponse` returned by `/v1/admin/policy/options` | ✓ WIRED | Route instantiates the model with exact field buckets in [admin.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/admin.py#L108). |
| `src/nebula/services/policy_service.py` | `tests/test_governance_runtime_hardening.py` | routing-mode, allowlist, cache, fallback, and spend-guardrail assertions | ✓ WIRED | Runtime branches in [policy_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/policy_service.py#L40) are asserted in [test_governance_runtime_hardening.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_runtime_hardening.py#L63). |
| `src/nebula/services/policy_service.py` | `src/nebula/services/chat_service.py` | `HTTPException.headers` carrying denial metadata into ledger recording | ✓ WIRED | `_policy_denied` sets `X-Nebula-*` headers in [policy_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/policy_service.py#L173), and `_resolve_policy` persists them in [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L801). |
| `src/nebula/services/chat_service.py` | `src/nebula/api/routes/chat.py` | route-level responses preserving metadata on 403 and 502 paths | ✓ WIRED | Chat route uses `_nebula_headers` for success/stream responses in [chat.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/chat.py#L17), while FastAPI forwards `HTTPException.headers` from [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L208). |
| `src/nebula/api/routes/admin.py` | `tests/test_admin_playground_api.py` | admin-playground requests using the same metadata/error contract | ✓ WIRED | Playground route delegates to `chat_service.create_completion_with_metadata` in [admin.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/admin.py#L175), covered by [test_admin_playground_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_admin_playground_api.py#L128). |
| `console/src/lib/admin-api.ts` | `console/src/components/policy/policy-form.tsx` | typed `PolicyOptionsResponse` fields deciding editable vs soft-signal controls | ✓ WIRED | `PolicyForm` derives visible sections from `options.runtime_enforced_fields` and `options.soft_signal_fields` in [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L62). |
| `console/src/components/policy/policy-form.tsx` | `console/src/components/policy/policy-advanced-section.tsx` | UI grouping separating runtime controls from deferred capture copy | ✓ WIRED | `PolicyForm` renders `PolicyAdvancedSection` after runtime/soft-signal sections in [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L253). |
| `console/src/components/policy/policy-page.test.tsx` | `console/e2e/policy.spec.ts` | component and browser assertions sharing contract wording | ✓ WIRED | Both assert the exact deferred and soft-budget strings in [policy-page.test.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-page.test.tsx#L41) and [policy.spec.ts](/Users/joaquinfernandezdegamboa/Proj/nebula/console/e2e/policy.spec.ts#L75). |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| GOV-01 | 04-01, 04-03 | Tenant policy changes affect runtime behavior for routing mode, fallback enablement, semantic-cache enablement, and premium-model allowlists | ✓ SATISFIED | Backend enforcement and tests in [policy_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/policy_service.py#L40), [test_governance_runtime_hardening.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_runtime_hardening.py#L63), and UI contract alignment in [policy-form.tsx](/Users/joaquinfernandezdegamboa/Proj/nebula/console/src/components/policy/policy-form.tsx#L126). |
| GOV-02 | 04-02 | Admin and tenant operations return clear error states for invalid credentials, inactive tenants, and disallowed routing choices | ✓ SATISFIED | Exact detail strings are centralized in [auth_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/auth_service.py#L25) and asserted in [test_governance_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_api.py#L53) and [test_admin_playground_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_admin_playground_api.py#L147). |
| ROUT-01 | 04-02 | Nebula records enough metadata per request to explain why a route was chosen and whether a fallback occurred | ✓ SATISFIED | Route metadata is emitted in [chat.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/chat.py#L51), denial/provider metadata is recorded in [chat_service.py](/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/chat_service.py#L801), and header/ledger correlation is asserted in [test_response_headers.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_response_headers.py#L160) and [test_governance_api.py](/Users/joaquinfernandezdegamboa/Proj/nebula/tests/test_governance_api.py#L374). |

No orphaned Phase 4 requirements were found in [.planning/REQUIREMENTS.md](/Users/joaquinfernandezdegamboa/Proj/nebula/.planning/REQUIREMENTS.md#L81); the only Phase 4 IDs mapped there are `GOV-01`, `GOV-02`, and `ROUT-01`, and all are claimed by phase plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| None | - | No TODO/FIXME/placeholder or empty stub patterns detected in the phase files scanned | ℹ️ Info | No automated red flags found in the implemented Phase 4 artifacts |

### Human Verification Required

### 1. Denied-path explanation clarity

**Test:** Trigger a denied premium-model request and a local-provider failure with fallback disabled, then compare the API response with the correlated usage-ledger row.
**Expected:** An operator can understand both why the request was denied and why fallback did not occur without ambiguous or conflicting wording.
**Why human:** Tests prove exact strings and metadata are present, but not whether the combined explanation is easy for a human operator to interpret.

### 2. Policy screen governance wording review

**Test:** Open the console policy screen, inspect the runtime section, soft-budget section, and deferred capture copy, then save a policy update.
**Expected:** The screen reads as runtime-enforced vs soft-signal vs deferred without implying hidden runtime behavior, and the save flow still feels coherent.
**Why human:** DOM and Playwright assertions prove string presence and save mechanics, but not final UX clarity or operator interpretation.

### Gaps Summary

No automated gaps were found. All phase must-haves verified in code and tests; remaining work is human semantic review only.

---

_Verified: 2026-03-17T03:13:30Z_
_Verifier: Claude (gsd-verifier)_
