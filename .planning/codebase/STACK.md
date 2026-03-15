# Technology Stack

**Analysis Date:** 2026-03-15

## Languages

**Primary:**
- Python 3.12+ - All application code under `src/nebula/` and all automated tests under `tests/`

**Secondary:**
- Shell - Local smoke automation in `scripts/smoke_openrouter.sh` and `Makefile` targets
- JSON / JSONL - Benchmark pricing and datasets in `benchmarks/pricing.json` and `benchmarks/v1/scenarios.jsonl`
- YAML - Local infrastructure in `docker-compose.yml`
- Markdown - Operator and developer documentation in `README.md`

## Runtime

**Environment:**
- CPython 3.12+ - Declared in `pyproject.toml` and pinned locally via `.python-version`
- ASGI application runtime - `uvicorn nebula.main:app --reload` serves `src/nebula/main.py`

**Package Manager:**
- `pip` inside a local virtualenv - Driven by `make setup` and `make install` in `Makefile`
- Build backend: `setuptools.build_meta` configured in `pyproject.toml`
- Lockfile: missing

## Frameworks

**Core:**
- FastAPI `>=0.115,<1.0` - HTTP API surface, dependency injection, and lifespan hooks in `src/nebula/main.py`
- Pydantic `>=2.8,<3.0` and `pydantic-settings` `>=2.3,<3.0` - Request/response models and environment-backed settings in `src/nebula/models/*.py` and `src/nebula/core/config.py`
- HTTPX `>=0.27,<1.0` - Async HTTP clients for Ollama and OpenAI-compatible providers in `src/nebula/providers/*.py` and `src/nebula/services/embeddings_service.py`

**Testing:**
- Pytest `>=8.2,<9.0` - Test runner for all files in `tests/`
- pytest-asyncio `>=0.23,<1.0` - Async service tests such as `tests/test_service_flows.py`
- FastAPI `TestClient` - API-level tests such as `tests/test_chat_completions.py`

**Build/Dev:**
- Uvicorn `>=0.30,<1.0` - Local ASGI server
- Ruff `>=0.5,<1.0` - Linting with `line-length = 100` and `target-version = "py312"` in `pyproject.toml`
- Docker Compose - Local Qdrant dependency in `docker-compose.yml`

## Key Dependencies

**Critical:**
- `fastapi` - Request routing and dependency wiring across `src/nebula/api/`
- `pydantic` - OpenAI-compatible payload contracts in `src/nebula/models/openai.py`
- `httpx` - Provider and embedding network transport
- `qdrant-client` - Semantic cache storage in `src/nebula/services/semantic_cache_service.py`
- `prometheus-client` - Metrics endpoint mounted from `src/nebula/main.py`

**Infrastructure:**
- `uvicorn[standard]` - Development server and benchmark-managed subprocesses
- `pydantic-settings` - `.env` loading and startup validation

## Configuration

**Environment:**
- Runtime configuration is centralized in `src/nebula/core/config.py` and loaded from `.env` plus process env vars
- Critical keys include `NEBULA_OLLAMA_BASE_URL`, `NEBULA_QDRANT_URL`, `NEBULA_PREMIUM_PROVIDER`, `NEBULA_PREMIUM_MODEL`, `NEBULA_PREMIUM_BASE_URL`, `NEBULA_PREMIUM_API_KEY`, `NEBULA_ADMIN_API_KEY`, and bootstrap tenant/key settings
- `Settings.validate_premium_provider_settings()` fails fast when `NEBULA_PREMIUM_PROVIDER=openai_compatible` without the required premium credentials

**Build:**
- `pyproject.toml` - Package metadata, test config, Ruff config, setuptools package discovery
- `Makefile` - Developer entrypoints for setup, lint, test, smoke tests, and benchmarks
- `docker-compose.yml` - Local Qdrant service definition

## Platform Requirements

**Development:**
- Python 3.12 with virtualenv support
- Docker for local Qdrant (`make qdrant-up`)
- Ollama with `llama3.2:3b` and `nomic-embed-text` models when exercising local routing and embeddings

**Production:**
- ASGI hosting for `nebula.main:app`
- Reachable Qdrant instance for semantic cache if enabled
- Reachable upstream LLM endpoints: Ollama for local routing and an OpenAI-compatible endpoint when premium routing is enabled
- No deployment manifests are checked in; production packaging is application-only

---

*Stack analysis: 2026-03-15*
*Update after major dependency changes*
