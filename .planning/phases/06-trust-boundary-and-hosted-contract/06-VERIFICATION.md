---
phase: 06-trust-boundary-and-hosted-contract
verified: 2026-03-21T12:53:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 6: Trust Boundary and Hosted Contract Verification Report

**Phase Goal:** Operators can understand and trust the hybrid hosted/self-hosted boundary before any deployment is linked.
**Verified:** 2026-03-21T12:53:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Operators and downstream phases can inspect a published machine-readable default-export contract for hosted metadata. | VERIFIED | `docs/hosted-default-export.schema.json` exists with 158 lines, title `HostedDeploymentMetadata`, 12 properties, and all sub-model definitions. Backed by `src/nebula/models/hosted_contract.py` Pydantic model. |
| 2 | The contract explicitly excludes raw prompts, responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state. | VERIFIED | `HOSTED_EXCLUDED_DATA_CLASSES` tuple in `hosted_contract.py:34-41` contains all 6 items exactly. Test `test_hosted_contract_excludes_sensitive_runtime_data` locks this. |
| 3 | Hosted freshness uses only connected, degraded, stale, and offline values. | VERIFIED | `FreshnessStatus = Literal["connected", "degraded", "stale", "offline"]` at line 26. JSON schema `freshness_status.enum` matches. Test `test_freshness_status_has_exactly_four_values` guards this. |
| 4 | An operator can open a public trust-boundary page before authenticating. | VERIFIED | `console/src/app/trust-boundary/page.tsx` exists as a public route outside the `(console)` auth group. E2E spec `trust-boundary.spec.ts` asserts reachability without auth. |
| 5 | The hosted UI states that hosted freshness is not local runtime authority. | VERIFIED | `trust-boundary-card.tsx` renders `copy.freshnessWarning` which is exactly `"Hosted freshness is not local runtime authority."`. Unit test and E2E spec both assert this string. |
| 6 | The UI lists the metadata exported by default and the data excluded by default. | VERIFIED | `TrustBoundaryCard` renders all 12 exported field labels from schema-backed content and all 6 excluded items. Unit tests assert all labels and excluded items are present. |
| 7 | The repo narrative says Nebula is self-hosted with an optional hosted control plane. | VERIFIED | `README.md` line 13: `"Nebula is self-hosted with an optional hosted control plane."` |
| 8 | Architecture and self-hosting docs list exactly what leaves the environment by default. | VERIFIED | `docs/architecture.md` lines 102-107 list core invariants and all 6 excluded data classes. `docs/self-hosting.md` line 113 has `Outbound-only hosted linking` section with same exclusion list. Both reference `hosted-default-export.schema.json`. |
| 9 | Docs explicitly say the hosted control plane is not in the serving path and not authoritative for local runtime enforcement. | VERIFIED | `docs/architecture.md` line 102: `"Nebula's hosted control plane is not in the request-serving path."` Line 103: `"Local runtime enforcement remains authoritative."` |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/nebula/models/hosted_contract.py` | Canonical hosted export models, exclusion list, and freshness enum | VERIFIED | 91 lines. Contains `HostedDeploymentMetadata`, `FreshnessStatus`, `HOSTED_EXCLUDED_DATA_CLASSES`, sub-models. Exported from `__init__.py`. |
| `tests/test_hosted_contract.py` | Schema drift and exclusion guards | VERIFIED | 162 lines, 10 tests, all passing. Contains `test_hosted_contract_excludes_sensitive_runtime_data`. |
| `docs/hosted-default-export.schema.json` | Committed JSON schema artifact | VERIFIED | 158 lines. Title `HostedDeploymentMetadata`. Contains `freshness_status` and `remote_action_summary`. Test locks sync with Pydantic model. |
| `console/src/lib/hosted-contract.ts` | Schema-backed content module | VERIFIED | 136 lines. Contains `getHostedContractContent`, imports `hosted-default-export.schema.json`, parity checks for freshness and field coverage. |
| `console/src/components/hosted/trust-boundary-card.tsx` | Reusable disclosure component | VERIFIED | 63 lines. Renders "What this deployment shares", all exported fields, excluded items, freshness states, and warning copy. |
| `console/src/app/trust-boundary/page.tsx` | Public trust-boundary route | VERIFIED | 33 lines. Renders `TrustBoundaryCard`, "recommended for pilots" intro, "Metadata-only by default" via card. |
| `console/e2e/trust-boundary.spec.ts` | Browser regression coverage | VERIFIED | 47 lines. 2 E2E specs covering public access and login-page link navigation. |
| `console/src/components/auth/login-page-client.tsx` | Pre-auth disclosure link | VERIFIED | Contains `href="/trust-boundary"` and `"Review hosted trust boundary"` link text. |
| `README.md` | Self-hosted-first product framing | VERIFIED | Contains `"optional hosted control plane"` and references `docs/hosted-default-export.schema.json`. |
| `docs/architecture.md` | Hybrid-boundary architecture narrative | VERIFIED | Contains all core invariants, exclusion list, and `"derived from docs/hosted-default-export.schema.json"`. |
| `docs/self-hosting.md` | Self-hosting runbook with hosted disclosure | VERIFIED | Contains `"Outbound-only hosted linking"` section and references schema artifact. |
| `docs/demo-script.md` | Demo narrative with hosted story | VERIFIED | Contains `"recommended for pilots"` and `"metadata-only"`. |
| `docs/pilot-checklist.md` | Pilot prep with trust boundary | VERIFIED | Contains exact excluded-by-default list and `"Do not improvise a hosted onboarding story"`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_hosted_contract.py` | `src/nebula/models/hosted_contract.py` | Pydantic model import and schema assertions | WIRED | Line 15-21: imports `HostedDeploymentMetadata`, `HOSTED_EXCLUDED_DATA_CLASSES`, all sub-models. 10 tests exercise them. |
| `docs/hosted-default-export.schema.json` | `src/nebula/models/hosted_contract.py` | model_json_schema output | WIRED | Test `test_committed_schema_artifact_matches_model` asserts `committed == generated`. Contains `freshness_status` and `remote_action_summary`. |
| `console/src/app/trust-boundary/page.tsx` | `console/src/lib/hosted-contract.ts` | shared contract content import | WIRED | Card component imports and calls `getHostedContractContent()`. |
| `console/src/lib/hosted-contract.ts` | `docs/hosted-default-export.schema.json` | schema-backed parity mapping | WIRED | Line 9: `import schemaJson from "../../../docs/hosted-default-export.schema.json"`. Parity checks on fields and freshness enum. |
| `console/src/components/auth/login-page-client.tsx` | `/trust-boundary` | pre-auth disclosure link | WIRED | `href="/trust-boundary"` with text `"Review hosted trust boundary"`. |
| `README.md` | `docs/hosted-default-export.schema.json` | explicit reference | WIRED | Two references linking to the schema artifact. |
| `README.md` | `docs/architecture.md` | documentation map | WIRED | README references architecture doc; both use `"optional hosted control plane"`. |
| `docs/self-hosting.md` | `docs/architecture.md` | shared authority language | WIRED | Both use metadata-only framing and reference the schema artifact. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| TRST-01 | 06-02, 06-03 | Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative. | SATISFIED | Trust-boundary page, card component, architecture docs, and demo/pilot docs all state the hosted plane is metadata-only and not authoritative for local runtime enforcement. |
| TRST-02 | 06-01, 06-03 | Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state. | SATISFIED | `HOSTED_EXCLUDED_DATA_CLASSES` tuple, JSON schema artifact, 10 backend regression tests, UI content module with 6 excluded items, architecture and self-hosting docs with exact exclusion lists. |

No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | No TODOs, FIXMEs, placeholders, empty implementations, or stub patterns found in any phase artifact. |

### Human Verification Required

### 1. Visual Trust Boundary Page

**Test:** Open `/trust-boundary` in a browser without logging in.
**Expected:** A clean, compact disclosure page showing the 12 exported metadata fields, 6 excluded data classes, 4 freshness states with descriptions, and the amber warning box about hosted freshness not being local authority.
**Why human:** Visual layout, spacing, and readability cannot be verified programmatically.

### 2. Login Page Link Visibility

**Test:** Open `/` (login page) and look for the "Review hosted trust boundary" link.
**Expected:** The link is visible, clickable, and navigates to `/trust-boundary` without requiring authentication.
**Why human:** Link prominence and visual hierarchy relative to the login form need human judgment.

### Gaps Summary

No gaps found. All 9 observable truths are verified. All artifacts exist, are substantive, and are properly wired. Both requirements (TRST-01, TRST-02) are satisfied. Backend tests (10 pytest) and console tests (20 vitest) all pass. No anti-patterns detected.

---

_Verified: 2026-03-21T12:53:00Z_
_Verifier: Claude (gsd-verifier)_
