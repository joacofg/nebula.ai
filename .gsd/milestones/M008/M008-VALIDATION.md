---
verdict: pass
remediation_round: 0
---

# Milestone Validation: M008

## Success Criteria Checklist
# Milestone Validation: M008

## Reviewer C — Assessment & Acceptance Criteria
[✓] tenant policy exposes explicit evidence-retention and metadata-minimization controls as typed enforced fields | **Evidence:** `M008-CONTEXT.md` defines this criterion. `S01-SUMMARY.md` says S01 “turned evidence retention and metadata minimization into typed, runtime-enforced tenant policy,” added explicit `evidence_retention_window` and `metadata_minimization_level`, exposed them through backend governance contract and console policy form, and verified `/v1/admin/policy/options` classifies them as runtime-enforced.

[✓] governed requests persist only the allowed metadata shape and record governance markers needed for later historical explanation | **Evidence:** `S01-SUMMARY.md` says governed persistence is centralized in `GovernanceStore.record_usage()` for chat and embeddings, with per-row governance markers including `message_type`, `evidence_expires_at`, `metadata_fields_suppressed`, and `governance_source`; verification covers chat and embeddings ledger tests plus request-detail rendering. `S02-SUMMARY.md` further confirms surviving rows still expose persisted governance markers via `/v1/admin/usage/ledger`.

[✓] retention windows cause real deletion of expired evidence | **Evidence:** `S02-SUMMARY.md` states `GovernanceStore.delete_expired_usage_records(now=...)` deletes rows whose persisted `evidence_expires_at` is at or before cutoff, proves expired rows disappear from `/v1/admin/usage/ledger`, and confirms idempotent cleanup. `S03-SUMMARY.md` strengthens this with a running `RetentionLifecycleService` that performs real deletion by persisted expiration markers and exposes health state.

[✓] policy and request-detail surfaces clearly show the effective evidence boundary without replacing request-led proof with dashboard framing | **Evidence:** `S04-SUMMARY.md` states policy and request-detail surfaces now use a shared retained/suppressed/deleted/not-hosted vocabulary, with policy deriving the effective boundary from runtime-enforced controls and request detail keeping the selected persisted row authoritative while it exists. `S05-SUMMARY.md` adds regression assertions that selected request evidence stays ahead of supporting runtime-health context.

[✓] hosted metadata-only contract remains aligned and explicitly bounded after governance changes | **Evidence:** `S01-SUMMARY.md` says hosted metadata-only boundary was reverified unchanged. `S03-SUMMARY.md` says hosted heartbeat export remains coarse healthy/degraded/unavailable membership only. `S04-SUMMARY.md` says hosted trust-boundary surfaces reuse the same shared evidence vocabulary and passing hosted-contract tests prove wording stays metadata-only. `S05-SUMMARY.md` reiterates hosted trust-boundary wording remains aligned and non-authoritative.

[✓] one integrated proof path demonstrates policy → persistence → request inspection → retention deletion → hosted-boundary consistency | **Evidence:** `S05-SUMMARY.md` explicitly says it “closed M008 with a canonical integrated governance proof” in `docs/m008-integrated-proof.md`, assembled in pointer-only order: policy/options → usage-ledger row and request detail → deletion by persisted `evidence_expires_at` → retention_lifecycle health as supporting context → hosted metadata-only boundary. It also reports passing focused backend and console verification for ledger, retention lifecycle, health, and hosted seams.

**Verdict: PASS**

