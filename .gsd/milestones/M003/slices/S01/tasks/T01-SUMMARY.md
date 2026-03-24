---
id: T01
parent: S01
milestone: M003
provides:
  - Narrow OpenAI-style embeddings schemas and an explicit batch-aware Ollama embeddings service contract for the future public `/v1/embeddings` route.
key_files:
  - src/nebula/models/openai.py
  - src/nebula/services/embeddings_service.py
  - tests/test_service_flows.py
  - .gsd/milestones/M003/slices/S01/S01-PLAN.md
key_decisions:
  - Added explicit embeddings service exceptions for validation, upstream HTTP failure, and empty upstream results while keeping the legacy `embed()` helper backward-compatible for semantic cache callers.
patterns_established:
  - New public-surface runtime behavior should expose typed, test-locked failure branches internally before API routing maps them into HTTP responses.
observability_surfaces:
  - `pytest tests/test_service_flows.py -k embedding`; `pytest tests/test_service_flows.py -k 'embedding and (blank or upstream or empty)'`; explicit `EmbeddingsValidationError`, `EmbeddingsUpstreamError`, and `EmbeddingsEmptyResultError` branches in `src/nebula/services/embeddings_service.py`
duration: 1h
verification_result: passed
completed_at: 2026-03-23T23:16:43-03:00
blocker_discovered: false
---

# T01: Extend embeddings internals for the public narrow contract

**Added narrow embeddings schemas, a batch-aware model-passthrough embeddings service, and focused failure-path tests that make blank/upstream/empty-result behavior explicit.**

## What Happened

I first fixed the slice-plan observability gap by adding an explicit failure-path verification command to `.gsd/milestones/M003/slices/S01/S01-PLAN.md`.

Then I extended `src/nebula/models/openai.py` with a narrow `EmbeddingsRequest` model that accepts only `model` plus `input` as either a string or a flat list of strings, and with `EmbeddingsResponse`/`EmbeddingData` models for the standard float-vector response shape.

In `src/nebula/services/embeddings_service.py` I replaced the old single-string implicit-model helper behavior with a richer internal contract: `create_embeddings(model=..., input=...)` now supports single and batch inputs, forwards the caller-supplied model to Ollama, preserves output ordering through stable indexes, and raises explicit service exceptions for blank input, upstream HTTP failures, and empty or malformed embedding payloads. I preserved `embed(text)` for existing semantic-cache callers by delegating to the new method and collapsing those explicit errors back to `None` only on the compatibility path.

Finally, I added focused coverage in `tests/test_service_flows.py` for request-model validation, single-input model passthrough, batch ordering, blank-input rejection, upstream HTTP failure, and empty-upstream-embedding rejection.

## Verification

I bootstrapped the project environment with `make setup` because the worktree initially had no usable `pytest` on PATH. After that, I ran the task-level verification and the new slice-level failure-path check via the repo-root virtualenv interpreter.

Both commands passed, confirming the narrow embeddings request validation, model passthrough, batch ordering, and explicit service failure signals.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_service_flows.py -k embedding` | 127 | ❌ fail | ~0s |
| 2 | `make setup` | 0 | ✅ pass | 18.3s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding` | 0 | ✅ pass | 0.80s |
| 4 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k 'embedding and (blank or upstream or empty)'` | 0 | ✅ pass | 0.57s |

## Diagnostics

Future agents can inspect the service behavior directly in `src/nebula/services/embeddings_service.py` via the `EmbeddingsValidationError`, `EmbeddingsUpstreamError`, and `EmbeddingsEmptyResultError` branches.

The fastest regression check is:

- `pytest tests/test_service_flows.py -k embedding`
- `pytest tests/test_service_flows.py -k 'embedding and (blank or upstream or empty)'`

These tests cover the intended model passthrough, ordered batch mapping, and the three explicit failure classes added in this task.

## Deviations

I amended `.gsd/milestones/M003/slices/S01/S01-PLAN.md` before implementation to add the missing inspectable failure-path verification command required by the task pre-flight instructions.

## Known Issues

The shell environment in this worktree did not expose `pytest` directly, so verification currently relies on the repo-root virtualenv interpreter path created by `make setup`.

## Files Created/Modified

- `src/nebula/models/openai.py` — added narrow embeddings request/response schemas and strict input validation.
- `src/nebula/services/embeddings_service.py` — added batch-aware embeddings creation, caller-model passthrough, ordered result mapping, and explicit failure exceptions while preserving `embed()` compatibility.
- `tests/test_service_flows.py` — added focused embeddings request/service tests for happy paths and explicit failure branches.
- `.gsd/milestones/M003/slices/S01/S01-PLAN.md` — added a slice-level failure-path verification command for observability coverage.
