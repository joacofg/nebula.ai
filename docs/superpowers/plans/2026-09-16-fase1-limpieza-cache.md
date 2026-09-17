# Fase 1 — Limpieza del repo y caché semántico por tenant — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove everything that is not part of the thesis (hosted control plane v2.0, stale planning, orphan benchmark runs), collapse Alembic history into one migration, and make the semantic cache tenant-scoped with the per-tenant threshold and TTL policy knobs actually enforced.

**Architecture:** Deletions first (backend, then console) so the remaining code is small before it is changed. Migrations collapse into a single `Base.metadata`-driven revision so the ORM models are the single schema source. The cache change is contained in `SemanticCacheService` (Qdrant payload filter on `tenant_id` + `created_at` range, per-call `score_threshold`) plus plumbing of two new fields through `PolicyEvaluation`/`PolicyResolution` into `ChatService`. The thesis skeleton is pure Markdown and independent of code.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, qdrant-client (`AsyncQdrantClient`), pytest-asyncio (auto mode), Next.js 15 + vitest, ruff.

**Spec:** `docs/superpowers/specs/2026-09-16-fase1-limpieza-cache.md`

## Global Constraints

- Work on branch `fase-1/limpieza-y-cache` off `main`; one commit per task; PR at the end, merge to `main` after CI is green (user authorised push+merge).
- Python: `make lint` (ruff, `E4,E7,E9,F`, line-length 100) and `make test` must be green after every task. Run tests with `.venv/bin/pytest`.
- Console: `npx tsc --noEmit -p tsconfig.json`, `npm run lint`, `npm run test -- --run` (all from `console/`) must be green after every console task.
- Never touch `scripts/metric_validation/`, `benchmarks/metric-validation/`, `docs/evaluation.md`, `tests/test_metric_validation.py` (the metric study is thesis material).
- Repo language is English for code, comments, commit messages and product docs. Thesis drafts under `docs/tfc/tesis/` are Spanish.
- Commit messages: conventional prefixes (`chore`, `feat`, `fix`, `test`, `docs`) and end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Tests must pass on a machine with no Qdrant and no Ollama running (that is the current property of the suite; keep it).

---

### Task 0: Branch and gitignore fix

**Files:**
- Modify: `.gitignore:108-110`

- [ ] **Step 1: Create the branch**

```bash
cd /Users/joaquinfernandezdegamboa/Proj/nebula
git checkout -b fase-1/limpieza-y-cache main
```

- [ ] **Step 2: Narrow the pending `.gitignore` change**

The working tree already has an uncommitted change that ignores `docs/tfc/` entirely. The thesis Markdown drafts (Task 8) must be tracked, only the Word deliverables and binary assets stay out. Replace the last three lines of `.gitignore` so they read:

```gitignore
# Entregas academicas del Taller de TFC en Word (no forman parte del codigo del producto).
# El Markdown de docs/tfc/tesis/ si se trackea: es la fuente de la tesis.
docs/tfc/*.docx
docs/tfc/assets/
```

- [ ] **Step 3: Verify and commit**

```bash
git check-ignore -v "docs/tfc/TFC-P5-Fernandez de Gamboa, Joaquin.docx"   # prints the rule
git check-ignore -v docs/tfc/tesis/00-indice.md; echo "exit=$? (1 means tracked-able)"
git add .gitignore
git commit -m "chore: ignore only the Word deliverables under docs/tfc

The Markdown thesis drafts that will live in docs/tfc/tesis/ are source and
must be versioned; the .docx files handed to the course are not.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 1: Remove the hosted control plane from the backend

**Files:**
- Delete: `src/nebula/api/routes/enrollment.py`, `src/nebula/api/routes/heartbeat.py`, `src/nebula/api/routes/remote_management.py`
- Delete: `src/nebula/services/enrollment_service.py`, `src/nebula/services/gateway_enrollment_service.py`, `src/nebula/services/heartbeat_ingest_service.py`, `src/nebula/services/heartbeat_service.py`, `src/nebula/services/remote_management_service.py`
- Delete: `src/nebula/models/deployment.py`, `src/nebula/models/heartbeat.py`, `src/nebula/models/hosted_contract.py`
- Delete: `docs/hosted-default-export.schema.json`
- Delete tests: `tests/test_enrollment_api.py`, `tests/test_freshness.py`, `tests/test_gateway_enrollment.py`, `tests/test_heartbeat_api.py`, `tests/test_hosted_contract.py`, `tests/test_remote_management_api.py`, `tests/test_remote_management_audit.py`, `tests/test_remote_management_service.py`
- Modify: `src/nebula/main.py`, `src/nebula/core/container.py`, `src/nebula/core/config.py:61-75`, `src/nebula/db/models.py`, `src/nebula/models/__init__.py`, `src/nebula/api/routes/admin.py`, `tests/test_phase10_outage_safety.py`

**Interfaces:**
- Produces: `ServiceContainer` without `enrollment_service`, `gateway_enrollment_service`, `heartbeat_ingest_service`, `heartbeat_service`, `remote_management_service`. `Settings` without `enrollment_token`, `hosted_plane_url`, `remote_management_enabled`, `remote_management_allowed_actions`, `remote_management_poll_interval_seconds`. `nebula.db.models` exports only `TenantModel`, `TenantPolicyModel`, `ApiKeyModel`, `UsageLedgerModel`.

- [ ] **Step 1: Delete the hosted files**

```bash
cd /Users/joaquinfernandezdegamboa/Proj/nebula
git rm -q src/nebula/api/routes/enrollment.py src/nebula/api/routes/heartbeat.py \
  src/nebula/api/routes/remote_management.py \
  src/nebula/services/enrollment_service.py src/nebula/services/gateway_enrollment_service.py \
  src/nebula/services/heartbeat_ingest_service.py src/nebula/services/heartbeat_service.py \
  src/nebula/services/remote_management_service.py \
  src/nebula/models/deployment.py src/nebula/models/heartbeat.py src/nebula/models/hosted_contract.py \
  docs/hosted-default-export.schema.json \
  tests/test_enrollment_api.py tests/test_freshness.py tests/test_gateway_enrollment.py \
  tests/test_heartbeat_api.py tests/test_hosted_contract.py tests/test_remote_management_api.py \
  tests/test_remote_management_audit.py tests/test_remote_management_service.py
find src -name __pycache__ -type d -exec rm -rf {} +
```

- [ ] **Step 2: Rewrite `src/nebula/main.py`**

Replace the whole file with:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from nebula.api.dependencies import get_container
from nebula.api.routes.admin import router as admin_router
from nebula.api.routes.chat import router as chat_router
from nebula.api.routes.embeddings import router as embeddings_router
from nebula.core.config import get_settings
from nebula.core.container import ServiceContainer
from nebula.observability.logging import configure_logging
from nebula.observability.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    container = ServiceContainer(settings=settings)
    await container.initialize()
    app.state.container = container
    container.retention_lifecycle_service.start()
    try:
        yield {"settings": settings}
    finally:
        await container.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(chat_router, prefix=settings.api_v1_prefix)
    app.include_router(embeddings_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router, prefix=settings.api_v1_prefix)
    if settings.enable_metrics:
        app.mount("/metrics", make_asgi_app())

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> JSONResponse:
        container = get_container(app)
        report = await container.runtime_health_service.readiness()
        status_code = 200 if report["status"] in {"ready", "degraded"} else 503
        return JSONResponse(content=report, status_code=status_code)

    @app.get("/health/dependencies", tags=["health"])
    async def health_dependencies() -> dict[str, object]:
        container = get_container(app)
        return await container.runtime_health_service.readiness()

    return app


app = create_app()
```

- [ ] **Step 3: Edit `src/nebula/core/container.py`**