## Slice Delivery Audit
## Reviewer A — Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| R056 — Tenant policy can explicitly govern evidence retention windows for persisted request evidence. | COVERED | **S01-SUMMARY.md**: “typed, runtime-enforced tenant policy” with explicit `evidence_retention_window`; governed persistence in `GovernanceStore.record_usage()`; “Requirements Validated” explicitly says R056 was proven with targeted backend verification and persisted expiration markers. **S03-SUMMARY.md** reinforces runtime retention lifecycle enforcement using persisted `evidence_expires_at`. |
| R057 — Tenant policy can explicitly govern metadata minimization for persisted request evidence without widening into raw payload capture. | COVERED | **S01-SUMMARY.md**: explicit `metadata_minimization_level`, governed suppression of non-essential metadata, and repeated statement that raw prompt/response capture remains out of scope. “Requirements Validated” explicitly marks R057 proven by backend + console verification. |
| R058 — Request evidence remains historically explainable after policy changes by persisting governance markers on each ledger row. | COVERED | **S01-SUMMARY.md** establishes per-row governance markers as the historical truth source. **S02-SUMMARY.md** explicitly validates R058: surviving rows retain write-time markers; cleanup uses persisted `evidence_expires_at` rather than current policy; request detail explains disappearance after cleanup instead of implying recovery. |
| R059 — Retention policy is enforced as real evidence deletion, not UI-only hiding. | COVERED | **S02-SUMMARY.md** adds `delete_expired_usage_records(now=...)` and proves expired rows disappear from `/v1/admin/usage/ledger`. **S03-SUMMARY.md** explicitly validates R059 by operationalizing cleanup as a running lifecycle service wired into app startup/shutdown and showing actual row deletion plus runtime-health reporting. |
| R060 — Operators can inspect the effective evidence boundary in the policy surface and the request-detail evidence surface. | COVERED | **S01-SUMMARY.md** says policy and request-detail surfaces already expose governed controls and row markers. **S04-SUMMARY.md** explicitly validates R060: policy derives an effective evidence boundary from retention/minimization controls, and request detail explains retained/suppressed/deleted semantics from persisted governance markers. |
| R061 — Hosted export remains metadata-only by default and M008 makes any tenant-governed evidence boundary visibly consistent with that contract. | COVERED | **S01-SUMMARY.md** says the hosted metadata-only boundary was preserved while governance became runtime-enforced locally. **S04-SUMMARY.md** explicitly validates R061: hosted trust-boundary surfaces reuse shared retained/suppressed/deleted/not-hosted vocabulary while excluding raw ledger rows and runtime-authority claims. **S05-SUMMARY.md** keeps hosted trust-boundary wording aligned in the integrated proof. |
| R062 — M008 proves the full governance chain end to end: tenant policy → persistence/export behavior → operator evidence surface → hosted trust boundary. | COVERED | **S01-SUMMARY.md** advances tenant policy → governed persistence. **S02-SUMMARY.md** advances persistence → deletion/read-path truth. **S03-SUMMARY.md** adds operational lifecycle + health. **S04-SUMMARY.md** aligns policy/request-detail/hosted vocabulary. **S05-SUMMARY.md** explicitly validates R062 with `docs/m008-integrated-proof.md`, README/architecture discoverability, and focused backend/console verification. |
| R063 — Evidence governance improves operator trust without weakening Nebula’s request-led debugging and interpretable evidence model. | COVERED | **S02-SUMMARY.md** says surviving rows remain historically explainable while rows exist and deletion semantics are made explicit. **S04-SUMMARY.md** says the selected persisted ledger row remains authoritative while shared vocabulary makes retained/suppressed/deleted/not-hosted legible. **S05-SUMMARY.md** explicitly validates R063 by keeping request-led evidence primary, runtime health secondary, and hosted surfaces metadata-only. |
| R064 — M008 stays bounded to request/policy/evidence governance and does not expand into a compliance platform, analytics product, or hosted authority layer. | COVERED | **S01-SUMMARY.md** explicitly advances and validates R064 by reusing existing policy and request-detail seams instead of adding a governance subsystem. **S02-SUMMARY.md** says no new backend route was added and rejects archive/recovery/hosted export drift. **S03-SUMMARY.md** keeps proof on existing health/ledger seams. **S04-SUMMARY.md** explicitly advances and validates R064 by avoiding a governance dashboard. **S05-SUMMARY.md** explicitly validates R064 via the pointer-only integrated proof and regression coverage rejecting compliance-platform / hosted-authority drift. |

**Verdict: PASS**

## Cross-Slice Integration
## Reviewer B — Cross-Slice Integration

No explicit boundary map block was present in the roadmap file, so the integration audit used the producer/consumer contracts recorded in the slice summaries.

