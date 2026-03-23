# Reference migration

This document is Nebula's single canonical migration proof for teams moving an existing OpenAI-style chat-completions caller onto Nebula.

Start here only after you have already completed the self-hosted setup in [`docs/quickstart.md`](quickstart.md). Keep [`docs/adoption-api-contract.md`](adoption-api-contract.md) as the canonical public API boundary, and use [`docs/production-model.md`](production-model.md) when you need the operator/app/tenant framing behind the headers and credentials below.

The source of truth for this guide is the executable proof in `tests/test_reference_migration.py`. If code, tests, and prose disagree, treat the test and live runtime behavior as authoritative and update this document.

## What this migration proves

A realistic chat-completions caller can move from a direct OpenAI-compatible endpoint to Nebula with a small, honest integration diff:

- change the base URL to Nebula
- send `X-Nebula-API-Key` instead of provider-specific bearer auth on the public path
- add `X-Nebula-Tenant-ID` only when the API key is intentionally authorized for multiple tenants
- keep the `POST /v1/chat/completions` request body in the same OpenAI-like shape

This guide does **not** redefine setup, contract compatibility, or the full operating model:

- use [`docs/quickstart.md`](quickstart.md) for environment and first-deployment setup
- use [`docs/adoption-api-contract.md`](adoption-api-contract.md) for the supported request/response contract
- use [`docs/production-model.md`](production-model.md) for tenant, operator, API-key, app, and workload boundaries

## Starting assumptions

Before applying the diff below, assume you already have:

- a running Nebula gateway, usually at `http://localhost:8000` in self-hosted development
- a client credential for the public path (`X-Nebula-API-Key`)
- an admin credential for operator inspection (`X-Nebula-Admin-Key`)
- a known tenant only if your API key can reach multiple tenants

If you do not have those yet, go back to [`docs/quickstart.md`](quickstart.md).

## Before

This is a believable direct-provider caller using an OpenAI-compatible chat-completions endpoint.

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url="https://api.openai.com/v1",
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a concise migration assistant."},
        {
            "role": "user",
            "content": "Summarize why this request proves minimal migration.",
        },
    ],
)

print(response.choices[0].message.content)
```

## After

Point the same chat-completions call at Nebula's public endpoint. The main caller changes are base URL and headers.

```python
import os

from openai import OpenAI

client = OpenAI(
    api_key="unused-by-nebula-public-auth",
    base_url="http://localhost:8000/v1",
    default_headers={
        "X-Nebula-API-Key": os.environ["NEBULA_API_KEY"],
        # Only send this when the API key is authorized for multiple tenants.
        # "X-Nebula-Tenant-ID": os.environ["NEBULA_TENANT_ID"],
    },
)

response = client.chat.completions.create(
    model="nebula-auto",
    messages=[
        {"role": "system", "content": "You are a concise migration assistant."},
        {
            "role": "user",
            "content": "Summarize why this request proves minimal migration.",
        },
    ],
)

