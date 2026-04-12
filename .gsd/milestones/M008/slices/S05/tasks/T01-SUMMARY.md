---
id: T01
parent: S05
milestone: M008
key_files:
  - docs/m008-integrated-proof.md
  - README.md
  - docs/architecture.md
key_decisions:
  - Kept the M008 proof doc pointer-only and delegated detailed contracts back to policy/options, ledger, retention lifecycle, and hosted trust-boundary canonicals instead of duplicating them.
  - Reused the shared hosted-contract evidence vocabulary in the integrated proof so retained/suppressed/deleted/not-hosted wording stays aligned with shipped UI and test seams.
duration: 
verification_result: passed
completed_at: 2026-04-12T17:27:04.284Z
blocker_discovered: false
---

# T01: Added the canonical M008 integrated governance proof doc and linked it from the main documentation entrypoints.

**Added the canonical M008 integrated governance proof doc and linked it from the main documentation entrypoints.**

## What Happened

I authored `docs/m008-integrated-proof.md` as a pointer-only integrated walkthrough that follows the established M006/M007 pattern and keeps each shipped seam in its canonical role. The new proof starts with tenant policy and runtime-enforced evidence options, moves through one persisted usage-ledger row and request detail as the primary historical evidence while the row exists, then points to persisted `evidence_expires_at`-driven retention cleanup plus `retention_lifecycle` health as supporting runtime context, and finishes with the hosted metadata-only trust boundary. I reused the shared retained/suppressed/deleted/not-hosted vocabulary from `console/src/lib/hosted-contract.ts` in the document framing so the proof does not imply recovery semantics, soft-delete archives, hosted raw-ledger export, or hosted runtime authority. I also added minimal discoverability links in `README.md` and `docs/architecture.md` so reviewers can find the new proof without expanding those docs into secondary explanation surfaces.

## Verification

Ran the task’s required Python assertion script against `docs/m008-integrated-proof.md`, `README.md`, and `docs/architecture.md`. The check confirmed the new document exists, includes the required proof-order headings and required phrases (`tenant policy`, `evidence_expires_at`, `request detail`, `retention_lifecycle`, `metadata-only`), contains no `TBD`/`TODO` placeholders, and that both documentation entrypoints now reference `docs/m008-integrated-proof.md`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 - <<'PY'
from pathlib import Path
proof = Path('docs/m008-integrated-proof.md')
assert proof.exists(), 'missing docs/m008-integrated-proof.md'
text = proof.read_text()
for heading in [
    '# M008 integrated governance proof',
    '## What this integrated proof establishes',
    '## Canonical proof order',
    '## Minimal operator walkthrough',
    '## Failure modes this integrated proof makes obvious',
]:
    assert heading in text, heading
for phrase in [
    'tenant policy',
    'evidence_expires_at',
    'request detail',
    'retention_lifecycle',
    'metadata-only',
]:
    assert phrase in text, phrase
for path in ['README.md', 'docs/architecture.md']:
    assert 'docs/m008-integrated-proof.md' in Path(path).read_text(), path
assert 'TBD' not in text and 'TODO' not in text
PY` | 0 | ✅ pass | 42ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `docs/m008-integrated-proof.md`
- `README.md`
- `docs/architecture.md`
