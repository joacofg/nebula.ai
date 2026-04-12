# S01: Typed evidence governance policy — UAT

**Milestone:** M008
**Written:** 2026-04-12T00:22:35.881Z

# UAT — M008/S01 Typed evidence governance policy

## Preconditions
- Nebula backend is running with the M008/S01 schema and code applied.
- Operator can access the console policy page and request-detail surface.
- A test tenant and API key exist.
- The console test environment or a live local environment can issue one chat request and one embeddings request for the same tenant.

## Test Case 1 — Operator can configure governed evidence controls from the existing policy boundary
1. Open the tenant policy page for the test tenant.
   - Expected: The existing runtime-enforced policy section includes controls for evidence retention window and metadata minimization level.
2. Set evidence retention to a bounded non-default option and metadata minimization to a stricter option than the current value.
   - Expected: The UI describes both settings as write-time/runtime-enforced evidence controls, not as future advisory capture settings.
3. Review any advanced/deferred capture copy on the page.
   - Expected: Prompt/response capture remains clearly described as advisory or out of scope; the page does not imply raw payload capture is part of this slice.
4. Save the policy.
   - Expected: The policy persists successfully and the saved state reflects the chosen retention/minimization settings.

## Test Case 2 — Chat request persists governed evidence markers under the selected tenant policy
1. With the updated tenant policy in place, send a chat completion request using the tenant API key.
   - Expected: The request succeeds and returns a request identifier/header that can be used for ledger lookup.
2. Open the matching request in the usage ledger / request-detail surface.
   - Expected: The persisted row includes governed evidence markers such as message type, evidence retention window or expiration, metadata minimization level, any suppressed metadata fields, and governance source.
3. Inspect the row for payload scope.
   - Expected: The row does not imply raw prompt/response capture; only the bounded metadata contract is present.
4. Compare the rendered request-detail values with the policy just saved.
   - Expected: The persisted governance markers match the policy that was active when the request was written.

## Test Case 3 — Embeddings request uses the same governed persistence seam and remains correlatable
1. Send an embeddings request for the same tenant.
   - Expected: The request succeeds even if middleware state is limited, and a request identifier is still available for correlation.
2. Look up the embeddings row in the usage ledger.
   - Expected: The embeddings row is present and includes the same governed evidence markers pattern as chat, adapted to the embeddings record shape.
3. Inspect request-detail for that row.
   - Expected: Governance markers are visible without needing to inspect raw JSON, and the row remains historically attributable to the policy active at write time.

## Test Case 4 — Policy minimization is truthful in operator surfaces
1. Change metadata minimization to a stricter level for the tenant.
   - Expected: The policy save succeeds and the updated level is visible in the policy surface.
2. Send another chat or embeddings request after the change.
   - Expected: A new ledger row is created.
3. Compare the new row to the earlier row.
   - Expected: The new row shows the stricter minimization marker and any suppressed metadata field markers appropriate to that level, while the earlier row still reflects the older policy state.
4. Re-open the first row.
   - Expected: The first row remains historically truthful and does not retroactively adopt the new minimization settings.

## Test Case 5 — Hosted boundary stays metadata-only
1. Exercise the hosted-contract verification path or inspect the hosted export behavior relevant to request evidence.
   - Expected: Hosted export remains metadata-only and does not include raw prompt/response payloads or new authority over local evidence governance.
2. Compare the hosted boundary description with the local policy/request-detail surfaces.
   - Expected: The product story is consistent: local tenant policy governs persistence boundaries, while hosted remains bounded and non-authoritative.

## Edge Cases
- If `pytest` is not available on PATH during local verification, rerun the Python checks with `./.venv/bin/pytest`; this is an environment issue, not a slice failure.
- If a request is recorded when middleware request state is absent, embeddings evidence should still remain correlatable through a generated fallback request ID.
- Historical rows created before a policy change should continue to show the governance markers that applied at write time rather than the tenant's current settings.
