# Fase 5 — Rate limiting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Per-tenant requests-per-minute limit on the public chat and embeddings endpoints.
**Spec:** `docs/superpowers/specs/2026-09-30-fase5-rate-limiting.md`

## Global Constraints
Branch `fase5-rate-limit`; tests without network; `darwin-throttle` for suites; commit trailers as in previous phases; default behaviour unchanged when the field is `None`.

## Review Focus
1. Streaming responses carry the rate-limit headers. 2. A denied request never reaches the router, cache or provider. 3. Lowering the limit mid-minute takes effect immediately. 4. Clock skew / negative elapsed never grants tokens above capacity. 5. Ledger minimisation (`metadata_minimization_level=strict`) still works on the new row.

### Task 1: token bucket (`services/rate_limiter.py`) — tests: burst, refill, cap, isolation, reconfigure, retry-after.
### Task 2: policy field + migration 0003 + store mapping + options — tests: round-trip, 422 out of range, migration.
### Task 3: enforcement dependency on chat (stream + non-stream) and embeddings, headers, ledger row, metric — API tests.
### Task 4: console policy field — vitest.
### Task 5: docs (architecture, self-hosting note on single process), full gates, review, PR, merge, memory.