Remove these imports:

```python
from nebula.services.enrollment_service import EnrollmentService
from nebula.services.gateway_enrollment_service import GatewayEnrollmentService
from nebula.services.heartbeat_ingest_service import HeartbeatIngestService
from nebula.services.heartbeat_service import HeartbeatService
from nebula.services.remote_management_service import RemoteManagementService
```

In `__init__`, delete the blocks that assign `self.enrollment_service`, `self.gateway_enrollment_service`, `self.heartbeat_ingest_service`, `self.heartbeat_service`, `self.remote_management_service`. In `shutdown`, delete the two lines `await self.remote_management_service.stop()` and `await self.heartbeat_service.stop()`. Everything else stays.

- [ ] **Step 4: Edit `src/nebula/core/config.py`**

Delete these five fields (currently lines 61-75):

```python
    enrollment_token: str | None = Field(default=None, alias="NEBULA_ENROLLMENT_TOKEN")
    hosted_plane_url: str | None = Field(default=None, alias="NEBULA_HOSTED_PLANE_URL")
    remote_management_enabled: bool = Field(
        default=False,
        alias="NEBULA_REMOTE_MANAGEMENT_ENABLED",
    )
    remote_management_allowed_actions: list[str] = Field(
        default_factory=list,
        alias="NEBULA_REMOTE_MANAGEMENT_ALLOWED_ACTIONS",
    )
    remote_management_poll_interval_seconds: int = Field(
        default=60,
        alias="NEBULA_REMOTE_MANAGEMENT_POLL_INTERVAL_SECONDS",
    )
```

- [ ] **Step 5: Edit `src/nebula/db/models.py`**

Delete the classes `DeploymentModel`, `EnrollmentTokenModel`, `DeploymentRemoteActionModel`, `LocalHostedIdentityModel`. Then trim the SQLAlchemy import to what remains in use:

```python
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
```

(`Index` was only used by `DeploymentRemoteActionModel`.)

- [ ] **Step 6: Rewrite `src/nebula/models/__init__.py`**

```python
"""Domain and transport models."""

from nebula.models.resilience import (  # noqa: F401
    DependencyClass,
    DependencyHealthReason,
    DependencyLifecycleState,
    ServingEffect,
    build_dependency_health,
    iso_or_none,
)
```

- [ ] **Step 7: Edit `src/nebula/api/routes/admin.py`**

Delete the two route handlers `queue_rotate_credential` and `list_remote_actions` (everything from the `@router.post("/deployments/{deployment_id}/remote-actions/rotate-credential"` decorator to the end of the file). Delete these imports:

```python
from nebula.models.deployment import RemoteActionQueueRequest, RemoteActionRecord
from nebula.services.enrollment_service import (
    DeploymentRemoteActionStateError,
    RemoteActionValidationError,
)
```

Then run `.venv/bin/ruff check src/nebula/api/routes/admin.py` and remove any import it now reports as unused (`Query` is still used by `/usage/ledger`; `HTTPException`/`status` are still used by tenant routes).

- [ ] **Step 8: Trim `tests/test_phase10_outage_safety.py`**

Delete, in this order:
1. The two tests `test_hosted_outage_keeps_chat_completion_serving_and_readiness_green` and `test_stale_and_offline_hosted_visibility_do_not_imply_serving_failure` (from the `@pytest.mark.asyncio` at line 713 to end of file).
2. The helpers `_hosted_outage_transport`, `configured_outage_client`, `_create_active_deployment`, `_session_factory`, `_set_last_seen_at`.
3. The imports `from nebula.db.models import DeploymentModel`, `from nebula.models.deployment import EnrollmentExchangeResponse`, and any of `asynccontextmanager`, `timedelta`, `create_engine`, `sessionmaker`, `httpx`, `FastAPI` that ruff then flags as unused.

If `_install_serving_stubs` was only called from the deleted helpers, delete it too. Run:

```bash
.venv/bin/ruff check tests/test_phase10_outage_safety.py
```

Expected: `All checks passed!`

- [ ] **Step 9: Run the suite and lint**

```bash
make lint && make test
```

Expected: ruff clean; pytest green with roughly 245 tests collected (330 minus the 8 deleted files and 2 deleted tests). If a remaining test imports a deleted module, that test is hosted-only and gets deleted too. Also confirm the app boots:

```bash
.venv/bin/python -c "from nebula.main import app; print(len(app.routes), 'routes')"
```

- [ ] **Step 10: Confirm nothing hosted survives in `src/`**

```bash
grep -rniE "enrollment|heartbeat|remote_management|hosted_plane|deployment" src/nebula --include='*.py'
```

Expected: no output.

- [ ] **Step 11: Commit**

```bash
git add -A src tests docs
git commit -m "chore: remove the hosted control plane from the gateway

The thesis is anchored to the self-hosted gateway. Enrollment, heartbeat,
remote management, the hosted export contract and their four tables leave
the codebase together with their tests.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Remove the hosted control plane from the console

**Files:**
- Delete: `console/src/app/(console)/deployments/` (dir), `console/src/app/trust-boundary/` (dir), `console/src/components/deployments/` (dir), `console/src/components/hosted/` (dir), `console/src/lib/hosted-contract.ts`, `console/src/lib/hosted-contract.test.ts`, `console/src/lib/freshness.ts`, `console/e2e/deployments-proof.spec.ts`, `console/e2e/trust-boundary.spec.ts`
- Modify: `console/src/components/shell/operator-shell.tsx:15-22`, `console/src/components/auth/login-page-client.tsx:60-72`, `console/src/components/policy/policy-form.tsx:14,300,584`, `console/src/components/ledger/ledger-request-detail.tsx:2,383,431-438`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/lib/query-keys.ts:4-5`, `console/src/lib/admin-api.ts:354-478`, `console/src/lib/admin-api.test.ts`

- [ ] **Step 1: Delete the hosted files**

```bash
cd /Users/joaquinfernandezdegamboa/Proj/nebula
git rm -rq "console/src/app/(console)/deployments" console/src/app/trust-boundary \
  console/src/components/deployments console/src/components/hosted \
  console/src/lib/hosted-contract.ts console/src/lib/hosted-contract.test.ts console/src/lib/freshness.ts \
  console/e2e/deployments-proof.spec.ts console/e2e/trust-boundary.spec.ts
```

- [ ] **Step 2: Navigation and login**

In `console/src/components/shell/operator-shell.tsx` delete the line `{ href: "/deployments", label: "Deployments", icon: Server },` and remove `Server` from the `lucide-react` import.

In `console/src/components/auth/login-page-client.tsx` delete the `<Link href="/trust-boundary" ...>...</Link>` block (lines 65-71). Then remove the `Link` and `ShieldCheck` imports if nothing else in the file uses them (check with `grep -n "Link\|ShieldCheck" console/src/components/auth/login-page-client.tsx`).

- [ ] **Step 3: Policy form**

In `console/src/components/policy/policy-form.tsx`:
- delete `import { getHostedContractContent } from "@/lib/hosted-contract";`
- delete `const { copy: hostedContractCopy } = getHostedContractContent();`
- delete `<p>{hostedContractCopy.hostedExportExclusion}</p>`

- [ ] **Step 4: Ledger request detail**

In `console/src/components/ledger/ledger-request-detail.tsx`:
- delete `import { getHostedContractContent } from "@/lib/hosted-contract";`
- delete `const { copy, reinforcement } = getHostedContractContent();`
- replace the `<div className="rounded-2xl border border-border bg-slate-50 px-4 py-4 text-sm text-slate-700">` block that renders the four `reinforcement.evidenceBoundaryVocabulary.*` paragraphs and `copy.hostedExportExclusion` with static copy:

```tsx
        <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4 text-sm text-slate-700">
          <p>
            Retained means the row is still inside its evidence retention window and is the authoritative record
            for this request.
          </p>
          <p className="mt-3">
            Suppressed means a metadata field was minimised at capture time under the tenant policy; it was never
            persisted and cannot be recovered.
          </p>
          <p className="mt-3">
            Deleted means governed retention cleanup removed the row at its expiration time; there is no soft-deleted
            archive.
          </p>
        </div>
```

- in the intro paragraph, replace `before reading broader tenant or hosted posture guidance elsewhere on this page` with `before reading broader tenant guidance elsewhere on this page`, and replace `rather than imply recovery, a soft-deleted archive, or hosted raw export.` with `rather than imply recovery or a soft-deleted archive.`

In `console/src/components/ledger/ledger-request-detail.test.tsx` update the assertions at lines 67, 74, 94 and 99 to the new copy: the two regexes become `/before reading broader tenant guidance elsewhere on this page/` and `/rather than imply recovery or a soft-deleted archive/`; the two exact-text expectations that quote the "Not hosted…" and "Hosted export still excludes…" sentences are deleted (the concept no longer exists).

- [ ] **Step 5: Query keys and admin API**

In `console/src/lib/query-keys.ts` delete the two lines `deployments: ["deployments"] as const,` and `deployment: (id: string) => ["deployment", id] as const,`.

In `console/src/lib/admin-api.ts` delete everything from `export type DeploymentEnvironment = ...` (line 354) through the closing brace of `listRemoteActions` (line 478), i.e. all `Deployment*`, `Enrollment*`, `Freshness*`, `RemoteAction*` types, `ADMIN_DEPLOYMENTS_ENDPOINT`, and the functions `listDeployments`, `createDeployment`, `generateEnrollmentToken`, `revokeDeployment`, `unlinkDeployment`, `queueRotateDeploymentCredential`, `listRemoteActions`.

In `console/src/lib/admin-api.test.ts` delete the whole `describe("admin-api remote actions", ...)` block and the `listRemoteActions`, `queueRotateDeploymentCredential` imports.

- [ ] **Step 6: Verify**

```bash
cd console
npx tsc --noEmit -p tsconfig.json && npm run lint && npm run test -- --run
grep -rniE "hosted|deployment|trust-boundary|enrollment|freshness" src e2e | grep -vi "self-hosted"
```

Expected: tsc silent, eslint clean, vitest green (about 110 tests), and the grep prints nothing. If tsc reports another importer of a deleted module, follow it and delete the dead reference.

- [ ] **Step 7: Commit**

```bash
cd /Users/joaquinfernandezdegamboa/Proj/nebula
git add -A console
git commit -m "chore(console): remove the deployments and trust-boundary surfaces

Follows the backend removal of the hosted control plane. The ledger detail
keeps its evidence vocabulary as static copy instead of reading it from the
deleted hosted contract module.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Collapse Alembic migrations into one initial revision

**Files:**
- Delete: all ten files in `migrations/versions/`
- Create: `migrations/versions/20260916_0001_initial_schema.py`
- Test: `tests/test_initial_migration.py`

**Interfaces:**
- Produces: revision id `20260916_0001`, `down_revision = None`. Schema is exactly `nebula.db.models.Base.metadata` (four tables).

- [ ] **Step 1: Write the failing test**

Create `tests/test_initial_migration.py`:

```python
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from nebula.db.models import Base


def _upgrade(database_url: str) -> None:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def test_single_migration_creates_exactly_the_orm_schema(tmp_path: Path) -> None:
    versions = sorted(p.name for p in (Path(__file__).resolve().parents[1] / "migrations" / "versions").glob("*.py"))
    assert versions == ["20260916_0001_initial_schema.py"]

    database_url = f"sqlite+pysqlite:///{tmp_path / 'fresh.db'}"
    _upgrade(database_url)

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        created = set(inspector.get_table_names()) - {"alembic_version"}
        expected = set(Base.metadata.tables)
        assert created == expected == {"tenants", "tenant_policies", "api_keys", "usage_ledger"}
        for table_name in expected:
            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            model_columns = {column.name for column in Base.metadata.tables[table_name].columns}
            assert actual_columns == model_columns, table_name
    finally:
        engine.dispose()
