# Testing Patterns

**Analysis Date:** 2026-03-15

## Test Framework

**Runner:**
- Pytest `>=8.2,<9.0`
- Config lives in `pyproject.toml` under `[tool.pytest.ini_options]`
- Async tests use `asyncio_mode = "auto"`

**Assertion Library:**
- Built-in `assert` statements and `pytest.raises`
- FastAPI endpoint assertions use response status/body/header checks

**Run Commands:**
```bash
make test                               # Run the full suite
.venv/bin/pytest                        # Run all tests directly
.venv/bin/pytest tests/test_health.py   # Run a single file
.venv/bin/pytest -k fallback            # Run matching tests
```

## Test File Organization

**Location:**
- All tests live under `tests/`
- Shared doubles and helpers live in `tests/support.py`

**Naming:**
- API and behavior tests use `test_<feature>.py`
- There is no separate `integration/` or `e2e/` tree; API and service tests share the same directory

**Structure:**
```text
tests/
├── support.py
├── test_benchmarking.py
├── test_chat_completions.py
├── test_governance_api.py
├── test_health.py
├── test_ollama_provider.py
├── test_openai_compatible_provider.py
├── test_response_headers.py
├── test_service_flows.py
└── test_settings.py
```

## Test Structure

**Suite Organization:**
```python
def test_chat_completions_returns_openai_like_payload() -> None:
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        with TestClient(app) as client:
            # arrange runtime overrides
            response = client.post("/v1/chat/completions", ...)

    assert response.status_code == 200
    assert response.headers["X-Nebula-Provider"] == "ollama"
```

**Patterns:**
- Prefer plain test functions over test classes
- Use context-managed app setup via `configured_app()` in `tests/support.py`
- Arrange runtime overrides by mutating `app.state.container`
- Assert concrete headers, body fields, and ledger states rather than broad snapshots

## Mocking

**Framework:**
- Hand-rolled fakes and stubs, not `unittest.mock`
- Main doubles: `StubProvider`, `FakeCacheService`, and the app factory helper in `tests/support.py`

**Patterns:**
```python
container.local_provider = StubProvider(
    "ollama",
    completion_result=CompletionResult(...),
)
container.provider_registry.local_provider = container.local_provider
container.cache_service = FakeCacheService()
container.chat_service.cache_service = container.cache_service
```

**What to Mock:**
- External providers and cache infrastructure
- Runtime environment variables through `configured_app(**env_overrides)`
- Benchmark server behavior via managed subprocesses when needed

**What NOT to Mock:**
- FastAPI routing and response serialization in API tests
- Internal policy and governance behavior when the test is meant to validate end-to-end request flow

## Fixtures and Factories

**Test Data:**
- Use helper constructors instead of pytest fixtures for most shared setup
- `tests/test_service_flows.py` defines in-file helper objects like `FakeGovernanceStore`, `FakePolicyService`, and `tenant_context()`
- `tests/support.py` provides reusable auth headers, admin headers, usage helpers, and provider/cache doubles

**Location:**
- Cross-test helpers: `tests/support.py`
- Feature-specific helpers: inline within the relevant test module

## Coverage

**Requirements:**
- No explicit coverage threshold is configured
- `pytest-cov` is installed but no dedicated coverage command is defined in `Makefile`

**Configuration:**
- Coverage appears optional/ad hoc
- Focus is on behavior-rich tests for API, provider, policy, and fallback paths

## Test Types

**Unit Tests:**
- Examples: `tests/test_settings.py`, `tests/test_ollama_provider.py`, `tests/test_openai_compatible_provider.py`
- Scope: single module or class with direct assertions and minimal runtime setup

**Integration Tests:**
- Examples: `tests/test_chat_completions.py`, `tests/test_governance_api.py`, `tests/test_response_headers.py`
- Scope: full FastAPI app with container wiring, overridden providers, and real request handling

**Service Flow Tests:**
- Example: `tests/test_service_flows.py`
- Scope: `ChatService` behavior with fake store/cache/providers and async assertions

**E2E / Smoke Tests:**
- Shell-based smoke coverage exists in `scripts/smoke_openrouter.sh`
- These are not part of the pytest suite and rely on a running local environment

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_create_completion_falls_back_to_premium_when_local_provider_fails() -> None:
    response = await service.create_completion(...)
    assert response.model == settings.premium_model
```

**Error Testing:**
```python
with pytest.raises(ValidationError, match="NEBULA_PREMIUM_API_KEY is required"):
    Settings(...)
```

**Streaming Testing:**
- For API tests, use `TestClient.stream(...)` and join `response.iter_bytes()`
- For service tests, consume the async iterator and assert raw SSE bytes

**Snapshot Testing:**
- Not used

---

*Testing analysis: 2026-03-15*
*Update when test patterns change*
