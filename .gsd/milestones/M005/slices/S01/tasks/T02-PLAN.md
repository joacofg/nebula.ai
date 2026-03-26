---
task: T02
title: Add route_signals to ledger and wire through chat_service
wave: 1
depends_on:
  - T01
files_modified:
  - src/nebula/db/models.py
  - src/nebula/models/governance.py
  - src/nebula/services/governance_store.py
  - src/nebula/services/chat_service.py
  - src/nebula/api/routes/chat.py
  - migrations/versions/20260326_0006_route_signals.py
requirements:
  - R039
autonomous: true
---

# T02: Add route_signals to ledger and wire through chat_service

## Goal

Persist `RouteDecision.signals` to a new `route_signals` JSON column on `usage_ledger` via a new Alembic migration, thread the signals through `CompletionMetadata`, extend `_nebula_headers()` with a `X-Nebula-Route-Score` header, and update the admin API's TypeScript type contract.

## Must-Haves

- New Alembic migration `20260326_0006_route_signals.py` adds `route_signals JSON NULL` to `usage_ledger` with idempotent guard
- `UsageLedgerModel` and `UsageLedgerRecord` both carry `route_signals`
- `CompletionMetadata` carries `route_signals: dict[str, Any] | None` and `route_score: float`
- `ChatService._metadata()` populates `route_signals` and `route_score` from `RouteDecision`
- `ChatService._record_usage()` writes `route_signals` to the ledger record
- `_nebula_headers()` emits `X-Nebula-Route-Score` as a string-formatted float
- `GovernanceStore.record_usage()` and `_usage_from_model()` handle the new column

## Tasks

<task id="1">
<title>Add route_signals column to DB models, Pydantic record, and Alembic migration</title>
<read_first>
- src/nebula/db/models.py — full file; note line 6 already imports JSON from sqlalchemy; UsageLedgerModel starts at line 144
- src/nebula/models/governance.py — UsageLedgerRecord starts at line 88; note existing fields up to policy_outcome at line 105
- migrations/versions/20260322_0005_remote_actions.py — idempotent migration pattern to replicate exactly
- migrations/versions/20260315_0001_governance_baseline.py — understand revision chain to set down_revision correctly
</read_first>
<action>
**Step 1 — Add SQLAlchemy column to `UsageLedgerModel` in `src/nebula/db/models.py`:**

After line 164 (`policy_outcome: Mapped[str | None] = mapped_column(Text(), nullable=True)`), add:

```python
route_signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

The `JSON` type is already imported at line 6: `from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text`.

**Step 2 — Add Pydantic field to `UsageLedgerRecord` in `src/nebula/models/governance.py`:**

`UsageLedgerRecord` currently ends with `policy_outcome: str | None = None` (line 105). Add after it:

```python
route_signals: dict[str, Any] | None = None
```

Also add `Any` to the import — the top of `governance.py` already has `from typing import Any, Literal` so no import change is needed.

**Step 3 — Create Alembic migration `migrations/versions/20260326_0006_route_signals.py`:**

```python
"""Add route_signals JSON column to usage_ledger.

Revision ID: 20260326_0006
Revises: 20260322_0005
Create Date: 2026-03-26 00:06:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260326_0006"
down_revision = "20260322_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("usage_ledger")}
    if "route_signals" not in columns:
        op.add_column("usage_ledger", sa.Column("route_signals", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("usage_ledger")}
    if "route_signals" in columns:
        op.drop_column("usage_ledger", "route_signals")
```
</action>
<acceptance_criteria>
- `grep -n "route_signals" src/nebula/db/models.py` — returns a line with `mapped_column(JSON, nullable=True)`
- `grep -n "route_signals" src/nebula/models/governance.py` — returns a line `route_signals: dict[str, Any] | None = None`
- `ls migrations/versions/20260326_0006_route_signals.py` exits 0
- `grep -n "down_revision" migrations/versions/20260326_0006_route_signals.py` returns `down_revision = "20260322_0005"`
- `grep -n "route_signals.*not in columns" migrations/versions/20260326_0006_route_signals.py` returns the idempotent guard line
</acceptance_criteria>
</task>

<task id="2">
<title>Wire route_signals and route_score through CompletionMetadata, _record_usage, _metadata, and headers</title>
<read_first>
- src/nebula/services/chat_service.py — read lines 42-52 (CompletionMetadata), lines 832-895 (_record_usage and _metadata); understand every call site of _metadata() by searching for `self._metadata(`
- src/nebula/services/governance_store.py — read record_usage() at lines 272-296 and _usage_from_model() (search for `def _usage_from_model`)
- src/nebula/api/routes/chat.py — full file; _nebula_headers() is lines 51-61
</read_first>
<action>
**Step 1 — Extend `CompletionMetadata` in `src/nebula/services/chat_service.py`:**

Current `CompletionMetadata` (lines 42-52):
```python
@dataclass(slots=True)
class CompletionMetadata:
    tenant_id: str
    route_target: Literal["local", "premium", "cache", "denied"]
    route_reason: str
    provider: str
    cache_hit: bool
    fallback_used: bool
    policy_mode: str
    policy_outcome: str
```

Add two fields at the end:
```python
    route_signals: dict[str, Any] | None = None
    route_score: float = 0.0
```

Also add `Any` to the imports at the top of `chat_service.py`. Currently line 8 has `from typing import AsyncIterator, Literal` — change to `from typing import Any, AsyncIterator, Literal`.

**Step 2 — Update `_metadata()` method (line 875) to populate new fields from `PolicyResolution.route_decision`:**

```python
def _metadata(
    self,
    *,
    tenant_id: str,
    route_target: Literal["local", "premium", "cache", "denied"],
    route_reason: str,
    provider: str,
    cache_hit: bool,
    fallback_used: bool,
    policy_resolution: PolicyResolution,
) -> CompletionMetadata:
    return CompletionMetadata(
        tenant_id=tenant_id,
        route_target=route_target,
        route_reason=route_reason,
        provider=provider,
        cache_hit=cache_hit,
        fallback_used=fallback_used,
        policy_mode=policy_resolution.policy_mode,
        policy_outcome=policy_resolution.policy_outcome,
        route_signals=policy_resolution.route_decision.signals or None,
        route_score=policy_resolution.route_decision.score,
    )
```

Note: for cache_hit and denial paths, `route_reason="cache_hit"` and the policy_resolution may have an empty-signals RouteDecision. The `or None` coercion on `{}` to `None` keeps the ledger clean for non-heuristic routes.

**Step 3 — Update `_record_usage()` (line 832) to include `route_signals` in the ledger record:**

Inside `self.governance_store.record_usage(UsageLedgerRecord(...))`, add after `policy_outcome=metadata.policy_outcome`:
```python
route_signals=metadata.route_signals,
```

**Step 4 — Update `GovernanceStore.record_usage()` in `src/nebula/services/governance_store.py`:**

Inside `record_usage()` (lines 272-296), update the `session.add(UsageLedgerModel(...))` call to include:
```python
route_signals=record.route_signals,
```

**Step 5 — Update `GovernanceStore._usage_from_model()` to read the new column:**

Find the `_usage_from_model` method (search for `def _usage_from_model`). It currently constructs a `UsageLedgerRecord`. Add the new field:
```python
route_signals=row.route_signals,
```

**Step 6 — Extend `_nebula_headers()` in `src/nebula/api/routes/chat.py`:**

Add a new header to the dict:
```python
"X-Nebula-Route-Score": f"{metadata.route_score:.4f}",
```

The existing headers remain unchanged. This adds exactly one header, consistent with "keeps header count stable" (new informational companion, not replacing existing).
</action>
<acceptance_criteria>
- `grep -n "route_signals" src/nebula/services/chat_service.py` — returns at least 3 matches: CompletionMetadata field, _metadata() assignment, _record_usage() assignment
- `grep -n "route_score" src/nebula/services/chat_service.py` — returns at least 2 matches: CompletionMetadata field and _metadata() assignment
- `grep -n "from typing import" src/nebula/services/chat_service.py` — returned line includes `Any`
- `grep -n "route_signals" src/nebula/services/governance_store.py` — returns at least 2 matches (record_usage and _usage_from_model)
- `grep -n "X-Nebula-Route-Score" src/nebula/api/routes/chat.py` — returns 1 match
- `pytest tests/test_chat_completions.py tests/test_admin.py -x` exits 0
</acceptance_criteria>
</task>

## Verification

```
pytest tests/test_chat_completions.py tests/test_admin.py tests/test_governance.py -x
```

All existing tests pass. Migration file exists and chains correctly from `20260322_0005`.

## Success Criteria

- `migrations/versions/20260326_0006_route_signals.py` exists with idempotent `ADD COLUMN` guard
- `UsageLedgerModel.route_signals` (SQLAlchemy), `UsageLedgerRecord.route_signals` (Pydantic), `CompletionMetadata.route_signals` (dataclass) all present
- `CompletionMetadata.route_score: float = 0.0` present
- `GovernanceStore.record_usage()` and `_usage_from_model()` handle `route_signals`
- `X-Nebula-Route-Score` header emitted by `_nebula_headers()`
- Full test suite green
