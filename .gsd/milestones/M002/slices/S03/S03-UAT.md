# S03 UAT — Integrated production-structuring walkthrough

## Purpose

Use this acceptance script to rehearse Nebula's canonical integrated adoption proof in the same order as `docs/integrated-adoption-proof.md`.

The goal is not to invent a new workflow. The goal is to prove that an operator can:

1. choose tenant and API-key structure first
2. decide whether `X-Nebula-Tenant-ID` is required
3. send the public request on `POST /v1/chat/completions`
4. capture `X-Request-ID` and the `X-Nebula-*` response headers
5. correlate the same request in the usage ledger
6. use Playground and Observability only as operator corroboration surfaces

## Redaction rules

- Do not record real secret values in notes, screenshots, or pasted commands.
- Refer to key names only, such as `X-Nebula-API-Key` and `X-Nebula-Tenant-ID`.
- If you capture examples, keep only request identifiers and non-secret metadata.

## Preconditions

- The reader has `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`, and `docs/integrated-adoption-proof.md` available.
- A Nebula environment is running with at least one tenant and an operator admin session available for `/v1/admin/*` and console access.
- The operator can inspect the Tenants, Playground, and Observability pages in the console.
- The operator can query or inspect `GET /v1/admin/usage/ledger`.

## Acceptance script

### 1. Start from production structuring

Open `docs/production-model.md` and confirm the operator can explain all of the following before sending any request:

- tenant is the enforced runtime boundary for policy, authorization, and usage attribution
- API keys segment which callers can reach each tenant
- operator admin sessions are separate from application credentials
- app and workload remain team guidance labels, not first-class Nebula runtime or admin objects

**Pass if:** the operator can describe tenant/API-key structure without introducing pseudo-entities such as workspace, app object, or workload object.

### 2. Decide whether `X-Nebula-Tenant-ID` is needed

Using the production model and migration reference, decide which of these cases applies:

- a tenant-scoped API key that resolves to one tenant automatically
- an intentionally multi-tenant API key that requires `X-Nebula-Tenant-ID`

Confirm the operator can state the rule correctly:

- send `X-Nebula-Tenant-ID` only when the key is intentionally authorized for multiple tenants
- do not describe the header as universal boilerplate for every caller

**Pass if:** the operator can explain both the inferred-tenant case and the ambiguous multi-tenant case without contradiction.

### 3. Send the public request first

Use `docs/quickstart.md` or `docs/reference-migration.md` to send one real public `POST /v1/chat/completions` request.

Boundary reminders:

- this is the real adoption target
- do not start in Playground
- do not use operator admin credentials as a substitute for the public caller

**Pass if:** the first runtime proof step is the public request, not an admin-only console action.

### 4. Capture the immediate public evidence

After the request completes, record the public response evidence before opening any operator surface.

Capture these headers if present:

- `X-Request-ID`
- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

**Pass if:** the operator can point to `X-Request-ID` and the `X-Nebula-*` headers as the first explainability seam on the public route itself.

### 5. Correlate the same request in the usage ledger

Use the `X-Request-ID` from the public response to inspect the matching ledger record in `GET /v1/admin/usage/ledger`.

Confirm the persisted record lines up with the public request on fields such as:

- `request_id`
- `tenant_id`
- `final_route_target`
- `final_provider`
- `route_reason`
- `policy_outcome`
- `terminal_status`

**Pass if:** the operator can show that the public request is not only visible in headers but also persisted in the usage ledger for the same request id.

### 6. Use Tenants as structuring corroboration only

Open the Tenants console page and confirm the page copy still frames tenants correctly:

- tenants are the enforced runtime boundary
- API keys are issued separately for caller access
- app/workload remain conventions or metadata guidance rather than product objects

**Pass if:** the surface reinforces tenant/API-key structure without implying extra runtime entities.

### 7. Use Playground as operator corroboration only

Open Playground only after the public request and ledger correlation are already established.

Confirm the page and form communicate that:

- Playground is an operator-admin surface
- the operator chooses tenant context on purpose
- the request is non-streaming and admin-session based
- it corroborates the live routing path
- it does not replace the public `POST /v1/chat/completions` integration boundary
- the immediate response and request id appear first, with recorded ledger evidence appearing after persistence

**Pass if:** Playground is clearly treated as corroboration and not as the public adoption target.

### 8. Use Observability as persisted explanation plus dependency-health context

Open Observability after the previous steps and confirm it communicates that:

- the usage ledger is the persisted request evidence surface
- dependency health is supporting runtime context for the same investigation
- dependency health does not replace the ledger record
- the page does not imply separate app/workload admin objects

**Pass if:** Observability closes the proof by explaining persisted request evidence and dependency health without replacing the public route or the ledger-correlation step.

## Final acceptance criteria

Mark this UAT complete only if all of the following are true:

- the walkthrough starts from tenant/API-key production structuring
- the conditional `X-Nebula-Tenant-ID` rule is explained correctly
- the first runtime proof step is the public request on `POST /v1/chat/completions`
- `X-Request-ID` and `X-Nebula-*` headers are captured before admin corroboration begins
- the same request is corroborated in the usage ledger
- Tenants, Playground, and Observability all reinforce the same story without inventing pseudo-entities
- Playground is treated as admin-side corroboration only
- Observability is treated as persisted explanation plus dependency-health context only

## Failure cues

Stop and record a failure if any of these happen:

- a doc or console surface implies app, workload, workspace, or similar pseudo-entities are first-class runtime objects
- `X-Nebula-Tenant-ID` is described as always required
- Playground is treated as the first proof step or the public integration target
- Observability is treated as replacing public headers or ledger evidence
- the usage ledger cannot be tied back to the same `X-Request-ID`