```

- [ ] **Step 2: Run it to see it fail**

```bash
.venv/bin/pytest tests/test_initial_migration.py -v
```

Expected: FAIL on the `versions == [...]` assertion (ten files present).

- [ ] **Step 3: Delete the old revisions and write the initial one**

```bash
git rm -q migrations/versions/*.py
```

Create `migrations/versions/20260916_0001_initial_schema.py`:

```python
"""initial schema

Revision ID: 20260916_0001
Revises:
Create Date: 2026-09-16 00:00:00.000000

Single baseline derived from ``nebula.db.models.Base``. The ORM models are the
schema's source of truth; ``alembic revision --autogenerate`` builds on top of
this revision for future changes.
"""

from __future__ import annotations

from alembic import op

from nebula.db.models import Base

revision = "20260916_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
```

- [ ] **Step 4: Run the new test and the full suite**

```bash
.venv/bin/pytest tests/test_initial_migration.py -v && make test
```

Expected: all green. `tests/support.py::_run_migrations` already upgrades to head for every `configured_app()`, so the whole suite exercises the new revision.

- [ ] **Step 5: Reset local databases**

```bash
rm -f .nebula/nebula.db
make migrate
.venv/bin/python scripts/seed_demo_data.py --help >/dev/null 2>&1 || true
docker compose -f docker-compose.selfhosted.yml down -v 2>/dev/null || true
```

The compose volumes only hold local demo data; the seed script recreates the `acme-demo` tenant when the stack is next started (see `docs/demo-runbook.md`).

- [ ] **Step 6: Commit**

```bash
git add -A migrations tests/test_initial_migration.py
git commit -m "chore(db): collapse migrations into a single initial revision

Ten revisions, four of them for hosted tables that no longer exist, become
one baseline generated from the ORM metadata. Existing databases must be
recreated; the demo seed script restores the demo tenant.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Tenant-scoped semantic cache with enforced threshold and TTL

**Files:**
- Modify: `src/nebula/services/semantic_cache_service.py`
- Modify: `src/nebula/services/policy_service.py:20-45,86-96` (add fields to `PolicyEvaluation`, `PolicyResolution`, and the `PolicyEvaluation(...)` return at the end of `evaluate`)
- Modify: `src/nebula/services/chat_service.py` (cache lookup/store call sites at lines 113-116, 269, 314-318, 429-455, 490; `_metadata` at 880)
- Modify: `src/nebula/core/config.py:27-30,39`, `.env.example`, `deploy/selfhosted.env.example`, `deploy/selfhosted.env`
- Modify: `tests/support.py:94-135` (`FakeCacheService`), `tests/test_service_flows.py:257,292,334,400`
- Create: `tests/test_semantic_cache_service.py`

**Interfaces:**
- Produces:

```python
@dataclass(slots=True, frozen=True)
class CacheHit:
    response: str
    model: str
    score: float
    age_seconds: int

class SemanticCacheService:
    async def lookup(self, prompt: str, *, tenant_id: str, similarity_threshold: float, max_entry_age_hours: int) -> CacheHit | None: ...
    async def store(self, prompt: str, response: str, model: str, *, tenant_id: str) -> None: ...
```

`PolicyEvaluation` and `PolicyResolution` gain `cache_similarity_threshold: float` and `cache_max_entry_age_hours: int`. `FakeCacheService.lookup_calls` becomes `list[tuple[str, str, float, int]]` = `(tenant_id, prompt, threshold, max_age_hours)`; `stored_entries` becomes `list[tuple[str, str, str, str]]` = `(tenant_id, prompt, response, model)`.

- [ ] **Step 1: Write the failing service tests**

Create `tests/test_semantic_cache_service.py`:

```python
from __future__ import annotations

from time import time
from types import SimpleNamespace

import pytest
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.services.semantic_cache_service import CacheHit, SemanticCacheService


class FakeEmbeddings:
    async def embed(self, text: str) -> list[float] | None:
        return [0.1, 0.2, 0.3]


class RecordingQdrant:
    def __init__(self, points: list[object] | None = None) -> None:
        self.query_kwargs: list[dict] = []
        self.upserts: list[dict] = []
        self.points = points or []

    async def collection_exists(self, name: str) -> bool:
        return True

    async def create_payload_index(self, **kwargs) -> None:
        return None

    async def query_points(self, **kwargs):
        self.query_kwargs.append(kwargs)
        return SimpleNamespace(points=self.points)

    async def upsert(self, **kwargs) -> None:
        self.upserts.append(kwargs)

    async def close(self) -> None:
        return None


def _service(client: RecordingQdrant) -> SemanticCacheService:
    service = SemanticCacheService(settings=Settings(), embeddings_service=FakeEmbeddings())
    service.client = client
    service.enabled = True
    return service


def _must_conditions(kwargs: dict) -> dict[str, qdrant_models.FieldCondition]:
    query_filter = kwargs["query_filter"]
    assert isinstance(query_filter, qdrant_models.Filter)
    return {condition.key: condition for condition in query_filter.must}


@pytest.mark.asyncio
async def test_lookup_filters_by_tenant_and_freshness_and_uses_tenant_threshold() -> None:
    client = RecordingQdrant()
    service = _service(client)

    before = int(time())
    result = await service.lookup(
        "hello", tenant_id="acme", similarity_threshold=0.93, max_entry_age_hours=2
    )

    assert result is None
    kwargs = client.query_kwargs[0]
    assert kwargs["score_threshold"] == 0.93
    conditions = _must_conditions(kwargs)
    assert conditions["tenant_id"].match.value == "acme"
    cutoff = conditions["created_at"].range.gte
    assert before - 2 * 3600 - 2 <= cutoff <= before - 2 * 3600 + 2


@pytest.mark.asyncio
async def test_lookup_returns_hit_with_score_and_age() -> None:
    created_at = int(time()) - 90
    point = SimpleNamespace(
        score=0.97,
        payload={"response": "cached", "model": "llama3.2:3b", "created_at": created_at, "tenant_id": "acme"},
    )
    service = _service(RecordingQdrant(points=[point]))

    hit = await service.lookup("hello", tenant_id="acme", similarity_threshold=0.9, max_entry_age_hours=24)

    assert isinstance(hit, CacheHit)
    assert hit.response == "cached"
    assert hit.model == "llama3.2:3b"
    assert hit.score == pytest.approx(0.97)
    assert 88 <= hit.age_seconds <= 92


@pytest.mark.asyncio
async def test_store_writes_tenant_id_into_payload() -> None:
    client = RecordingQdrant()
    service = _service(client)

    await service.store("hello", "world", "llama3.2:3b", tenant_id="acme")

    payload = client.upserts[0]["points"][0].payload
    assert payload["tenant_id"] == "acme"
    assert payload["prompt"] == "hello"
    assert payload["response"] == "world"
    assert isinstance(payload["created_at"], int)
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/bin/pytest tests/test_semantic_cache_service.py -v
```

Expected: FAIL with `ImportError: cannot import name 'CacheHit'`.

- [ ] **Step 3: Rewrite `SemanticCacheService`**

Replace the imports, add `CacheHit`, and replace `initialize`, `lookup`, `store` in `src/nebula/services/semantic_cache_service.py`. Keep `close` and `health_status` unchanged.

```python
from __future__ import annotations

import logging
from dataclasses import dataclass
from time import time
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from nebula.core.config import Settings
from nebula.models.resilience import DependencyHealthReason, build_dependency_health
from nebula.observability.metrics import CACHE_LOOKUPS
from nebula.services.embeddings_service import OllamaEmbeddingsService

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class CacheHit:
    response: str
    model: str
    score: float
    age_seconds: int


class SemanticCacheService:
    def __init__(
        self,
        settings: Settings,
        embeddings_service: OllamaEmbeddingsService,
    ) -> None:
        self.settings = settings
        self.embeddings_service = embeddings_service
        self.client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            check_compatibility=False,
        )
        self.enabled = False
        self.degraded_reason: str | None = None

    async def initialize(self) -> None:
        collection = self.settings.semantic_cache_collection
        try:
            exists = await self.client.collection_exists(collection)
            if not exists:
                await self.client.create_collection(
                    collection_name=collection,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.settings.embedding_dimensions,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
            # Payload indexes make the tenant/freshness filter cheap. Both calls
            # are idempotent on the Qdrant side.
            await self.client.create_payload_index(
                collection_name=collection,
                field_name="tenant_id",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
            )
            await self.client.create_payload_index(
                collection_name=collection,
                field_name="created_at",
                field_schema=qdrant_models.PayloadSchemaType.INTEGER,
            )
            self.enabled = True
            self.degraded_reason = None
        except Exception as exc:
            logger.warning("semantic_cache_disabled: %s", exc)
            self.enabled = False
            self.degraded_reason = str(exc)

    async def lookup(
        self,
        prompt: str,
        *,
        tenant_id: str,
        similarity_threshold: float,
        max_entry_age_hours: int,
    ) -> CacheHit | None:
        if not self.enabled:
            CACHE_LOOKUPS.labels("disabled").inc()
            return None

        vector = await self.embeddings_service.embed(prompt)
        if vector is None:
            CACHE_LOOKUPS.labels("embedding_unavailable").inc()
            return None

        now = int(time())
        freshness_cutoff = now - max_entry_age_hours * 3600
        query_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="tenant_id",
                    match=qdrant_models.MatchValue(value=tenant_id),
                ),
                qdrant_models.FieldCondition(
                    key="created_at",
                    range=qdrant_models.Range(gte=freshness_cutoff),
                ),
            ]
        )
        try:
            results = await self.client.query_points(
                collection_name=self.settings.semantic_cache_collection,
                query=vector,
                query_filter=query_filter,
                limit=1,
                score_threshold=similarity_threshold,
                with_payload=True,
            )
        except Exception as exc:
            logger.warning("semantic_cache_lookup_failed: %s", exc)
            CACHE_LOOKUPS.labels("error").inc()
            return None

        points = getattr(results, "points", [])
        if not points:
            CACHE_LOOKUPS.labels("miss").inc()
            return None

        point = points[0]
        payload = point.payload or {}
        response = payload.get("response")
        if not isinstance(response, str):
            CACHE_LOOKUPS.labels("miss").inc()
            return None

        CACHE_LOOKUPS.labels("hit").inc()
        created_at = payload.get("created_at")
        age_seconds = now - int(created_at) if isinstance(created_at, int) else 0
        return CacheHit(
            response=response,
            model=str(payload.get("model") or "unknown"),
            score=float(getattr(point, "score", 0.0) or 0.0),
            age_seconds=max(age_seconds, 0),
        )

    async def store(self, prompt: str, response: str, model: str, *, tenant_id: str) -> None:
        if not self.enabled:
            return

        vector = await self.embeddings_service.embed(prompt)
        if vector is None:
            return

        try:
            await self.client.upsert(
                collection_name=self.settings.semantic_cache_collection,
                wait=False,
                points=[
                    qdrant_models.PointStruct(
                        id=str(uuid4()),
                        vector=vector,
                        payload={
                            "tenant_id": tenant_id,
                            "prompt": prompt,
                            "response": response,
                            "model": model,
                            "created_at": int(time()),
                        },
                    )
                ],
            )
        except Exception as exc:
            logger.warning("semantic_cache_store_failed: %s", exc)
```

- [ ] **Step 4: Run the service tests**

```bash
.venv/bin/pytest tests/test_semantic_cache_service.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Plumb the policy knobs through `PolicyEvaluation` and `PolicyResolution`**

In `src/nebula/services/policy_service.py` add two fields to both dataclasses right after `cache_enabled: bool`:

```python
    cache_similarity_threshold: float
    cache_max_entry_age_hours: int
```

In the `return PolicyEvaluation(...)` at the end of `evaluate`, add:

```python
            cache_similarity_threshold=policy.semantic_cache_similarity_threshold,
            cache_max_entry_age_hours=policy.semantic_cache_max_entry_age_hours,
```

In the `return PolicyResolution(...)` in `resolve` (line 86), add:

```python
            cache_similarity_threshold=evaluation.cache_similarity_threshold,
            cache_max_entry_age_hours=evaluation.cache_max_entry_age_hours,
```

Then grep for any other constructor call that must be updated:

```bash
grep -rn "PolicyEvaluation(\|PolicyResolution(" src tests
```

Update every hit found in `src/nebula/services/policy_simulation_service.py` or tests with the two new keyword arguments (use `0.9` and `168` where a test builds one by hand).

- [ ] **Step 6: Update `ChatService`**

In `src/nebula/services/chat_service.py`:

1. Import the hit type: change the import to `from nebula.services.semantic_cache_service import CacheHit, SemanticCacheService`.

2. Replace `_lookup_cache` with:

```python
    async def _lookup_cache(
        self,
        *,
        prompt: str,
        tenant_id: str,
        policy_resolution: PolicyResolution,
        request_id: str | None,
        stream: bool,
    ) -> CacheHit | None:
        if not policy_resolution.cache_enabled:
            logger.info("cache_bypassed request_id=%s stream=%s reason=policy_disabled", request_id, stream)
            return None
        hit = await self.cache_service.lookup(
            prompt,
            tenant_id=tenant_id,
            similarity_threshold=policy_resolution.cache_similarity_threshold,
            max_entry_age_hours=policy_resolution.cache_max_entry_age_hours,
        )
        if hit is not None:
            logger.info(
                "cache_hit request_id=%s stream=%s prompt_chars=%s score=%.4f age_seconds=%s",
                request_id,
                str(stream).lower(),
                len(prompt),
                hit.score,
                hit.age_seconds,
            )
        else:
            logger.info(
                "cache_miss request_id=%s stream=%s prompt_chars=%s",
                request_id,
                str(stream).lower(),
                len(prompt),
            )
        return hit
```

3. At the two call sites (non-streaming ~line 113 and streaming ~line 314) change the call to:

```python
        cache_hit = await self._lookup_cache(
            prompt=latest_user_prompt,
            tenant_id=tenant_context.tenant.id,
            policy_resolution=policy_resolution,
            request_id=request_id,
            stream=False,   # True in the streaming method
        )
        if cache_hit is not None:
            cached_response = cache_hit.response
```

and keep the rest of each block using `cached_response`. In both blocks, pass the score into the metadata by adding `cache_hit=cache_hit` to the `self._metadata(...)` call for the cache branch (see step 4 below).

4. Extend `_metadata` with an optional hit so the score lands in the ledger:

```python
    def _metadata(
        self,
        *,
        tenant_id: str,
        route_target: Literal["local", "premium", "cache", "denied"],
        route_reason: str,
        provider: str,
        cache_hit: bool | CacheHit,
        fallback_used: bool,
        policy_resolution: PolicyResolution,
    ) -> CompletionMetadata:
        signals: dict[str, Any] = dict(policy_resolution.route_decision.signals or {})
        if isinstance(cache_hit, CacheHit):
            signals["cache_similarity_score"] = round(cache_hit.score, 4)
            signals["cache_entry_age_seconds"] = cache_hit.age_seconds
            signals["cache_entry_model"] = cache_hit.model
        return CompletionMetadata(
            tenant_id=tenant_id,
            route_target=route_target,
            route_reason=route_reason,
            provider=provider,
            cache_hit=bool(cache_hit),
            fallback_used=fallback_used,
            policy_mode=policy_resolution.policy_mode,
            policy_outcome=policy_resolution.policy_outcome,
            route_signals=signals or None,
            route_score=policy_resolution.route_decision.score,
        )
```

5. Update the two `store` calls. Non-streaming (line ~269):

```python
        if policy_resolution.cache_enabled:
            await self.cache_service.store(
                latest_user_prompt, result.content, result.model, tenant_id=tenant_context.tenant.id
            )
```

Streaming (line ~490, inside `_prefetched_stream`, which already receives `tenant_id`):

```python
                    if cache_enabled:
                        await self.cache_service.store(
                            prompt, "".join(content_parts), chunk.model, tenant_id=tenant_id
                        )
```

If `_prefetched_stream`'s inner generator does not see `tenant_id` in scope, thread it through the same way `cache_enabled` already is.

- [ ] **Step 7: Update the test double and the four assertions**

In `tests/support.py` replace `FakeCacheService.__init__` attribute types and the two methods:

```python
        self.lookup_calls: list[tuple[str, str, float, int]] = []
        self.stored_entries: list[tuple[str, str, str, str]] = []
```

```python
    async def lookup(
        self,
        prompt: str,
        *,
        tenant_id: str,
        similarity_threshold: float,
        max_entry_age_hours: int,
    ) -> CacheHit | None:
        self.lookup_calls.append((tenant_id, prompt, similarity_threshold, max_entry_age_hours))
        if self.lookup_error is not None:
            raise self.lookup_error
        if self.cached_response is None:
            return None
        return CacheHit(response=self.cached_response, model="nebula-cache", score=1.0, age_seconds=0)

    async def store(self, prompt: str, response: str, model: str, *, tenant_id: str) -> None:
        if self.store_error is not None:
            raise self.store_error
        self.stored_entries.append((tenant_id, prompt, response, model))
```

and add `from nebula.services.semantic_cache_service import CacheHit` to the imports.

In `tests/test_service_flows.py` the four `stored_entries` assertions (lines 257, 292, 334, 400) gain the tenant id as first tuple element. The tenant in those flows is the bootstrap tenant, so e.g. line 334 becomes:

```python
    assert cache_service.stored_entries == [
        (settings.bootstrap_tenant_id, "hello", "fallback response", settings.premium_model)
    ]
```

Apply the same shape to the other three (read each test to confirm which tenant it authenticates as; if it creates its own tenant use that id).

- [ ] **Step 8: Add the isolation and knob tests to `tests/test_service_flows.py`**

Append (reuse the file's existing helpers `configured_app`, `auth_headers`, `admin_headers`, `FakeCacheService`, `StubProvider`, and the module's pattern for mounting stubs onto `app.state.container`; copy the mounting lines from the nearest existing cache test in the file):

```python
@pytest.mark.asyncio
async def test_cache_lookup_is_scoped_to_the_authenticated_tenant_and_its_policy() -> None:
    cache_service = FakeCacheService(cached_response=None)
    with configured_app(NEBULA_PREMIUM_PROVIDER="mock") as app:
        async with app.router.lifespan_context(app):
            container = app.state.container
            container.cache_service = cache_service
            container.chat_service.cache_service = cache_service
            container.provider_registry.local_provider = StubProvider(
                "ollama", completion_result=CompletionResult(content="ok", model="llama", usage=usage())
            )
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as client:
                created = await client.post(
                    "/v1/admin/tenants",
                    json={"id": "tenant-b", "name": "Tenant B"},
                    headers=admin_headers(),
                )
                assert created.status_code == 201
                policy = await client.get("/v1/admin/tenants/tenant-b/policy", headers=admin_headers())
                body = policy.json()
                body["semantic_cache_similarity_threshold"] = 0.95
                body["semantic_cache_max_entry_age_hours"] = 12
                updated = await client.put(
                    "/v1/admin/tenants/tenant-b/policy", json=body, headers=admin_headers()
                )
                assert updated.status_code == 200
                key = await client.post(
                    "/v1/admin/api-keys",
                    json={"name": "b-key", "tenant_id": "tenant-b"},
                    headers=admin_headers(),
                )
                raw_key = key.json()["api_key"]

                response = await client.post(
                    "/v1/chat/completions",
                    json={"model": "nebula-auto", "messages": [{"role": "user", "content": "hi"}]},
                    headers={"X-Nebula-API-Key": raw_key},
                )
                assert response.status_code == 200

    assert cache_service.lookup_calls == [("tenant-b", "hi", 0.95, 12)]
    assert cache_service.stored_entries == [("tenant-b", "hi", "ok", "llama")]
```

Adjust the exact JSON field names for creating a tenant and an API key to what `tests/test_governance_api.py` already uses (search that file for `"/v1/admin/api-keys"` and copy its payload shape). The assertions at the end are the contract.

- [ ] **Step 9: Remove the dead settings**

In `src/nebula/core/config.py` delete the `semantic_cache_threshold` field (lines 27-30) and the `router_complexity_chars` field (line 39). In `.env.example` delete `NEBULA_SEMANTIC_CACHE_THRESHOLD=0.90`, the `# Routing` header and `NEBULA_ROUTER_COMPLEXITY_CHARS=400`. In `deploy/selfhosted.env.example` and `deploy/selfhosted.env` delete `NEBULA_SEMANTIC_CACHE_THRESHOLD=0.90`. Then:

```bash
grep -rn "semantic_cache_threshold\b\|router_complexity_chars\|SEMANTIC_CACHE_THRESHOLD\|ROUTER_COMPLEXITY_CHARS" src tests docs README.md deploy .env.example Makefile
```

Expected: only `tune_semantic_cache_threshold` (a recommendation code, unrelated) remains.

- [ ] **Step 10: Run everything**

```bash
make lint && make test
```

Expected: green. Typical breakage to fix here: a test building `PolicyResolution`/`PolicyEvaluation` by hand without the two new fields, or a `_metadata(...)` call passing `cache_hit=True` (still valid: `bool` is accepted).

- [ ] **Step 11: Commit**

```bash
git add -A src tests .env.example deploy
git commit -m "fix(cache): scope the semantic cache to the tenant and enforce its policy knobs

Every cached point now carries tenant_id and lookups filter on it, so a
response can no longer be served across tenants. The per-tenant similarity
threshold and max entry age that the console already edits are read on
every lookup instead of being ignored, and the hit's similarity score is
persisted in route_signals for later analysis. The global threshold setting
and the unused NEBULA_ROUTER_COMPLEXITY_CHARS are removed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Console copy for the now-live cache knobs

**Files:**
- Modify: `console/src/components/policy/policy-form.tsx` (help text near the two cache inputs), `console/src/components/policy/*.test.tsx` if any assertion quotes the changed copy

- [ ] **Step 1: Find the current copy**

```bash
grep -n "semanticCacheSimilarityThreshold\|semanticCacheMaxEntryAgeHours\|threshold\|entry age" console/src/components/policy/policy-form.tsx | head -30
```

- [ ] **Step 2: Make the help text state the runtime effect**

Under the similarity-threshold input, the helper `<p>` must read: `Minimum cosine similarity a cached answer needs to be served to this tenant. Applied on every lookup.` Under the max-entry-age input: `Cached answers older than this are ignored on lookup for this tenant.` If either input has no helper paragraph, add one with the same classes as the neighbouring helper paragraphs in the form.

- [ ] **Step 3: Verify and commit**

```bash
cd console && npx tsc --noEmit -p tsconfig.json && npm run lint && npm run test -- --run && cd ..
git add console
git commit -m "docs(console): say what the cache threshold and max age actually do

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Benchmark results, planning docs and product docs cleanup

**Files:**
- Create: `benchmarks/results/README.md` plus five copied run directories
- Delete: `.planning/` (7 tracked files), local untracked `ROADMAP.md`, `STATE.md`, 18 orphan run directories under `artifacts/benchmarks/`
- Modify: `README.md`, `docs/architecture.md`, `CLAUDE.md`, `TODOS.md`

- [ ] **Step 1: Preserve the cited benchmark runs in a tracked folder**

```bash
cd /Users/joaquinfernandezdegamboa/Proj/nebula
mkdir -p benchmarks/results
for run in 20260314T193127Z 20260819T225557Z 20260819T225703Z 20260819T225713Z 20260903T143128Z; do
  cp -R "artifacts/benchmarks/$run" "benchmarks/results/$run"
done
for run in artifacts/benchmarks/*/; do
  name=$(basename "$run")
  case "$name" in
    20260314T193127Z|20260819T225557Z|20260819T225703Z|20260819T225713Z|20260903T143128Z) ;;
    *) rm -rf "$run" ;;
  esac
