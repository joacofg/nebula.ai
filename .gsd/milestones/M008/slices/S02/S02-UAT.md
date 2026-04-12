# S02: Governed ledger persistence and request markers — UAT

**Milestone:** M008
**Written:** 2026-04-12T00:33:51.615Z

# UAT — Governed ledger persistence and request markers

## Preconditions

1. Nebula backend test environment is available with the project virtualenv provisioned.
2. A tenant exists with M008 evidence governance enabled through tenant policy fields (`evidence_retention_window`, `metadata_minimization_level`).
3. Operator access to the existing admin usage-ledger/read surfaces is available.
4. No background retention scheduler is assumed; cleanup is exercised through the explicit local lifecycle seam introduced in this slice.

## Test Case 1 — New governed requests persist historical governance markers

1. Submit a new governed request for a tenant with evidence governance enabled.
   - Expected: A usage-ledger row is created for the request.
2. Open the request through `/v1/admin/usage/ledger` or the request-detail surface.
   - Expected: The row shows persisted write-time markers such as `evidence_retention_window`, `evidence_expires_at`, `metadata_fields_suppressed`, and `governance_source`.
3. Change the tenant policy after the request is written.
   - Expected: The already-persisted row still shows the original row-level governance markers rather than being recomputed from the new policy.

## Test Case 2 — Explicit cleanup deletes only expired governed rows

1. Prepare one governed row whose persisted `evidence_expires_at` is in the past and one governed row whose persisted expiration is still in the future.
   - Expected: Both rows are visible through `/v1/admin/usage/ledger` before cleanup.
2. Run the explicit retention cleanup seam with `now` set at or after the expired row’s `evidence_expires_at`.
   - Expected: Cleanup returns a deterministic summary showing one eligible expired row and one deleted row.
3. Query `/v1/admin/usage/ledger` again.
   - Expected: The expired row no longer appears.
   - Expected: The surviving row is still present and still shows its persisted governance markers.

## Test Case 3 — Rows without persisted expiration markers are preserved

1. Prepare a usage-ledger row that has no persisted `evidence_expires_at` marker.
   - Expected: The row is visible before cleanup.
2. Run the explicit cleanup seam using the same cutoff that removed expired governed rows.
   - Expected: The no-expiration row is ignored by cleanup.
3. Query `/v1/admin/usage/ledger` again.
   - Expected: The no-expiration row still exists and remains inspectable.

## Test Case 4 — Cleanup is idempotent

1. Run cleanup once for a set of already-expired rows.
   - Expected: Eligible/deleted counts reflect the expired rows removed in that pass.
2. Run cleanup again with the same cutoff.
   - Expected: The second pass reports zero additional deletions.
3. Query `/v1/admin/usage/ledger` after the second pass.
   - Expected: No previously deleted row reappears, and no surviving row is removed unexpectedly.

## Test Case 5 — Request detail explains real deletion semantics truthfully

1. Open a surviving governed request in the console request-detail surface.
   - Expected: The UI states that the persisted row is authoritative while it exists.
2. Read the evidence-retention explanatory copy in request detail.
   - Expected: The copy explains that governed cleanup can remove expired evidence later.
   - Expected: The copy does not imply soft-delete, hidden archive recovery, or hosted raw export.
3. After cleanup removes an expired row, attempt to find that request again in the operator ledger surface.
   - Expected: The request is absent rather than shown as an archived or recoverable entry.

## Edge Cases

1. **Policy changed after write:** A row written under an earlier tenant policy must continue showing its original persisted governance markers until it is deleted.
2. **No expiration marker:** Cleanup must not delete rows that lack `evidence_expires_at`.
3. **Repeated cleanup:** Running cleanup multiple times at the same cutoff must be safe and produce zero additional deletions after the first successful pass.
4. **Hosted boundary:** No UAT step should reveal raw prompts, raw responses, provider credentials, or any hosted raw ledger export path; hosted behavior remains metadata-only.
5. **Shared persistence seam:** Both chat and embeddings request families must continue to produce governed ledger rows with the expected per-request markers after the cleanup lifecycle feature is added.
