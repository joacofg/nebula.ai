---
estimated_steps: 3
estimated_files: 4
skills_used: []
---

# T02: Wire M010 proof discoverability from entry docs

Why: The integrated proof only closes the milestone if reviewers can find it from the repository’s main documentation index and architecture proof chain. Without discoverability, the proof remains siloed and easy to miss.

Do: Update `README.md` and `docs/architecture.md` to add bounded references to `docs/m010-integrated-proof.md` alongside the existing milestone proof links. Ensure the wording reflects that M010 is a resilience close-out path joining outage truth, operator corroboration, and recovery confirmation on existing surfaces. If `docs/m010-recovery-proof.md` lacks an obvious forward link to the integrated proof once the new doc exists, add a minimal cross-link without rewriting recovery ownership or duplicating content. Keep all references pointer-first and consistent with the anti-sprawl boundary.

Done when: the repo documentation map and architecture proof chain both mention `docs/m010-integrated-proof.md`, and any optional recovery-doc cross-link remains small and subordinate to the recovery document’s existing purpose.

## Inputs

- `README.md`
- `docs/architecture.md`
- `docs/m010-recovery-proof.md`
- `docs/m010-integrated-proof.md`

## Expected Output

- `README.md`
- `docs/architecture.md`
- `docs/m010-recovery-proof.md`

## Verification

rg -n "m010-integrated-proof" README.md docs/architecture.md docs/m010-recovery-proof.md docs/m010-integrated-proof.md

## Observability Impact

Improves documentation-level discoverability of the existing resilience inspection surfaces so future reviewers can find the health and console corroboration path quickly.
