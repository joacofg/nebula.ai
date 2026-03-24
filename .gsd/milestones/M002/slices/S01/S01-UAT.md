# S01: Operator structuring truth surface — UAT

## Preconditions

1. Worktree includes the S01 console changes.
2. Console dependencies are installed (`npm --prefix console install`).
3. Targeted vitest files exist and pass in this worktree.
4. If running the UI manually, the console is available and renders the API Keys, Playground, and Observability pages with an admin session.

## UAT Goal

Confirm that the highest-impact operator surfaces tell one runtime-truthful story about tenant scope, API-key behavior, Playground’s role, and Observability’s role.

---

## Test Case 1 — API Keys page explains tenant inference vs explicit tenant header

**Purpose:** Verify that the API Keys overview gives an operator the right mental model before issuing or inspecting keys.

### Steps
1. Open the API Keys page.
2. Read the main page heading and introductory copy.
3. Look for the explanation of `allowed_tenant_ids`.
4. Look for the explanation of `tenant_id`.
5. Confirm the page explains when `X-Nebula-Tenant-ID` is required.

### Expected Outcomes
- The page reads as a client-credentials surface, not a vague admin inventory.
- It states that `allowed_tenant_ids` defines which tenants the key may use.
- It states that `tenant_id` provides the default tenant when callers omit `X-Nebula-Tenant-ID`.
- It states that a key authorizing multiple tenants without a default requires `X-Nebula-Tenant-ID` on requests.
- No copy introduces `app` or `workload` as runtime entities.

---

## Test Case 2 — Create API key dialog explains real tenant-resolution order

**Purpose:** Verify that key issuance guidance is aligned to existing runtime behavior.

### Steps
1. Open the API Keys page.
2. Click **Create API key**.
3. Read the explanatory text at the top of the dialog.
4. Inspect the helper text under `tenant_id`.
5. Inspect the helper text under `allowed_tenant_ids`.

### Expected Outcomes
- The dialog explains that `allowed_tenant_ids` defines every tenant the key may access.
- The dialog explains that Nebula honors an explicit `X-Nebula-Tenant-ID` when it matches an allowed tenant.
- The dialog explains the fallback behavior through `tenant_id`, then the single allowed tenant.
- The dialog states that multi-tenant authorization without a default `tenant_id` requires the public caller to send the tenant header.
- The helper copy under `allowed_tenant_ids` explicitly distinguishes single-tenant inference from intentional multi-tenant authorization.

---

## Test Case 3 — API key table distinguishes all supported tenant-scope cases

**Purpose:** Verify that inventory rows expose runtime-true scope semantics instead of generic labels.

### Steps
1. Open the API Keys page with seed data or mocked rows representing:
   - one key with `tenant_id` set
   - one key with `tenant_id = null` and one allowed tenant
   - one key with `tenant_id = null` and multiple allowed tenants
2. Read the **Tenant Scope** column for each row.
3. Inspect any revoked row if present.

### Expected Outcomes
- A row with `tenant_id` shows an auto-resolve/default-tenant summary.
- A row with exactly one allowed tenant and no default says that the only allowed tenant is inferred.
- A row with multiple allowed tenants and no default says public callers must send `X-Nebula-Tenant-ID`.
- Revoked keys remain visible for audit/history purposes.
- Scope language is derived from current runtime fields, not invented labels.

---

## Test Case 4 — Playground reads as admin-only corroboration, not the public adoption path

**Purpose:** Verify the trust boundary between the public API contract and the admin Playground.

### Steps
1. Open the Playground page.
2. Read the page title and the paragraph below it.
3. Confirm whether the page references the active admin session.
4. Confirm whether it distinguishes itself from `POST /v1/chat/completions`.
5. Confirm whether it is marked non-streaming.

### Expected Outcomes
- The page heading reads as an operator corroboration surface.
- The copy explicitly references the active admin session.
- The copy states this checks the live routing path without acting as the public `POST /v1/chat/completions` integration boundary.
- The page is clearly marked non-streaming.
- The page does not teach Playground as the main public client migration path.