done
ls artifacts/benchmarks   # exactly the five kept runs
```

Create `benchmarks/results/README.md`:

```markdown
# Benchmark results kept for the thesis

`artifacts/benchmarks/` is gitignored: every `make benchmark` writes there and
the directory is disposable. The runs below are the ones cited in docs or in
the thesis, so they are copied here and versioned. Never edit a report in
place; re-run and add a new folder.

| Run | Why it is kept | Headline |
|---|---|---|
| `20260314T193127Z` | Golden v1.0 run referenced by `docs/architecture.md` and `tests/golden/` | 14/14 scenarios passed |
| `20260819T225557Z` | Thesis anchor, run 1 of 3 (same 14 scenarios, healthy dependencies) | 38.2 % premium spend avoided |
| `20260819T225703Z` | Thesis anchor, run 2 of 3 | 40.0 % premium spend avoided |
| `20260819T225713Z` | Thesis anchor, run 3 of 3 | 41.2 % premium spend avoided |
| `20260903T143128Z` | Example of a degraded run carrying the **NOT COMPARABLE** banner (Qdrant down) | not comparable |

The three August runs measure the two-rule heuristic router against a
premium-only baseline. They stop being comparable once the learned router
lands (phase 3); they stay here as the "before" picture.
```

Fix the reference in `docs/architecture.md:71` so it mentions both locations: `under artifacts/benchmarks/<timestamp>/ (disposable) — runs cited by the docs are copied to benchmarks/results/.`

- [ ] **Step 2: Delete stale planning artefacts**

```bash
git rm -rq .planning
rm -f ROADMAP.md STATE.md
```

- [ ] **Step 3: README**

In `README.md`:
- Replace the paragraph at line 13 (`Nebula is self-hosted with an optional hosted control plane. …`) with: `Nebula is self-hosted only. Everything that serves or governs traffic runs inside the operator's environment; no component reports to an external control plane.`
- Delete the whole `## Hosted control plane` section (heading plus its two paragraphs).
- Delete the doc-map bullet for `docs/hosted-default-export.schema.json`.
- Add a doc-map bullet: `- [Evaluation](docs/evaluation.md): the metric-validation study (does cosine similarity track answer quality?) and how the judges were calibrated`.