print(response.choices[0].message.content)
```

## Before/after diff

```diff
 from openai import OpenAI
 
 client = OpenAI(
-    api_key=os.environ["OPENAI_API_KEY"],
-    base_url="https://api.openai.com/v1",
+    api_key="unused-by-nebula-public-auth",
+    base_url="http://localhost:8000/v1",
+    default_headers={
+        "X-Nebula-API-Key": os.environ["NEBULA_API_KEY"],
+        # Optional when the key can access multiple tenants.
+        # "X-Nebula-Tenant-ID": os.environ["NEBULA_TENANT_ID"],
+    },
 )
 
 response = client.chat.completions.create(
-    model="gpt-4o-mini",
+    model="nebula-auto",
     messages=[
         {"role": "system", "content": "You are a concise migration assistant."},
         {
             "role": "user",
             "content": "Summarize why this request proves minimal migration.",
```

## What stayed the same

The migration is intentionally narrow because the request body stays on Nebula's existing public contract:

- same `POST /v1/chat/completions` path
- same `messages` array structure
- same non-streaming `chat.completion` response shape
- same basic caller expectation that `choices[0].message.content` contains the answer

For the exact compatibility boundary, including auth semantics, validation behavior, streaming notes, and unsupported/deferred claims, see [`docs/adoption-api-contract.md`](adoption-api-contract.md).

## When to send X-Nebula-Tenant-ID

Do **not** add `X-Nebula-Tenant-ID` to every request by default.

Send it only when Nebula cannot infer the tenant from the API key alone:

- the API key is authorized for multiple tenants, and
- the request needs to select one of them explicitly

You usually do **not** need it when:

- the key has a single bound `tenant_id`, or
- the key has exactly one `allowed_tenant_ids` entry

The executable proof in `tests/test_reference_migration.py` covers both sides of this behavior:

- the bootstrap-style happy path succeeds with only `X-Nebula-API-Key`
- a deliberately ambiguous multi-tenant key is rejected with `403` until `X-Nebula-Tenant-ID` is supplied

For the runtime explanation behind this rule, see [`docs/production-model.md`](production-model.md).

## How to confirm the migration worked

Do not stop at “the SDK returned text.” Nebula's migration proof is that the same public request is inspectable from both the caller side and the operator side.

### 1. Confirm the public response still looks like chat completions

A successful request should still return an OpenAI-like non-streaming response body, including:

- `object: "chat.completion"`
- `choices[0].message.role == "assistant"`
- a resolved response `model`
- `usage` token counts

That is the application-facing proof that you did not migrate onto a Nebula-specific façade.

### 2. Inspect the X-Nebula-* response headers

Nebula adds public-path evidence headers that tell you what actually happened at runtime. The tested migration proof confirms headers such as:

- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`
- `X-Request-ID`

These headers are the fastest way to tell whether the request reached the expected tenant and whether Nebula routed it to local, cache, or premium execution.

### 3. Correlate the same request in the usage ledger

Use the `X-Request-ID` from the public response to inspect the persisted operator-side record:

```bash
curl "http://localhost:8000/v1/admin/usage/ledger?request_id=<x-request-id>" \
  -H "X-Nebula-Admin-Key: <admin-api-key>"
```

For the reference migration proof, the operator-side confirmation should line up with the public response on at least these fields:

- `request_id`
- `tenant_id`
- `requested_model`
- `final_route_target`
- `final_provider`
- `cache_hit`
- `fallback_used`
- `route_reason`
- `policy_outcome`
- `terminal_status`
- token counts

The migration is only “proved” when the public request and the usage ledger tell the same story.

## Minimal verification path

After migrating one caller, use this exact sanity check sequence:

1. Send one non-streaming `POST /v1/chat/completions` request through Nebula.
2. Confirm the body is still a `chat.completion` payload.
3. Record the `X-Request-ID` and inspect the `X-Nebula-*` headers.
4. Query `GET /v1/admin/usage/ledger?request_id=...` with the admin key.
5. Verify the ledger row matches the public headers and reports a terminal status such as `completed`.

That is the canonical proof path for this migration slice.

## What not to use as migration proof

Do not treat these as substitutes for the public-path migration proof:

- the admin Playground alone
- console login alone
- a handcrafted demo-only curl snippet that does not hit `POST /v1/chat/completions`
- docs that restate the public contract or production model from scratch

Playground remains useful for operator inspection, but it is not the migration target. The migration target is the public `POST /v1/chat/completions` contract.

After this public migration proof succeeds, use [`docs/day-1-value.md`](day-1-value.md) for the canonical operator-visible walkthrough that connects `X-Nebula-*` headers, `X-Request-ID`, Playground corroboration, persisted usage-ledger evidence, and Observability dependency-health context.

## Related docs

- [`docs/quickstart.md`](quickstart.md) — supported setup and first-request flow
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public compatibility boundary
- [`docs/production-model.md`](production-model.md) — canonical tenant/operator/app/workload framing
- `tests/test_reference_migration.py` — executable proof source for this guide