---

## Test Case 5 — Playground form preserves tenant-selected operator behavior

**Purpose:** Verify that the request form itself reinforces the operator-only usage model.

### Steps
1. On the Playground page, inspect the request form heading and helper copy.
2. Confirm the form requires a tenant selection.
3. Confirm the explanatory footer text describes immediate vs recorded evidence.
4. If possible, run one prompt.

### Expected Outcomes
- The form heading reads **Operator playground request**.
- The form copy says the operator chooses tenant context on purpose.
- The form describes the path as an admin-session, non-streaming playground request.
- The footer explains that the first response is immediate and the recorded ledger evidence appears after Nebula persists the outcome.
- If a prompt is run, the operator can see immediate response content before recorded outcome details appear.

---

## Test Case 6 — Playground still separates immediate response from recorded outcome

**Purpose:** Verify the proof boundary between immediate request corroboration and persisted evidence.

### Steps
1. Run a Playground prompt with a valid admin session.
2. Observe the response area immediately after submission.
3. Observe the UI while recorded outcome data is still loading.
4. Observe the recorded-outcome card after the ledger lookup resolves.

### Expected Outcomes
- Immediate response content and request metadata appear first.
- While ledger lookup is pending, the UI indicates recorded outcome is still loading.
- Once available, the recorded-outcome card identifies itself as a persisted ledger record for the same request.
- The UI does not collapse immediate response and persisted outcome into one generic state.

---

## Test Case 7 — Observability reads as persisted request evidence first

**Purpose:** Verify that Observability is framed as the ledger-first explanation surface.

### Steps
1. Open the Observability page.
2. Read the primary page heading and intro copy.
3. Confirm the page discusses recorded request outcomes.
4. Confirm the dependency-health section has its own heading and explanatory text.

### Expected Outcomes
- The main heading reads **Persisted request evidence**.
- The intro copy explains that operators inspect the persisted usage ledger by tenant, route target, terminal status, and time window.
- The intro copy says dependency health is supporting runtime context for the same investigation.
- The dependency section heading reads **Dependency health context**.
- The dependency section explicitly says it does not replace the ledger record.

---

## Test Case 8 — Observability preserves the operator investigation model

**Purpose:** Verify that request evidence and runtime context remain distinct but related.

### Steps
1. Open Observability with at least one ledger row available.
2. Select a request row if one is not already selected.
3. Review the request detail panel.
4. Review the dependency-health cards.

### Expected Outcomes
- The page continues to center on recorded request outcomes.
- Request-level investigation remains anchored on ledger rows and request details.
- Dependency health appears as supporting context, not as a replacement explanation.
- Existing runtime investigation anchors remain visible: request ids, route target, terminal status, and dependency states.

---

## Edge Cases

### Edge Case A — Single allowed tenant with no default
1. Inspect a key with `tenant_id = null` and one entry in `allowed_tenant_ids`.
2. Confirm the UI says the tenant is inferred automatically.

**Expected:** The UI does not incorrectly require `X-Nebula-Tenant-ID` for this case.

### Edge Case B — Multiple allowed tenants with no default
1. Inspect a key with `tenant_id = null` and multiple entries in `allowed_tenant_ids`.
2. Confirm the UI says callers must send `X-Nebula-Tenant-ID`.

**Expected:** The UI does not imply tenant inference is possible for intentionally multi-tenant keys.

### Edge Case C — Revoked API key remains visible
1. Inspect a revoked key row.
2. Confirm it is still shown in the table.

**Expected:** Historical scope remains visible for operator auditability.

### Edge Case D — Missing Playground admin session
1. Render or open Playground without an admin session.
2. Inspect the form state.

**Expected:** The UI shows **Operator session missing** and blocks prompt submission.

---

## Supporting Automated Evidence

The following automated checks back this UAT script:

- `npm --prefix console run test -- --run src/components/api-keys/create-api-key-dialog.test.tsx src/components/api-keys/api-key-table.test.tsx`
- `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx`
- `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`

All passed in this worktree for S01.