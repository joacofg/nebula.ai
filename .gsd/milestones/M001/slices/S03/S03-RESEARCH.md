# S03: Reference migration integration — Research

**Date:** 2026-03-23

## Summary

S03 owns the active migration-proof requirements: **R004** (prove a realistic app/service can swap direct provider calls for Nebula with minimal code changes) and **R008** (make the reference integration credible enough that engineers trust it). The codebase already contains the core runtime pieces this slice needs: a stable public `POST /v1/chat/completions` path with `X-Nebula-API-Key` auth, response metadata headers, persisted usage-ledger records, and an operator Playground/Observability surface that can corroborate what happened after a request. That means S03 should not invent a new gateway path or a demo-only façade; it should package a believable migration target around the existing public contract and existing operator evidence.

The strongest implementation seam is to build the slice around a **reference app/service integration artifact plus proof harness**, not around new runtime capabilities. The backend already behaves like the OpenAI-compatible target, and the console already demonstrates the operator-side evidence chain. What is missing is a canonical migration example that starts from a direct OpenAI-compatible client call pattern, shows the minimal diff to point that client at Nebula, and then proves the request end to end with both public-path evidence (`X-Nebula-*` headers) and operator-path evidence (`X-Request-ID`/usage ledger). Use the S01/S02 composition rules directly: keep the public contract in `docs/adoption-api-contract.md`, keep operating-model language in `docs/production-model.md`, and make S03 produce the runnable migration proof those docs can point at.

## Recommendation

Take a **targeted documentation + executable proof** approach:

1. Create one realistic reference integration that mirrors a common OpenAI-style chat-completions caller.
2. Keep the migrated code intentionally small so the diff is legible: base URL, auth header, and optional tenant header should be the primary changes.
3. Add focused tests/smoke verification that prove the integration uses the real public route and that Nebula emits both immediate metadata headers and persisted ledger evidence.
4. Wire the new artifact into repo entry docs rather than scattering a second quickstart.

This follows the loaded skill guidance from **react-best-practices** / installed Next.js patterns indirectly only at the level of avoiding framework-specific reinvention: the slice does not need a new UI framework surface. It also follows the S01/S02 rules exactly: do not reopen the contract, do not use Playground as compatibility proof, and do not imply that app/workload are first-class runtime entities. The most credible proof is a small client that behaves like a real adopter would, pointed at the already-tested public path.

## Implementation Landscape

### Key Files

- `src/nebula/api/routes/chat.py` — the canonical public migration target. Confirms that the supported path is `POST /v1/chat/completions` and that routed requests emit `X-Nebula-*` metadata headers.
- `src/nebula/services/chat_service.py` — source of truth for what the reference proof can show on day 1: route target, route reason, provider, cache hit, fallback use, policy mode/outcome, and usage-ledger persistence for both completion and streaming paths.
- `src/nebula/providers/openai_compatible.py` — reveals the shape Nebula already expects/forwards for OpenAI-compatible providers. Useful for choosing a realistic reference caller because the downstream payload remains standard chat-completions JSON.
- `tests/test_chat_completions.py` — best existing evidence for the supported public contract: auth shape, bootstrap-key happy path, OpenAI-like payload, and SSE streaming behavior.
- `tests/test_response_headers.py` — pins the public metadata contract S03 should surface in the proof (local/premium/cache/fallback/denial headers, and no route headers on validation failures).
- `tests/test_governance_api.py` — proves the admin-side evidence chain S03 can reuse after the public call succeeds: request IDs, usage ledger lookup, denied/fallback outcomes, and tenant/policy/API-key setup paths.
- `tests/support.py` — established harness for backend integration-style tests via `configured_app()`, `auth_headers()`, `admin_headers()`, `StubProvider`, and `FakeCacheService`. Best place to mirror existing patterns instead of hand-rolling new fixtures.
- `docs/quickstart.md` — canonical happy path. S03 should consume this flow, not create a competing onboarding path. Reference-integration docs should start after this setup is complete.
- `docs/production-model.md` — runtime truth for tenant/operator/API key boundaries. The reference example must use tenant/API-key reality and keep app/workload conceptual only.
- `README.md` — documentation map. Likely place to add one link to the finished migration proof artifact without restating the contract.
- `scripts/smoke_openrouter.sh` — existing example of an executable proof script. Important pattern: resolve runtime values from config, hit `/v1/chat/completions`, and assert both completion and streaming success. This is the closest existing seam for an S03-style proof harness.
- `src/nebula/api/routes/admin.py` — admin surfaces available for follow-up proof: `/v1/admin/api-keys`, `/v1/admin/usage/ledger`, `/v1/admin/playground/completions`. S03 should use ledger/admin APIs only as corroborating operator evidence, not as the migration target itself.
- `console/src/lib/admin-api.ts` — current UI-facing contract for operator calls. Useful only if S03 adds console-facing pointers or proof copy; it should not become the primary migration example.
- `console/src/app/(console)/playground/page.tsx` — shows the current “immediate response metadata + recorded outcome” product pattern. Good reference if the slice needs a doc screenshot or wording pattern, but not the public integration boundary.
- `console/e2e/playground.spec.ts` and `console/src/components/playground/playground-page.test.tsx` — existing test evidence that operator surfaces already express request-id correlation and recorded outcomes. Reusable for wording and proof expectations, not for public API compatibility.

