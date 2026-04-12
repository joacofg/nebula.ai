# S03: Retention lifecycle enforcement — UAT

**Milestone:** M008
**Written:** 2026-04-12T17:03:23.553Z

# UAT — S03 Retention lifecycle enforcement

## Preconditions

- Nebula is running with M008/S03 code and default retention cleanup enabled.
- A test tenant exists with evidence governance already configured from S01/S02.
- The operator can access `/health/ready`, `/health/dependencies`, `/v1/admin/usage/ledger`, and the console Observability page.
- At least three ledger rows can be prepared for one tenant/request cohort:
  1. one row with `evidence_expires_at` in the past,
  2. one row with `evidence_expires_at` in the future,
  3. one row with `evidence_expires_at = null`.
- For deterministic proof in non-production environments, the operator may trigger the lifecycle through the test/helper seam used by automated verification (or wait for the configured cleanup interval).

## Test Case 1 — Expired evidence is actually deleted through the lifecycle

1. Open `/v1/admin/usage/ledger` and confirm all three prepared rows are visible before cleanup.
   - Expected: the expired row, future-expiration row, and null-expiration row all appear before the lifecycle runs.
2. Trigger one retention cleanup run through the real lifecycle seam, or wait for the configured interval to elapse.
   - Expected: cleanup executes without requiring a retention-specific admin endpoint.
3. Refresh `/v1/admin/usage/ledger` using the same filters/request IDs.
   - Expected: the expired row is no longer returned.
   - Expected: the future-expiration row still exists.
   - Expected: the null-expiration row still exists.
4. Confirm request-detail access for the surviving rows still shows their governance markers normally.
   - Expected: surviving rows remain inspectable through the existing ledger/request-detail surfaces.

## Test Case 2 — Runtime health reports lifecycle status truthfully

1. Open `/health/ready`.
   - Expected: the response includes a `retention_lifecycle` dependency payload.
   - Expected: payload includes bounded fields such as status/detail, enablement, last status, last run/attempt times, counts, and last error.
2. Open `/health/dependencies`.
   - Expected: the same retention lifecycle dependency is visible through the dependency-health surface.
3. After a successful cleanup run, inspect the retention dependency fields again.
   - Expected: `last_status` indicates success, `last_run_at` is populated, and count fields reflect the run.

## Test Case 3 — Console observability shows retention lifecycle on existing cards only

1. Open the console Observability page.
   - Expected: runtime health includes a card for the retention lifecycle dependency.
2. Inspect the retention lifecycle card content.
   - Expected: the card shows truthful summary information such as current status, last run/attempt, deleted rows, eligible rows, and last error when present.
3. Inspect the rest of the page structure.
   - Expected: there is no dedicated retention dashboard, wizard, or new cleanup control surface; the lifecycle is represented only as part of existing runtime health/observability cards.

## Test Case 4 — Failure is visible but does not falsely imply gateway outage

1. Simulate a cleanup failure in a non-production environment (for example, by forcing the governance-store cleanup seam to raise during a run).
   - Expected: the retention lifecycle records a failed attempt rather than crashing request serving.
2. Re-open `/health/ready` and `/health/dependencies`.
   - Expected: `retention_lifecycle` reports a degraded or failed status with a bounded `last_error` and updated `last_attempted_run_at`.
   - Expected: the gateway can still report overall readiness as degraded rather than unavailable if only this optional dependency failed.
3. Open the console Observability runtime health section.
   - Expected: the retention lifecycle card surfaces the failure truthfully through the existing dependency-card UI.

## Test Case 5 — Hosted boundary remains metadata-only

1. Inspect the hosted heartbeat/dependency summary path after the new lifecycle dependency is present.
   - Expected: the hosted payload includes only coarse dependency membership (`healthy`, `degraded`, or `unavailable`) for `retention_lifecycle`.
   - Expected: hosted export does not contain deleted row counts, eligible counts, cutoff times, raw evidence, or cleanup payload details.

## Edge Cases

- A row whose expiration is in the future must survive cleanup even if the tenant’s current policy is stricter than when the row was written.
- A row with no expiration marker must survive cleanup.
- A failed cleanup attempt must update failure diagnostics without introducing raw evidence into health payloads.
- Disabling the lifecycle by configuration should prevent the background loop from starting and should report that disabled state truthfully on health surfaces.
