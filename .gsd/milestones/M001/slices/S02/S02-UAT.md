# UAT — S02: Happy-path quickstart and production model

## Purpose
Validate that Nebula’s documented self-hosted adoption path and production model are clear, internally consistent, and actionable for a human operator without requiring guesswork.

## Preconditions
1. Repository checkout contains the S02 documentation updates.
2. Reviewer can open and read:
   - `README.md`
   - `docs/self-hosting.md`
   - `docs/quickstart.md`
   - `docs/production-model.md`
   - `docs/adoption-api-contract.md`
   - `docs/architecture.md`
3. Optional live-run precondition for runtime-backed checks:
   - self-hosted stack available via `docker compose -f docker-compose.selfhosted.yml up -d`
   - valid values prepared for `NEBULA_ADMIN_API_KEY`, `NEBULA_BOOTSTRAP_API_KEY`, provider credentials, and database settings
4. Known environment caveat for this worktree:
   - Python `pytest` and console `vitest` were not provisioned locally during slice closure, so test-suite-backed UAT steps may need a prepared environment.

## Test Case 1 — Entry docs route me to one canonical adoption story
**Goal:** Confirm a new adopter is not forced to assemble the flow from scattered docs.

### Steps
1. Open `README.md`.
2. Locate the documentation map and quick-start sections.
3. Follow the links to:
   - `docs/self-hosting.md`
   - `docs/quickstart.md`
   - `docs/production-model.md`
   - `docs/adoption-api-contract.md`
4. Check whether each document has a distinct role instead of duplicating the others.

### Expected outcome
- `README.md` clearly points to one supported deployment path, one quickstart, one production model, and one public API contract.
- The docs feel intentionally composed, not repetitive or conflicting.
- `docs/adoption-api-contract.md` is referenced as the public contract source of truth rather than being re-described in multiple places.

## Test Case 2 — Quickstart yields a first-request path without credential confusion
**Goal:** Confirm the happy path explains how to get from env setup to first public request.

### Steps
1. Open `docs/quickstart.md`.
2. Read from the beginning through the first request example.
3. Verify the doc explicitly tells you to:
   - copy `deploy/selfhosted.env.example` to `deploy/selfhosted.env`
   - set the required env vars
   - start the stack with `docker compose -f docker-compose.selfhosted.yml up -d`
   - sign into the console with the admin key
   - send a public request with `X-Nebula-API-Key`
4. Verify the doc explicitly distinguishes admin credentials from client credentials.

### Expected outcome
- A human reviewer can identify a concrete sequence from deployment to first public request.
- The document clearly states that `X-Nebula-Admin-Key` is for operator/admin flows and `X-Nebula-API-Key` is for application traffic.
- The doc does not imply that the admin key should be used for public inference calls.

## Test Case 3 — Tenant-header behavior is unambiguous
**Goal:** Confirm the docs explain when `X-Nebula-Tenant-ID` is required.

### Steps
1. In `docs/quickstart.md`, find the section describing request headers.
2. In `docs/production-model.md`, find the section explaining tenant inference rules.
3. Compare the explanations.
4. Verify the docs cover these cases:
   - single-tenant key
   - key with exactly one allowed tenant
   - multi-tenant key without `X-Nebula-Tenant-ID`
   - multi-tenant key with `X-Nebula-Tenant-ID`

### Expected outcome
- Both docs align on the rule: `X-Nebula-Tenant-ID` is only required when the key is authorized for multiple tenants and Nebula cannot infer the tenant automatically.
- The multi-tenant omission case is described as a rejection path, not a vague warning.
- No document implies that every request always needs `X-Nebula-Tenant-ID`.

## Test Case 4 — Production model matches current runtime truth
**Goal:** Confirm the operating-model doc does not invent unsupported product entities.

### Steps
1. Open `docs/production-model.md`.
2. Review the sections describing runtime entities and app/workload behavior.
3. Check whether the doc treats these as real enforced entities today:
   - tenant
   - tenant policy
   - API key
   - operator admin session
4. Check whether the doc describes app/workload as guidance only.

### Expected outcome
- The doc clearly states that tenant, policy, API key, and operator/admin surfaces are real runtime entities.
- The doc clearly states that app and workload are conceptual guidance only in M001.
- The doc does not claim there are first-class runtime resources like `/v1/admin/apps` or `/v1/admin/workloads`.

## Test Case 5 — Quickstart points to real operator evidence surfaces
**Goal:** Confirm the docs tell operators how to prove a first request worked.