- [ ] **Step 4: architecture.md**

Delete the `## Hybrid trust boundary` section entirely (heading through the sentence ending `…propagate here.`). Check the doc's table of contents or intro list, if any, for a link to that section and remove it.

- [ ] **Step 5: CLAUDE.md**

Replace the `## v2.0 Context` section with:

```markdown
## Thesis context

Nebula is Joaquín's Trabajo Final de Carrera (Ingeniería Informática, UB). Scope is the self-hosted gateway only; the former hosted control plane was removed in September 2026. Thesis drafts live in `docs/tfc/tesis/` (Markdown, Spanish); course deliverables (`docs/tfc/*.docx`) are not versioned. Plans and specs for the improvement phases live in `docs/superpowers/`. The metric-validation study (`scripts/metric_validation/`, `docs/evaluation.md`) is thesis material: do not modify it without an explicit request.
```

Also delete the line `make selfhost-*` descriptions only if the targets were removed (they were not; leave them).

- [ ] **Step 6: TODOS.md**

Remove any open item that only made sense with the hosted plane (read the three open items; the console/design backlog, the 409-vs-500 admin bug and the dead `budget_penalty` signal all stay).

- [ ] **Step 7: Verify no hosted vocabulary remains and commit**

```bash
grep -rniE "hosted control plane|hosted plane|enrollment|heartbeat|remote.management|trust boundary|hosted-default-export" README.md CLAUDE.md TODOS.md docs/*.md Makefile docker-compose*.yml deploy .env.example
make lint && make test
git add -A benchmarks/results .planning README.md docs/architecture.md CLAUDE.md TODOS.md
git commit -m "docs: drop the hosted-plane narrative and keep the cited benchmark runs

The five benchmark runs referenced by docs and by the thesis move from the
gitignored artifacts/ tree into benchmarks/results/ with an index. Stale
GSD planning files for milestones that no longer exist are removed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Expected grep output: nothing (the phrase "self-hosted" does not match any of those patterns).

---

### Task 7: Thesis skeleton in `docs/tfc/tesis/`

**Files:**
- Create: `docs/tfc/tesis/README.md`, `docs/tfc/tesis/00-indice.md`, `docs/tfc/tesis/01-introduccion.md`, `docs/tfc/tesis/02-marco-teorico.md`, `docs/tfc/tesis/03-estado-del-arte.md`, `docs/tfc/tesis/04-diseno.md`, `docs/tfc/tesis/05-implementacion.md`, `docs/tfc/tesis/06-evaluacion.md`, `docs/tfc/tesis/07-conclusiones.md`, `docs/tfc/tesis/99-bibliografia.md`

- [ ] **Step 1: Create the folder and the index**

`docs/tfc/tesis/README.md`:

```markdown
# Tesis — fuente en Markdown

Cada capítulo es un archivo. Los números y tablas marcados con `<!-- GEN: ... -->`
se regeneran con scripts del repo (`make thesis-tables`, fase 6); no se editan a mano.
Los bloques `> PENDIENTE (fase N)` indican qué fase del plan produce el contenido.

Título fijado por la cátedra: **Enrutamiento inteligente y cacheo semántico multi-proveedor
para reducción de costos en gateways de LLM self-hosted**.

Objetivos específicos aprobados (TP4): OE1 relevamiento y estándar de referencia; OE2 diseño e
implementación del enrutamiento y consola operativa; OE3 medición de calidad (similitud semántica)
y benchmarks; OE4 documentación y conclusiones.
```

`docs/tfc/tesis/00-indice.md`:

```markdown
# Índice

1. [Introducción](01-introduccion.md) — problema, hipótesis, objetivos, alcance
2. [Marco teórico](02-marco-teorico.md) — LLM, costos por token, embeddings, caché semántico, enrutamiento de modelos, evaluación con jueces LLM
3. [Estado del arte](03-estado-del-arte.md) — RouteLLM, FrugalGPT, GPTCache, LiteLLM, Portkey, OpenRouter
4. [Diseño](04-diseno.md) — arquitectura del gateway, política por tenant, caché, router de tres niveles, frontera costo/calidad
5. [Implementación](05-implementacion.md) — stack, componentes, consola, decisiones de ingeniería
6. [Evaluación](06-evaluacion.md) — metodología, corpus, jueces, resultados, amenazas a la validez
7. [Conclusiones](07-conclusiones.md) — contribuciones, limitaciones, trabajo futuro
8. [Bibliografía](99-bibliografia.md)
```

- [ ] **Step 2: Write each chapter skeleton**

`01-introduccion.md`:

```markdown
# 1. Introducción

## 1.1 Contexto y problema
Las organizaciones que integran LLM pagan por token a proveedores premium aun cuando una fracción
relevante de sus pedidos podría resolverse con modelos locales o con una respuesta ya generada.
Un gateway self-hosted que decide por pedido a qué nivel enviarlo permite recortar ese gasto sin
ceder el control operativo.

## 1.2 Hipótesis
Un gateway con enrutamiento aprendido de tres niveles y caché semántico por tenant reduce el gasto
premium en al menos un 35 % respecto de enviar todo a un proveedor premium, manteniendo una tasa de
respuestas aceptables para un lector no inferior a la del nivel premium económico.

> PENDIENTE (fase 3): fijar el umbral de calidad exacto una vez medida la frontera.

## 1.3 Objetivos
OE1–OE4 según TP4 (ver README).

## 1.4 Alcance y límites
Self-hosted únicamente. Proveedores premium vía OpenRouter. Corpus bilingüe (es/en) de dominio
general. Sin aprendizaje en línea.

## 1.5 Estructura del documento
```

`02-marco-teorico.md`:

```markdown
# 2. Marco teórico

## 2.1 Modelos de lenguaje y costo por token
## 2.2 Modelos locales cuantizados (Ollama, GGUF)
## 2.3 Embeddings y similitud coseno
## 2.4 Caché semántico: admisión, aislamiento, TTL
## 2.5 Enrutamiento de modelos: heurísticas, cascadas, routers aprendidos
## 2.6 Evaluación de calidad con jueces LLM: sesgos de posición, familia y severidad
## 2.7 Métricas de acuerdo: κ de Cohen, α de Krippendorff, AUC

> PENDIENTE (fase 6): redacción completa; las definiciones de 2.7 ya están implementadas en
> `scripts/metric_validation/stats.py`.
```

`03-estado-del-arte.md`:

```markdown
# 3. Estado del arte

| Sistema | Tipo | Enrutamiento | Caché | Cifra publicada | Fuente |
|---|---|---|---|---|---|
| RouteLLM (LMSYS, 2024) | router aprendido | MF / BERT / causal LLM | no | hasta 85 % menos costo con 95 % de la calidad de GPT-4 en MT-Bench | Ong et al. 2024 |
| FrugalGPT (Stanford, 2023) | cascada | scorer por respuesta | sí (prompt) | hasta 98 % menos costo igualando GPT-4 | Chen et al. 2023 |
| GPTCache | caché semántico | no | sí | — | repo zilliztech |
| LiteLLM | proxy | reglas/fallback | sí (exacto y semántico) | — | docs |
| Portkey | gateway comercial | reglas condicionales | sí | — | docs |
| OpenRouter Auto Router | router hospedado | propietario (NotDiamond) | no | — | docs |

> PENDIENTE (fase 6): verificar cada cifra contra la fuente primaria y completar columnas.
> Decisión de diseño de la tesis: no se corren benchmarks de terceros; se comparan cifras publicadas.

## 3.1 Qué no cubre ninguno de los anteriores
Aislamiento por tenant del caché con política operable, frontera costo/calidad visible y ajustable
por el operador, y validación de los jueces contra un lector humano.
```

`04-diseno.md`:

```markdown
# 4. Diseño

## 4.1 Arquitectura del gateway
Flujo: cliente → `/v1/chat/completions` → resolución de política por tenant → caché → router →
proveedor → cabeceras `X-Nebula-*` → ledger.

## 4.2 Política por tenant
Modo de ruteo, modelos premium permitidos, presupuestos blando y duro, caché (habilitado, umbral
de similitud, antigüedad máxima), fallback, captura de evidencia.

## 4.3 Caché semántico por tenant
Punto en Qdrant = embedding(prompt) + payload {tenant_id, prompt, response, model, created_at}.
Lookup filtra por tenant y por `created_at ≥ ahora − TTL`, con `score_threshold` de la política.
(Implementado en fase 1.)

## 4.4 Router de tres niveles
> PENDIENTE (fase 3): clasificador sobre embedding, salida = probabilidad de aceptabilidad por
> nivel, umbral operable = punto de la frontera.

## 4.5 Frontera costo/calidad
> PENDIENTE (fase 3/4).
```

`05-implementacion.md`:

```markdown
# 5. Implementación

## 5.1 Stack
FastAPI + Python 3.12, PostgreSQL 16, Qdrant, Ollama, Next.js 15 (consola).

## 5.2 Componentes del backend
> PENDIENTE (fase 6): tabla de módulos con responsabilidad y líneas.

## 5.3 Consola de operación
> PENDIENTE (fase 4).

## 5.4 Decisiones de ingeniería relevantes
- Fail-open del caché y del embedding (el gateway sigue sirviendo sin Qdrant/Ollama).
- Banner NOT COMPARABLE en benchmarks con dependencias degradadas.
- Migración única derivada de los modelos ORM (fase 1).
```

`06-evaluacion.md`:

```markdown
# 6. Evaluación

## 6.1 Preguntas de investigación
RQ1 ¿Cuánto gasto premium evita cada estrategia de ruteo a igual calidad?
RQ2 ¿La similitud coseno sirve como métrica de calidad? (estudio de validación: no, AUC 0.25)
RQ3 ¿Cuánto se aproximan los jueces LLM a un lector humano, en inglés y en español?
RQ4 ¿Cómo cambia la frontera con el tamaño del modelo local (3B vs 7B)?

## 6.2 Corpus
> PENDIENTE (fase 2): origen público, estratificación por tarea, traducción, tamaño.

## 6.3 Jueces y validación contra humanos
Antecedente ya medido: sobre 22 pares en inglés, sustituibles según gpt-4o-mini 32 %, gemini-2.5-flash 68 %,
lector humano 91 % (p = 1.2e-4). <!-- GEN: judge-vs-human -->
> PENDIENTE (fase 2): ensamble, rúbrica "lector satisfecho", 50 pares en español.

## 6.4 Resultados de ruteo
Línea de base (heurística de dos reglas, 14 escenarios, 2026-08-19): 38.2 / 40.0 / 41.2 % de gasto
premium evitado. <!-- GEN: baseline-savings -->
> PENDIENTE (fase 3): curva costo/calidad del router aprendido vs heurística.

## 6.5 Amenazas a la validez
```

`07-conclusiones.md`:

```markdown
# 7. Conclusiones

## 7.1 Contribuciones
## 7.2 Limitaciones
## 7.3 Trabajo futuro
- Aprendizaje en línea del router a partir de muestreo juzgado en producción.
- Cascada local→premium con juez en línea.
- Proveedores nativos adicionales.

> PENDIENTE (fase 6).
```

`99-bibliografia.md`:

```markdown
# Bibliografía

- Ong, I. et al. (2024). *RouteLLM: Learning to Route LLMs with Preference Data.* arXiv:2406.18665.
- Chen, L., Zaharia, M., Zou, J. (2023). *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance.* arXiv:2305.05176.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685.
- Bang, F. (2023). *GPTCache: An Open-Source Semantic Cache for LLM Applications.* NLP-OSS.
- Krippendorff, K. (2011). *Computing Krippendorff's Alpha-Reliability.*

> PENDIENTE: completar a medida que se cite.
```

- [ ] **Step 3: Verify tracking and commit**

```bash
git add docs/tfc/tesis
git status --short docs/tfc   # only tesis/*.md staged; .docx not listed
git commit -m "docs(tesis): add the thesis chapter skeleton in Spanish

Each chapter marks which phase of the plan fills it; numbers already
measured (judge-vs-human, baseline savings) are quoted with GEN markers so
they can be regenerated by script later.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: End-to-end smoke, PR and merge

**Files:** none new

- [ ] **Step 1: Full verification**

```bash
cd /Users/joaquinfernandezdegamboa/Proj/nebula
make lint && make test
cd console && npx tsc --noEmit -p tsconfig.json && npm run lint && npm run test -- --run && cd ..
grep -rniE "enrollment|heartbeat|remote_management|hosted_plane|hosted control|trust-boundary" src console/src docs README.md CLAUDE.md | grep -vi "self-hosted"
```

Expected: all green, grep empty.

- [ ] **Step 2: Live smoke against real dependencies (only if Docker is running)**

```bash
docker compose up -d qdrant
rm -f .nebula/nebula.db && make migrate
(make run &) ; sleep 4
.venv/bin/python scripts/seed_demo_data.py
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health/ready
make benchmark-demo
pkill -f "uvicorn nebula.main:app"
```

Expected: `/health/ready` returns 200; `benchmark-demo` report has no NOT COMPARABLE banner and the warm scenarios show `cache_hit`. If Ollama is not running, skip the benchmark and record that in the PR description.

- [ ] **Step 3: Push, open PR, merge**

```bash
git push -u origin fase-1/limpieza-y-cache
gh pr create --title "Fase 1: remove the hosted plane, collapse migrations, tenant-scoped cache" --body "$(cat <<'EOF'
## Summary
- Remove the v2.0 hosted control plane from backend, console, tests and docs.
- Collapse ten Alembic revisions into one initial schema derived from the ORM models.
- Semantic cache: tenant-scoped lookups, per-tenant similarity threshold and max entry age enforced, similarity score persisted in route_signals.
- Keep the five cited benchmark runs under benchmarks/results/ with an index; drop stale planning files.
- Add the Spanish thesis chapter skeleton under docs/tfc/tesis/.

Spec: docs/superpowers/specs/2026-09-16-fase1-limpieza-cache.md
Plan: docs/superpowers/plans/2026-09-16-fase1-limpieza-cache.md

## Test plan
- [ ] make lint && make test
- [ ] console: tsc, eslint, vitest
- [ ] live smoke: migrate on empty DB, seed demo, /health/ready 200, benchmark-demo with cache hits

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
gh pr checks --watch
gh pr merge --squash --delete-branch
git checkout main && git pull
```

---

## Self-review

**Spec coverage**
- A (hosted removal backend/console/docs/tests) → Tasks 1, 2, 6. ✔
- B (collapse migrations) → Task 3. ✔
- C (tenant cache, threshold, TTL, score in ledger, dead settings) → Task 4; console copy → Task 5. ✔
- D (benchmark results) → Task 6 step 1. ✔
- E (thesis skeleton, gitignore) → Tasks 0 and 7. ✔
- Acceptance criteria 1–5 → Task 8 steps 1–2 (criterion 5, the demo, is exercised by the seed + benchmark-demo smoke).

**Type consistency**
- `CacheHit(response, model, score, age_seconds)` is used identically in Task 4 steps 1, 3, 6, 7.
- `lookup(prompt, *, tenant_id, similarity_threshold, max_entry_age_hours)` and `store(prompt, response, model, *, tenant_id)` match between service, fake, and chat service.
- `FakeCacheService.lookup_calls` tuple order `(tenant_id, prompt, threshold, max_age_hours)` matches the assertion in Task 4 step 8; `stored_entries` `(tenant_id, prompt, response, model)` matches steps 7 and 8.
- Revision id `20260916_0001` matches file name and test.
