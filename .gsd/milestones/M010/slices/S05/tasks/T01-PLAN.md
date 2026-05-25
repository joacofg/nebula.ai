---
estimated_steps: 3
estimated_files: 1
skills_used: []
---

# T01: Author the integrated M010 resilience proof document

Why: M010 already has validated outage, operator-surface, and recovery seams, but the milestone still needs one canonical close-out path that tells reviewers where to look and in what order without duplicating contracts or widening scope.

Do: Create `docs/m010-integrated-proof.md` using the pointer-first integrated-proof pattern established by prior milestone close-out docs. Anchor the document on the local-authority trust boundary and existing runtime health surfaces first, then join the two bounded outage classes proved in S02 (`governance_store` fail-closed and `semantic_cache` degraded-serving), the existing console corroboration seams from S03, and the recovery confirmation path from `docs/m010-recovery-proof.md` and the deterministic tests from S04. Include canonical sources, what the proof establishes, a strict proof order, a source-fit table, a minimal reviewer/operator walkthrough, explicit anti-duplication and anti-sprawl boundaries, and concrete failure modes that reveal drift. Keep hosted/control-plane wording subordinate to the existing local-authority boundary and do not restate full field contracts already owned by health endpoints, tests, or console code.

Done when: `docs/m010-integrated-proof.md` exists, is non-empty, and gives a stranger-readable, pointer-first integrated review path that closes R086/R089 support while preserving R088’s operator-surface role without adding any new runtime or UI feature scope.

## Inputs

- `docs/m009-integrated-proof.md`
- `docs/m010-recovery-proof.md`
- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/components/health/runtime-health-cards.tsx`
- `docs/hosted-reinforcement-boundary.md`

## Expected Output

- `docs/m010-integrated-proof.md`

## Verification

python3 -c "from pathlib import Path; p = Path('docs/m010-integrated-proof.md'); assert p.exists() and p.stat().st_size > 0; print(p.stat().st_size)"

## Observability Impact

Documents the canonical inspection order across `/health/ready`, `/health/dependencies`, console runtime health cards, and Observability so future agents and operators can localize outage-versus-recovery truth without adding new surfaces.
