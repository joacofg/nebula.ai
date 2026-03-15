# Codebase Structure

**Analysis Date:** 2026-03-15

## Directory Layout

```text
nebula/
├── artifacts/                 # Generated benchmark reports
├── benchmarks/                # Pricing catalog and versioned benchmark dataset
├── scripts/                   # Shell smoke tests
├── src/
│   └── nebula/                # Application package
│       ├── api/               # FastAPI dependencies and route modules
│       ├── benchmarking/      # Benchmark runner and dataset helpers
│       ├── core/              # Settings and service container
│       ├── models/            # Pydantic request/response and governance models
│       ├── observability/     # Logging, middleware, Prometheus metrics
│       ├── providers/         # Provider implementations and interfaces
│       └── services/          # Business logic and persistence services
├── tests/                     # Pytest suite and test helpers
├── docker-compose.yml         # Local Qdrant service
├── Makefile                   # Developer commands
├── pyproject.toml             # Python package and tool configuration
└── README.md                  # Project documentation
```

## Directory Purposes

**`src/nebula/api/`:**
- Purpose: HTTP boundary
- Contains: Dependency helpers and route modules
- Key files: `src/nebula/api/routes/chat.py`, `src/nebula/api/routes/admin.py`, `src/nebula/api/dependencies.py`
- Subdirectories: `routes/` only

**`src/nebula/services/`:**
- Purpose: Core application logic
- Contains: Auth, routing, policy, provider registry, governance store, embeddings, semantic cache, chat orchestration
- Key files: `src/nebula/services/chat_service.py`, `src/nebula/services/governance_store.py`
- Subdirectories: none; all services are flat modules

**`src/nebula/providers/`:**
- Purpose: Upstream completion adapters
- Contains: Provider interface and concrete local/premium/mock implementations
- Key files: `src/nebula/providers/base.py`, `src/nebula/providers/ollama.py`, `src/nebula/providers/openai_compatible.py`
- Subdirectories: none

**`src/nebula/core/`:**
- Purpose: App bootstrapping and dependency composition
- Contains: `config.py`, `container.py`
- Key files: `src/nebula/core/config.py`, `src/nebula/core/container.py`
- Subdirectories: none

**`src/nebula/models/`:**
- Purpose: Shared schemas
- Contains: OpenAI-compatible chat models and governance records
- Key files: `src/nebula/models/openai.py`, `src/nebula/models/governance.py`
- Subdirectories: none

**`src/nebula/benchmarking/`:**
- Purpose: CLI benchmark workflow
- Contains: Dataset loading, pricing lookup, benchmark orchestration
- Key files: `src/nebula/benchmarking/run.py`, `dataset.py`, `pricing.py`
- Subdirectories: none

**`tests/`:**
- Purpose: Centralized test tree
- Contains: API, service, provider, health, config, and benchmark tests plus shared stubs/helpers
- Key files: `tests/support.py`, `tests/test_service_flows.py`, `tests/test_governance_api.py`
- Subdirectories: none

## Key File Locations

**Entry Points:**
- `src/nebula/main.py` - FastAPI app factory and module-level `app`
- `src/nebula/benchmarking/run.py` - Benchmark CLI entrypoint

**Configuration:**
- `pyproject.toml` - Package metadata, pytest config, Ruff config
- `.python-version` - Local Python version pin
- `.env.example` - Local environment template
- `docker-compose.yml` - Qdrant local service

**Core Logic:**
- `src/nebula/services/chat_service.py` - Routing, cache, fallback, streaming, and usage recording
- `src/nebula/services/governance_store.py` - SQLite persistence and bootstrap logic
- `src/nebula/services/policy_service.py` - Tenant policy and spend guardrails
- `src/nebula/providers/` - Provider adapters

**Testing:**
- `tests/test_chat_completions.py` - OpenAI-compatible API behavior
- `tests/test_governance_api.py` - Admin and governance flows
- `tests/test_service_flows.py` - Lower-level service behavior with stubs
- `tests/support.py` - Shared app fixture and provider/cache doubles

**Documentation:**
- `README.md` - Developer/operator overview
- `.planning/codebase/*.md` - GSD codebase map once initialized

## Naming Conventions

**Files:**
- `snake_case.py` for Python modules such as `chat_service.py` and `openai_compatible.py`
- `test_*.py` for tests in the centralized `tests/` directory
- `UPPERCASE.md` for planning artifacts inside `.planning/`

**Directories:**
- Lowercase package names (`api`, `services`, `providers`, `models`)
- Flat module collections rather than feature-nested trees inside the Python package

**Special Patterns:**
- `__init__.py` files are minimal and mostly mark packages
- Route modules live in `src/nebula/api/routes/`

## Where to Add New Code

**New API endpoint:**
- Definition: `src/nebula/api/routes/`
- Dependency wiring: `src/nebula/api/dependencies.py` if a new dependency helper is needed
- Tests: `tests/test_<feature>.py` using `TestClient`

**New service logic:**
- Primary code: `src/nebula/services/`
- Shared schema additions: `src/nebula/models/`
- Tests: `tests/test_service_flows.py` for internal flows or a new `tests/test_<service>.py`

**New provider integration:**
- Implementation: `src/nebula/providers/`
- Registration/wiring: `src/nebula/core/container.py` and possibly `src/nebula/services/provider_registry.py`
- Tests: provider-specific test file under `tests/`

**New benchmarking capability:**
- Implementation: `src/nebula/benchmarking/`
- Datasets or pricing: `benchmarks/`
- Output artifacts: `artifacts/benchmarks/`

## Special Directories

**`artifacts/`:**
- Purpose: Generated benchmark outputs
- Source: Created by `src/nebula/benchmarking/run.py`
- Committed: currently present in the repo; treat as generated output

**`.nebula/`:**
- Purpose: Default local runtime data directory for SQLite
- Source: Created at runtime from `NEBULA_DATA_STORE_PATH`
- Committed: no

**`.planning/`:**
- Purpose: GSD project planning state
- Source: Created by GSD initialization workflows
- Committed: yes if `commit_docs` remains enabled

---

*Structure analysis: 2026-03-15*
*Update when directory structure changes*
