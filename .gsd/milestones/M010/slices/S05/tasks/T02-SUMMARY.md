---
id: T02
parent: S05
milestone: M010
key_files:
  - README.md
  - docs/architecture.md
  - docs/m010-recovery-proof.md
key_decisions:
  - Added pointer-first discoverability links for `docs/m010-integrated-proof.md` from the repository documentation map and architecture proof chain, while keeping recovery ownership in `docs/m010-recovery-proof.md` and adding only a minimal forward cross-link.
duration: 
verification_result: passed
completed_at: 2026-05-23T20:37:43.057Z
blocker_discovered: false
---

# T02: Wired `docs/m010-integrated-proof.md` into the README, architecture guide, and recovery proof so reviewers can discover the M010 resilience close-out path from the repo’s main entry docs.

**Wired `docs/m010-integrated-proof.md` into the README, architecture guide, and recovery proof so reviewers can discover the M010 resilience close-out path from the repo’s main entry docs.**

## What Happened

Updated the repository documentation map in `README.md` to include `docs/m010-integrated-proof.md` alongside the existing milestone proof links, with wording that frames M010 as a resilience close-out review path joining outage truth, operator corroboration, and recovery confirmation on existing surfaces. Updated `docs/architecture.md` to extend the architecture proof chain with the same bounded pointer-first reference so reviewers can discover the integrated resilience proof from the core architecture entry doc. Added a minimal subordinate forward link in `docs/m010-recovery-proof.md` back to the integrated proof so the dedicated recovery walkthrough remains canonical for recovery details while still pointing reviewers to the broader M010 close-out path.

## Verification

Ran the task-plan verification command `rg -n "m010-integrated-proof" README.md docs/architecture.md docs/m010-recovery-proof.md docs/m010-integrated-proof.md` and confirmed all four docs now reference the integrated proof in the intended pointer-first review chain.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rg -n "m010-integrated-proof" README.md docs/architecture.md docs/m010-recovery-proof.md docs/m010-integrated-proof.md` | 0 | ✅ pass | 29ms |

## Deviations

None.

## Known Issues

The broad `python3 -m pytest` gate reported an environment-level LibreSSL/urllib3 warning in the automated verification pass, but this docs-only task used the narrower plan-defined verification command and did not require code-path changes.

## Files Created/Modified

- `README.md`
- `docs/architecture.md`
- `docs/m010-recovery-proof.md`
