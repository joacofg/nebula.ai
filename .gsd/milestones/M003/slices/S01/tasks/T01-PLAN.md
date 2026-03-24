---
estimated_steps: 5
estimated_files: 3
skills_used:
  - test
---

# T01: Extend embeddings internals for the public narrow contract

**Slice:** S01 — Public embeddings endpoint
**Milestone:** M003

## Description

Build the runtime foundation that makes the public embeddings endpoint truthful. The existing embeddings helper only supports a single string and silently uses the configured default model, so this task must add the narrow public schema and extend the internal service to support caller-supplied `model` plus ordered flat batch input. Keep the contract intentionally strict per D015: no broad parameter parity, no chat-service reuse, and no hidden fallback to unsupported shapes.

## Steps

1. Add narrow OpenAI-style embeddings models to `src/nebula/models/openai.py`, including request validation for `input` as either a string or a flat list of strings and response models for standard float-vector embeddings payloads.
2. Extend `src/nebula/services/embeddings_service.py` so the service accepts a requested model and either one string or a flat list of strings, forwards that shape to Ollama, preserves response ordering, and returns a deterministic result structure the API route can map directly.
3. Decide and codify the service failure behavior for blank input, empty upstream embeddings, and upstream HTTP failures so the later route can translate them into intentional API outcomes instead of silent `None` ambiguity.
4. Add focused service tests in `tests/test_service_flows.py` that prove model passthrough, single-input and batch-input ordering, and failure-path behavior without requiring the full FastAPI stack.
5. Keep the scope tight: support only `input` + `model` for string or flat list input, and do not add optional OpenAI embeddings parameters beyond what S01 explicitly promises.

## Must-Haves

- [ ] `src/nebula/models/openai.py` contains narrow embeddings request/response models that match the S01 contract and reject unsupported input shapes.
- [ ] `src/nebula/services/embeddings_service.py` can embed both a single string and a simple batch while honoring the caller-supplied model.
- [ ] `tests/test_service_flows.py` includes real assertions covering happy-path ordering and at least one failure-path signal for embeddings behavior.

## Verification

- `pytest tests/test_service_flows.py -k embedding`
- Confirm the new tests fail if model passthrough or batch ordering is broken.

## Observability Impact

- Signals added/changed: service-level failure behavior becomes explicit and test-locked instead of returning ambiguous `None` for all failure classes.
- How a future agent inspects this: run `pytest tests/test_service_flows.py -k embedding` and inspect `src/nebula/services/embeddings_service.py` for the exact blank/upstream failure branches.
- Failure state exposed: upstream HTTP failures, blank input rejection, and empty-embedding responses become distinguishable service outcomes for the API layer.

## Inputs

- `src/nebula/services/embeddings_service.py` — current single-string helper that ignores the caller model.
- `src/nebula/models/openai.py` — existing public OpenAI-style schema module where embeddings models should live.
- `tests/test_service_flows.py` — existing fast service-level test file that can host focused embeddings coverage.

## Expected Output

- `src/nebula/services/embeddings_service.py` — updated embeddings runtime supporting model passthrough and simple batch input.
- `src/nebula/models/openai.py` — new narrow embeddings request/response schemas.
- `tests/test_service_flows.py` — embeddings-focused unit/service assertions proving the runtime contract.
