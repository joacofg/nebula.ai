---
id: T01
parent: S05
milestone: M006
provides: []
requires: []
affects: []
key_files: ["docs/m006-integrated-proof.md", "README.md", "docs/architecture.md", ".gsd/KNOWLEDGE.md"]
key_decisions: ["D038: Keep the M006 close-out proof pointer-only and discoverability-first instead of duplicating calibrated-routing, replay, or operator-surface contracts."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Mechanical verification passed for the new doc and discoverability pointers. The file/content check passed with `./.venv/bin/python`, confirming `docs/m006-integrated-proof.md`, `README.md`, and `docs/architecture.md` exist, are non-empty, include the required proof seams, and contain no `TODO` or `TBD` placeholders. The planned `rg` check also passed, confirming the expected M006 proof references appear across the new doc and pointer surfaces."
completed_at: 2026-04-02T04:22:56.987Z
blocker_discovered: false
---

# T01: Added the pointer-only M006 integrated proof and linked it from README and architecture.

> Added the pointer-only M006 integrated proof and linked it from README and architecture.

## What Happened
---
id: T01
parent: S05
milestone: M006
key_files:
  - docs/m006-integrated-proof.md
  - README.md
  - docs/architecture.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D038: Keep the M006 close-out proof pointer-only and discoverability-first instead of duplicating calibrated-routing, replay, or operator-surface contracts.
duration: ""
verification_result: mixed
completed_at: 2026-04-02T04:22:56.988Z
blocker_discovered: false
---

# T01: Added the pointer-only M006 integrated proof and linked it from README and architecture.

**Added the pointer-only M006 integrated proof and linked it from README and architecture.**

## What Happened

Created `docs/m006-integrated-proof.md` as the calibrated-routing close-out walkthrough that joins the stable route vocabulary, one public `POST /v1/chat/completions` response, calibrated `X-Nebula-*` and `X-Request-ID` evidence, request-id-to-ledger correlation, replay parity via `policy/simulate`, and selected-request-first Observability inspection without redefining those seams. Updated `README.md` and `docs/architecture.md` only to add discoverability pointers to the new proof artifact. Recorded the pointer-only composition rule as decision D038 and added the matching M006 integrated-proof guidance to `.gsd/KNOWLEDGE.md`.

## Verification

Mechanical verification passed for the new doc and discoverability pointers. The file/content check passed with `./.venv/bin/python`, confirming `docs/m006-integrated-proof.md`, `README.md`, and `docs/architecture.md` exist, are non-empty, include the required proof seams, and contain no `TODO` or `TBD` placeholders. The planned `rg` check also passed, confirming the expected M006 proof references appear across the new doc and pointer surfaces.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python - <<'PY' ... PY` | 127 | ❌ fail | 100ms |
| 2 | `rg -n "m006-integrated-proof|route-decision-vocabulary|X-Request-ID|X-Nebula-|/v1/admin/usage/ledger|policy/simulate|Observability|does not duplicate|failure modes" README.md docs/architecture.md docs/m006-integrated-proof.md` | 0 | ✅ pass | 100ms |
| 3 | `./.venv/bin/python - <<'PY' ... PY` | 1 | ❌ fail | 100ms |
| 4 | `./.venv/bin/python - <<'PY' ... PY` | 0 | ✅ pass | 100ms |
| 5 | `rg -n "m006-integrated-proof|route-decision-vocabulary|X-Request-ID|X-Nebula-|/v1/admin/usage/ledger|policy/simulate|Observability|does not duplicate|failure modes" README.md docs/architecture.md docs/m006-integrated-proof.md` | 0 | ✅ pass | 100ms |


## Deviations

The task plan’s verification snippet used `python`, but the active worktree only exposed the project interpreter as `./.venv/bin/python`, so I reran the same check with that interpreter. No product-scope deviation was made.

## Known Issues

None.

## Files Created/Modified

- `docs/m006-integrated-proof.md`
- `README.md`
- `docs/architecture.md`
- `.gsd/KNOWLEDGE.md`


## Deviations
The task plan’s verification snippet used `python`, but the active worktree only exposed the project interpreter as `./.venv/bin/python`, so I reran the same check with that interpreter. No product-scope deviation was made.

## Known Issues
None.