### Steps
1. Open `docs/quickstart.md`.
2. Find the section about confirming the request through operator-visible evidence.
3. Verify that it points to all of the following:
   - `X-Nebula-*` public response headers
   - Playground
   - `GET /v1/admin/usage/ledger`
   - Observability
4. Check whether Playground is described correctly.

### Expected outcome
- The quickstart provides more than one verification surface.
- Playground is described as an admin/operator tool, not the public adoption boundary.
- The evidence surfaces form a coherent progression from immediate response proof to persisted operator proof.

## Test Case 6 — Live happy-path walkthrough (optional but preferred)
**Goal:** Validate the docs against a real self-hosted deployment.

### Steps
1. Follow `docs/self-hosting.md` and `docs/quickstart.md` exactly.
2. Configure `deploy/selfhosted.env` with real values.
3. Start the stack.
4. Visit `http://localhost:3000` and sign in with `NEBULA_ADMIN_API_KEY`.
5. Use either the bootstrap API key or create a tenant-scoped key.
6. Send the documented `POST /v1/chat/completions` request with `X-Nebula-API-Key`.
7. Inspect response headers.
8. Use Playground for operator-side confirmation.
9. Query `GET /v1/admin/usage/ledger` with `X-Nebula-Admin-Key`.
10. Open Observability and confirm the request appears in the expected operator-facing surfaces.

### Expected outcome
- The first public request succeeds with HTTP 200.
- The response includes meaningful `X-Nebula-*` metadata.
- The same activity is observable through Playground, usage ledger, and Observability.
- The human reviewer can complete the flow without needing undocumented steps.

## Test Case 7 — Edge case: multi-tenant key without tenant header
**Goal:** Verify the operating-model docs describe the ambiguous-tenant rejection path.

### Steps
1. Create or identify an API key authorized for more than one tenant.
2. Send a public `POST /v1/chat/completions` request using that key but omit `X-Nebula-Tenant-ID`.
3. Compare the observed behavior to the documented expectation.

### Expected outcome
- The request is rejected.
- The documentation accurately prepared the reviewer for this behavior.
- The failure mode reinforces that multi-tenant access is intentional and carries an extra calling requirement.

## Test Case 8 — Edge case: operator tries to use admin key as app credential
**Goal:** Confirm the docs strongly prevent trust-boundary confusion.

### Steps
1. Read the quickstart and production-model credential sections.
2. Attempt to answer this question only from the docs: “Can I use `X-Nebula-Admin-Key` for my application’s public inference traffic?”

### Expected outcome
- The answer is clearly “no.”
- The docs consistently describe the admin key as operator/admin-only.
- A reviewer would not leave the docs with a mixed or permissive interpretation.

## Test Case 9 — Audience framing check
**Goal:** Confirm the documentation speaks credibly to multiple adopter types.

### Steps
1. Read `README.md`, `docs/quickstart.md`, and `docs/production-model.md`.
2. Evaluate whether each of these audiences can find relevant framing:
   - startup product team wanting a fast first request
   - platform-minded team wanting tenant/key structure clarity
   - enterprise/self-hosted operator wanting explicit responsibility boundaries

### Expected outcome
- Startup teams can follow the happy path quickly.
- Platform teams can understand how tenant and key structure map to production.
- Enterprise/self-hosted operators can see the admin/operator responsibility boundary clearly.

## Test Case 10 — No dead ends or placeholder language
**Goal:** Confirm the docs feel finished enough for downstream slices to depend on.

### Steps
1. Review the touched docs:
   - `README.md`
   - `docs/self-hosting.md`
   - `docs/quickstart.md`
   - `docs/production-model.md`
   - `docs/architecture.md`
2. Confirm there are no `TODO` or `TBD` placeholders.
3. Follow all major cross-links manually.

### Expected outcome
- No placeholder text remains.
- Cross-links lead to real, relevant documents.
- A downstream slice author can safely reuse these docs as the canonical adoption baseline.

## UAT Verdict Rules
- **Pass:** Test cases 1–5, 8–10 pass, and optional live test case 6 either passes or is explicitly blocked by environment setup rather than document ambiguity.
- **Conditional pass:** Documentation-only cases pass, but live validation is deferred due to missing runtime/tooling setup.
- **Fail:** Any core ambiguity remains around the supported path, credential split, tenant-header rules, or runtime-vs-conceptual entity framing.

## Slice-Specific Notes
- This slice is primarily documentation composition, not new runtime implementation.
- The most important failure modes are ambiguity and contradiction, not visual polish.
- If a live run diverges from the docs, treat that as a high-priority docs/product mismatch for S05 closure.