### Build Order

1. **Choose and define the reference integration artifact first.**
   - Highest-risk question in this slice is credibility, not plumbing. Decide the exact reference target early: it should resemble a direct OpenAI-compatible caller using chat completions, not a toy wrapper.
   - Keep the artifact narrow enough that the migration diff is obvious.

2. **Prove the public-path migration mechanics next.**
   - Show the minimal changes required to move from direct provider usage to Nebula: base URL, `X-Nebula-API-Key`, optional `X-Nebula-Tenant-ID`, and unchanged chat-completions body shape.
   - Reuse backend test patterns/harnesses instead of adding new infrastructure.

3. **Add operator-evidence correlation after the public proof works.**
   - Once the reference integration can call Nebula successfully, prove that the same request can be understood via headers and usage ledger.
   - This unblocks S04 by producing a real request flow with operator-visible evidence.

4. **Only then wire docs/entrypoints.**
   - Add one canonical migration doc/reference section and link to it from README/quickstart if needed.
   - Follow D008: do not duplicate quickstart or contract content.

### Verification Approach

Primary backend verification should stay close to existing patterns:

- `pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_governance_api.py -q`
- Add a focused S03 test module for the new reference integration artifact/harness if the slice introduces code under `examples/`, `scripts/`, or a new docs-backed test fixture.

If the slice uses a runnable script patterned after `scripts/smoke_openrouter.sh`, verify:

- it targets `POST /v1/chat/completions`
- it uses `X-Nebula-API-Key` and, where relevant, `X-Nebula-Tenant-ID`
- success output includes or inspects `X-Nebula-*` response evidence
- the same request can be correlated in `GET /v1/admin/usage/ledger`

If console/docs wiring changes are added, use the existing console verification class:

- `npm --prefix console run test -- --run`
- optionally targeted Playwright coverage if UI copy or proof navigation changes (`make console-e2e` or a targeted spec)

Observable behaviors the slice should prove:

- a realistic client can send a standard chat-completions body to Nebula with minimal caller changes
- routed success returns OpenAI-like JSON plus Nebula metadata headers
- optional streaming remains on the public path if the reference example claims it
- a follow-up admin lookup shows the request persisted in the usage ledger with route/terminal-status evidence
- the docs/reference artifact does not imply Playground is the migration target or that app/workload are runtime entities

## Constraints

- S01 contract is fixed input: `docs/adoption-api-contract.md` remains the only canonical public API contract.
- S02 composition rule is fixed: `docs/quickstart.md` is the only happy-path setup doc and `docs/production-model.md` is the only operating-model reference.
- Runtime truth for M001: tenant, policy, API key, and operator/admin surfaces are real; app and workload are guidance only.
- Public auth is `X-Nebula-API-Key`, not `Authorization: Bearer ...`, so any “minimal diff” example must be honest that header wiring changes.
- Slice-level executable verification still depends on local toolchains being provisioned in the active worktree (`pytest`, console test tooling).

## Common Pitfalls

- **Using Playground as the migration proof** — Playground is admin-only and non-streaming; use it only for operator-side corroboration after the public request.
- **Restating the contract in a second doc** — keep request/response rules in `docs/adoption-api-contract.md`; the S03 artifact should reference it rather than clone it.
- **Over-claiming runtime entities** — do not present app/workload identifiers as enforced product objects.
- **Making the reference app too toy-like** — a tiny diff is good, but the example still needs believable request flow and evidence, not just a one-line curl already covered by quickstart.

## Open Risks

- The repository does not yet show an obvious existing `examples/` reference app for migration proof, so the planner must choose whether S03 should add a small example app, a script-backed reference client, or both.
- If the active worktree still lacks provisioned Python/console tooling, fresh executable verification may again be blocked by environment rather than by slice content.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Next.js | `react-best-practices` | available |
| OpenAI-compatible client integration | `mindrally/skills@openai-api-development` | none found locally; installable suggestion |
| FastAPI | `mindrally/skills@fastapi-python` | none found locally; installable suggestion |

