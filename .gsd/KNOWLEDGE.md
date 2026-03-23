# Knowledge

- S01 / API contract: Treat `docs/adoption-api-contract.md` as the only canonical public compatibility boundary. Update README and architecture docs by linking back to it rather than restating request/response details in multiple places.
- S01 / Validation behavior: `ChatCompletionRequest` now enforces the "at least one user message" invariant at schema-validation time, so invalid requests return FastAPI's native 422 `detail` payload and do not emit route-level `X-Nebula-*` headers.
- S01 / Test alignment: The admin Playground is an admin-only, non-streaming operator surface that can route differently from the public adoption path for the same requested model. Do not assume Playground responses should mirror public-route provider selection.
- S01 / Header assertions: For routed denials and fallback-blocked paths, assert that `X-Nebula-Policy-Outcome` is present and meaningful rather than hard-coding a specific string unless the runtime contract explicitly guarantees that exact value.
