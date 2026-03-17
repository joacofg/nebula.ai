---
phase: 05-product-proof-delivery
plan: 01
subsystem: benchmarking
tags: [benchmarking, markdown, reporting, makefile, pytest]
requires:
  - phase: 04-governance-hardening
    provides: Runtime metadata and fallback behavior that the benchmark proof package now summarizes explicitly
provides:
  - Summary-first benchmark JSON and Markdown artifacts with phase-5 comparison groups
  - Demo-sized benchmark dataset and repo-native `benchmark-demo` entrypoint
  - Automated coverage for proof-package report fields and demo subset ordering
affects: [documentation, evaluation, pilot-demo]
tech-stack:
  added: []
  patterns: [summary-first benchmark artifacts, phase-5 comparison grouping, demo subset via existing runner]
key-files:
  created: [.planning/phases/05-product-proof-delivery/05-01-SUMMARY.md, benchmarks/v1/demo-scenarios.jsonl]
  modified: [src/nebula/benchmarking/dataset.py, src/nebula/benchmarking/run.py, Makefile, tests/test_benchmarking.py]
key-decisions:
  - "Phase 5 benchmark storytelling is modeled as comparison-group metadata in the dataset layer so the report renderer can stay black-box and dataset-driven."
  - "The live demo path reuses the existing benchmark runner with a dedicated dataset instead of adding a second CLI or alternate artifact flow."
patterns-established:
  - "Benchmark artifacts lead with takeaways, comparison framing, and expectation mismatches before raw scenario rows."
  - "Demo-proof subsets are versioned JSONL datasets that preserve canonical mode ordering and run through the same CLI path."
requirements-completed: [EVAL-01, EVAL-02]
duration: 1min
completed: 2026-03-17
---

# Phase 5 Plan 1: Strengthen benchmark workflows and reports Summary

**Summary-first benchmark proof artifacts with comparison-group framing, mismatch notes, and a demo-sized dataset on the existing runner path**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-17T15:30:59Z
- **Completed:** 2026-03-17T15:31:59Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added Phase 5 comparison-group metadata so reports can frame premium control, local control, warm-cache, fallback, and supporting premium evidence explicitly.
- Reworked benchmark report generation into a summary-first JSON/Markdown proof package that preserves raw scenario rows while surfacing takeaways, route/cost highlights, and expectation mismatches.
- Added a five-scenario demo subset plus `make benchmark-demo` so operators can run a faster live proof without forking the benchmark engine.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add a human-readable benchmark summary layer on top of the existing raw report rows** - `0ba061f` (feat)
2. **Task 2: Ship a live-demo benchmark subset and repo-native execution path without changing the canonical suite** - `c76d43f` (feat)

## Files Created/Modified
- `src/nebula/benchmarking/dataset.py` - Defines Phase 5 comparison-group metadata and the mode-to-story mapping used by reports.
- `src/nebula/benchmarking/run.py` - Builds summary-first benchmark reports and renders the new Markdown structure.
- `benchmarks/v1/demo-scenarios.jsonl` - Captures the compact live-demo benchmark story beats.
- `Makefile` - Adds the `benchmark-demo` target that reuses the existing benchmark runner.
- `tests/test_benchmarking.py` - Locks the report-summary contract, comparison groups, and demo-subset behavior.

## Decisions Made
- Added comparison-group metadata in the dataset module rather than hard-coding storytelling rules inside the Markdown renderer.
- Kept `auto_complex` in the canonical suite as supporting premium-routed evidence instead of promoting it into the top-line five-group story.
- Treated the demo workflow as a dataset choice (`--dataset`) rather than a separate benchmark mode or CLI.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Benchmark proof artifacts and demo entrypoint are ready for the Phase 5 documentation plan to reference directly.
- No blockers identified for 05-02.

## Self-Check: PASSED

- Verified `.planning/phases/05-product-proof-delivery/05-01-SUMMARY.md`, `benchmarks/v1/demo-scenarios.jsonl`, and the benchmark implementation files exist.
- Verified task commits `0ba061f` and `c76d43f` exist in git history.
- Verified `.venv/bin/pytest tests/test_benchmarking.py -q` passed and the contract markers were present via `rg`.

---
*Phase: 05-product-proof-delivery*
*Completed: 2026-03-17*