| Boundary | Producer Summary | Consumer Summary | Status |
|---|---|---|---|
| S01 → S02: typed evidence-governance policy fields and per-row governance markers | **Confirmed.** `S01-SUMMARY.md` provides typed tenant-policy fields, a shared governed persistence seam, and per-row governance markers including `evidence_expires_at` and suppression markers. | **Confirmed.** `S02-SUMMARY.md` explicitly requires S01’s typed policy fields and write-time markers, then uses persisted row markers as the basis for historical explainability and cleanup behavior. | HONORED |
| S01 + S02 → S03: persisted expiration markers plus explicit deletion seam | **Confirmed.** `S01-SUMMARY.md` establishes `evidence_expires_at`; `S02-SUMMARY.md` adds `delete_expired_usage_records(now=...)` and proves deletion through the ledger seam. | **Confirmed.** `S03-SUMMARY.md` explicitly requires S01 and S02, and operationalizes cleanup via `RetentionLifecycleService` calling the governed deletion seam while preserving persisted-marker semantics. | HONORED |
| S03 → S04: retention/deletion truth must be operator-legible without new surfaces | **Confirmed.** `S03-SUMMARY.md` provides a running retention lifecycle, runtime-health diagnostics, and a bounded observability proof path on existing seams. | **Confirmed.** `S04-SUMMARY.md` reuses existing policy, request-detail, and hosted surfaces to explain retained/suppressed/deleted/not-hosted states without adding a new dashboard, matching S03’s bounded-surface model. | HONORED |
| S04 → S05: shared evidence vocabulary and hosted-boundary wording for integrated proof | **Confirmed.** `S04-SUMMARY.md` provides a shared retained/suppressed/deleted/not-hosted vocabulary and verified policy/request-detail/hosted seams telling one bounded story. | **Confirmed.** `S05-SUMMARY.md` explicitly requires S04 and says the integrated proof keeps hosted trust-boundary wording aligned while treating request evidence as primary and hosted surfaces as supporting metadata-only context. | HONORED |
| S01–S04 → S05: end-to-end close-out proof | **Confirmed.** S01 provides tenant-governed policy + markers; S02 provides persisted-row governance truth and deletion by `evidence_expires_at`; S03 provides lifecycle execution + health context; S04 provides shared vocabulary and hosted trust-boundary surfaces. | **Confirmed.** `S05-SUMMARY.md` explicitly requires all four prior slices and assembles them in pointer-only order in `docs/m008-integrated-proof.md`: policy/options → request row + detail → deletion by persisted expiration → supporting retention health → hosted metadata-only boundary. | HONORED |

**Verdict: PASS**

## Requirement Coverage
## Reviewer A — Requirements Coverage

All milestone requirements R056–R064 are covered by passing slice summary evidence, with explicit validations recorded for the key runtime-enforcement, retention, operator-surface, hosted-boundary, and anti-sprawl requirements. No partial or missing requirement evidence was identified.

## Verification Class Compliance
- **Contract:** S01, S04, and S05 summaries report passing backend/admin and hosted-contract verification for typed governance policy, governed ledger row shape, request markers, and hosted metadata-only alignment.
- **Integration:** S01–S05 collectively prove tenant policy → write-time persistence → request-detail read path → deletion by persisted expiration → integrated proof ordering, with S05 explicitly assembling the end-to-end chain.
- **Operational:** S02 proves callable deletion by persisted `evidence_expires_at`; S03 operationalizes it as a running lifecycle with health diagnostics and validates real deletion behavior rather than visibility-only hiding.
- **UAT:** S04 and S05 demonstrate that operators can inspect effective evidence boundaries on policy and request-detail surfaces, understand retained/suppressed/deleted/not-hosted states, and see hosted trust-boundary alignment without replacing request-led evidence with a dashboard.


## Verdict Rationale
All three independent review tracks passed. Requirements coverage is complete across R056–R064, producer/consumer contracts across slices are honored, and every milestone acceptance criterion is supported by clear slice-summary evidence despite the absence of separate assessment artifacts.
