---
phase: closeout
phase_name: Milestone Completion
project: Nebula
generated: 2026-04-27T21:52:00Z
counts:
  decisions: 4
  lessons: 3
  patterns: 4
  surprises: 3
missing_artifacts:
  - Per-slice ASSESSMENT artifacts were absent; milestone validation remained needs-attention even though slice summaries, UAT, and verification evidence were present.
---

### Decisions
- Kept one shared backend contract for recent tenant-scoped outcome evidence and route-score factors across runtime routing, replay, persistence, and operator evidence so live decisions, simulations, and request-level explanations stay aligned.
  Source: DECISIONS.md/D049
- Extended routing with a bounded additive scoring model instead of a larger branch tree or opaque optimizer so route factors stay deterministic, persistable, replayable, and operator-readable.
  Source: DECISIONS.md/D050
- Preserved request detail and selected-request Observability as the primary operator surfaces for outcome-grounded routing evidence, with tenant summary context remaining supporting only.
  Source: DECISIONS.md/D051
- Kept hosted and fleet-level state out of live route choice and outcome-evidence truth so M009 improves routing quality without weakening Nebula’s local-authority and metadata-only hosted boundary.
  Source: DECISIONS.md/D052

### Lessons
- Pytest `-k` selectors are case-sensitive in this repo’s verification flows; mixed-case selectors like `Route-Mode` can falsely deselect all tests and must be normalized to the actual lowercase test naming used by the suites.
  Source: S02-SUMMARY.md/Deviations
- Close-out proof stayed more reliable when it strengthened focused existing seams instead of adding new broad harnesses: backend parity was locked through targeted request/header/governance tests and degraded operator proof was kept in deterministic request-detail coverage rather than a brittle larger UI flow.
  Source: S05-SUMMARY.md/What Happened
- Replay parity verification is strongest when unchanged-policy parity and changed-policy drift are separated into distinct assertions inside the same simulation coverage, which makes failures easier to interpret without creating duplicate replay paths.
  Source: S03-SUMMARY.md/Deviations

### Patterns
- Extend existing typed evidence seams additively instead of creating new API families or replay-only structures when deepening backend semantics or operator evidence.
  Source: S01-SUMMARY.md/Patterns established
- Use a single typed evidence-summary contract across live routing, persistence, replay, and operator inspection to prevent semantic drift between runtime and admin flows.
  Source: S02-SUMMARY.md/Patterns established
- Compute tenant-window evidence classification once per bounded replay window and reuse it everywhere that simulation request needs it rather than re-classifying per row.
  Source: S03-SUMMARY.md/Patterns established
- Integrated proof docs should remain pointer-first and link the existing request, ledger, simulation, and request-detail seams rather than duplicating contracts inline.
  Source: S05-SUMMARY.md/Patterns established

### Surprises
- Milestone validation landed at `needs-attention` not because delivery was incomplete, but because every slice lacked a dedicated ASSESSMENT artifact even though SUMMARY, UAT, and verification evidence were present.
  Source: M009-VALIDATION.md/Slice Delivery Audit
- Broader Observability-page degraded proof was briefly attempted during close-out, but it proved brittle enough that the authoritative degraded assertion had to remain in deterministic request-detail tests.
  Source: S05-SUMMARY.md/Deviations
- The local shell environment exposed `python3.12` rather than `python`, requiring close-out verification commands to be adjusted even though the underlying proof remained the same.
  Source: S05-SUMMARY.md/Deviations
