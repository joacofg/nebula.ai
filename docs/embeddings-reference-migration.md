# Embeddings reference migration

This document is Nebula's canonical migration proof for teams moving an existing OpenAI-style embeddings caller onto Nebula.

Start here only after you have already completed the self-hosted setup in [`docs/self-hosting.md`](self-hosting.md). Keep [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md) as the canonical public API boundary, and use this guide only for the narrow before/after migration proof.

The source of truth for this guide is the executable proof in `tests/test_embeddings_reference_migration.py`. If code, tests, and prose disagree, treat the test and live runtime behavior as authoritative and update this document.

## What this migration proves

A believable embeddings caller can move from a direct provider path to Nebula with a small, honest integration diff:

- change the base URL to Nebula
- keep using the OpenAI Python client
- send `X-Nebula-API-Key` on the public path
- keep the `POST /v1/embeddings` request body inside Nebula's supported `model` plus string-or-flat-list `input` contract
- confirm the request from both the public response and the persisted metadata-only usage ledger

This guide does **not** redefine the detailed embeddings contract, broaden auth claims, or promise API parity beyond what the tests prove. For the exact boundary, exclusions, and failure semantics, use [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md).

## Starting assumptions

Before applying the diff below, assume you already have:

- a running Nebula gateway, usually at `http://localhost:8000` in self-hosted development
- a client credential for the public path (`X-Nebula-API-Key`)
- an admin credential for operator inspection (`X-Nebula-Admin-Key`)
- an existing embeddings caller that already uses the OpenAI Python client against a direct provider endpoint

If you do not have Nebula running yet, go back to [`docs/self-hosting.md`](self-hosting.md).

## Before

This is a believable direct-provider caller using the OpenAI Python client against an OpenAI-compatible embeddings endpoint.

```python
import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url="https://api.openai.com/v1",
)

response = client.embeddings.create(
    model="nomic-embed-text",
    input=[
        "minimal migration keeps the provider-style request body",
        "only the base URL and auth header change",
    ],
)

print(response.data[0].embedding)
```

## After

Point the same embeddings call at Nebula's public endpoint. The caller change stays narrow: base URL, placeholder client `api_key`, and `default_headers={"X-Nebula-API-Key": ...}`.

```python
import os

from openai import OpenAI

client = OpenAI(
    api_key="unused-by-nebula-public-auth",
    base_url="http://localhost:8000/v1",
    default_headers={
        "X-Nebula-API-Key": os.environ["NEBULA_API_KEY"],
    },
)

response = client.embeddings.create(
    model="nomic-embed-text",
    input=[
        "minimal migration keeps the provider-style request body",
        "only the base URL and auth header change",
    ],
)

print(response.data[0].embedding)
```

## Before/after diff

```diff
 import os
 
 from openai import OpenAI
 
 client = OpenAI(
-    api_key=os.environ["OPENAI_API_KEY"],
-    base_url="https://api.openai.com/v1",
+    api_key="unused-by-nebula-public-auth",
+    base_url="http://localhost:8000/v1",
+    default_headers={
+        "X-Nebula-API-Key": os.environ["NEBULA_API_KEY"],
+    },
 )
 
 response = client.embeddings.create(
     model="nomic-embed-text",
     input=[
```

## What stayed the same

The migration is intentionally narrow because the request body and application-facing usage pattern stay close to the direct-provider caller:

- same OpenAI Python client
- same `client.embeddings.create(...)` call shape
- same `model`
- same flat list of input strings
- same expectation that the response contains an ordered `data` list with embedding vectors

For the exact supported request/response boundary, auth semantics, and excluded options such as `encoding_format`, see [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md).

## How to confirm the migration worked

Do not stop at "the SDK returned vectors." Nebula's migration proof is that the same public request is inspectable from both the caller side and the operator side.

### 1. Confirm the public response still looks like embeddings

A successful request should still return an OpenAI-like embeddings payload, including:

- `object: "list"`
- `data` entries shaped like embeddings objects with `index` and `embedding`
- the resolved `model`
- `usage` with the currently tested embeddings fields

That is the application-facing proof that the caller stayed on an OpenAI-like embeddings shape rather than switching to a Nebula-specific helper abstraction.

### 2. Inspect `X-Request-ID` and the `X-Nebula-*` headers

Nebula adds public-path evidence headers that tell you what happened at runtime. The executable proof confirms:

- `X-Request-ID`
- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

These headers are the fastest way to confirm that the request reached Nebula's public `/v1/embeddings` route and completed on the direct embeddings path.

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

The tested boundary is metadata-only. The ledger evidence should help you correlate the request, but it should **not** expose raw `input` strings or returned embedding vectors.

Observability is a secondary operator surface for this same durable row, not a replacement proof source. After you confirm the `X-Request-ID` and query `GET /v1/admin/usage/ledger?request_id=...`, you can open the Observability page, filter to `Route target = embeddings`, and inspect the matching request id plus route/outcome metadata as UI corroboration of that ledger record.

## Minimal verification path

After migrating one caller, use this exact sanity-check sequence:

1. Send one `POST /v1/embeddings` request through Nebula with `X-Nebula-API-Key`.
2. Confirm the body still looks like an OpenAI-style embeddings response.
3. Record `X-Request-ID` and inspect the `X-Nebula-*` headers.
4. Query `GET /v1/admin/usage/ledger?request_id=...` with the admin key.
5. Verify the ledger row matches the public evidence and remains metadata-only.
6. Run `tests/test_embeddings_reference_migration.py` when you need the repo's executable source of truth.

That is the canonical proof path for this migration slice.

## What not to use as migration proof

Do not treat these as substitutes for the public-path migration proof:

- a direct provider request that never hits Nebula's `POST /v1/embeddings`
- bearer-auth examples that replace `X-Nebula-API-Key`
- examples that add unsupported request options such as `encoding_format`
- helper SDK wrappers that hide the actual public request shape
- docs or dashboards alone without `X-Request-ID` plus usage-ledger correlation
- admin evidence that suggests raw `input` values or returned embeddings are persisted

The migration target is the public `POST /v1/embeddings` contract proved by `tests/test_embeddings_reference_migration.py`, not a broader parity claim.

## Related docs

- [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md) — canonical public compatibility boundary and exclusions
- [`docs/self-hosting.md`](self-hosting.md) — supported deployment path before trying the migration
- [`docs/architecture.md`](architecture.md) — high-level request flow and operator evidence model
- `tests/test_embeddings_reference_migration.py` — executable proof source for this guide
