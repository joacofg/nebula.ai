# Coding Conventions

**Analysis Date:** 2026-03-15

## Naming Patterns

**Files:**
- Use `snake_case.py` for source modules such as `router_service.py`, `openai_compatible.py`, and `test_governance_api.py`
- Keep tests in the root `tests/` directory with `test_*.py` names
- Use package markers and optional re-exports through minimal `__init__.py` files

**Functions:**
- Use `snake_case` for all functions and methods
- Async functions do not get a special prefix; examples include `create_completion_with_metadata()` and `stream_complete()`
- Helper methods are often prefixed with `_` inside classes for internal use

**Variables:**
- Use `snake_case` for locals and attributes
- Use `UPPER_SNAKE_CASE` for module constants such as `API_KEY_HEADER` and Prometheus metric objects
- No private-member underscore convention on instance attributes beyond helper methods

**Types:**
- Use `PascalCase` for Pydantic models and dataclasses such as `ChatCompletionRequest`, `TenantPolicy`, and `PolicyResolution`
- Literal aliases such as `RoutingMode` and `RouteTarget` are also `PascalCase`

## Code Style

**Formatting:**
- Ruff is the only explicit style tool configured in `pyproject.toml`
- Maximum line length is 100 characters
- String literals predominantly use double quotes
- Type hints are expected throughout application and test code
- `from __future__ import annotations` is used in many modules that benefit from forward references

**Linting:**
- Run `.venv/bin/ruff check .` or `make lint`
- No formatter configuration is present; preserve existing whitespace and import grouping when editing

## Import Organization

**Order:**
1. Standard library imports
2. Third-party packages
3. Internal `nebula.*` imports
4. Test-local imports in test modules

**Grouping:**
- Separate groups with blank lines
- Keep imports explicit instead of wildcard imports
- Relative imports are rare; package-qualified imports like `from nebula.services...` are preferred

**Path Aliases:**
- No alias system is configured
- Pytest adds `src` to `PYTHONPATH` via `pyproject.toml`

## Error Handling

**Patterns:**
- Raise `HTTPException` for request/auth/policy failures at API-facing boundaries
- Wrap transport failures in `ProviderError` in provider modules
- Catch provider failures in `ChatService` to record usage and decide whether fallback is allowed
- Use early returns for cache hits and guard conditions

**Error Types:**
- Use validation exceptions from Pydantic for settings/model validation
- Return normal values for cache misses or optional behavior; do not raise for unavailable cache in `SemanticCacheService`
- Log with context around provider failures, cache failures, and route selection

## Logging

**Framework:**
- Python standard `logging`
- Levels used in code: `info` and `warning`, configured through `NEBULA_LOG_LEVEL`

**Patterns:**
- Log at request, routing, provider, and cache boundaries
- Include request and tenant context when available
- Avoid ad-hoc `print()` statements in committed code

## Comments

**When to Comment:**
- Comments are sparse; prefer readable types and method names over inline commentary
- Add comments only when behavior is subtle, especially around streaming or persistence edges

**Docstrings:**
- Not a prevailing pattern in the mapped modules
- Match the existing style unless introducing a public API that truly benefits from a docstring

**TODO Comments:**
- No active `TODO`, `FIXME`, or `HACK` markers were detected in `src/` or `tests/`

## Function Design

**Size:**
- Most modules favor small-to-medium helper methods, but `ChatService` and `GovernanceStore` already contain large orchestration methods
- When extending those files, prefer extracting private helpers rather than growing the main methods further

**Parameters:**
- Constructor injection is the dominant pattern for services
- Public methods use explicit keyword-heavy signatures when many inputs are needed

**Return Values:**
- Use typed return values, including unions like `ChatCompletionResponse | StreamingResponse`
- Dataclasses are used for internal envelopes instead of loose dicts

## Module Design

**Exports:**
- Each module owns a concrete concern; cross-module access is usually through direct imports, not barrels
- Keep provider/service interfaces narrow and explicit

**Barrel Files:**
- `__init__.py` files exist but are not used as heavy export hubs
- Prefer importing the concrete module you need rather than expanding package-level indirection

---

*Convention analysis: 2026-03-15*
*Update when patterns change*
