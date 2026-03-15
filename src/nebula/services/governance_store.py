from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import uuid4

from nebula.core.config import Settings
from nebula.models.governance import (
    ApiKeyRecord,
    TenantPolicy,
    TenantRecord,
    UsageLedgerRecord,
)


@dataclass(slots=True, frozen=True)
class StoredApiKey:
    id: str
    name: str
    key_hash: str
    key_prefix: str
    tenant_id: str | None
    allowed_tenant_ids: list[str]
    revoked_at: str | None
    created_at: str
    updated_at: str

    def to_record(self) -> ApiKeyRecord:
        return ApiKeyRecord(
            id=self.id,
            name=self.name,
            key_prefix=self.key_prefix,
            tenant_id=self.tenant_id,
            allowed_tenant_ids=self.allowed_tenant_ids,
            revoked_at=self.revoked_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class GovernanceStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.path = Path(settings.data_store_path)
        self._lock = RLock()
        self.connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        with self._lock:
            self.connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tenant_policies (
                    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                    routing_mode_default TEXT NOT NULL,
                    allowed_premium_models_json TEXT NOT NULL,
                    semantic_cache_enabled INTEGER NOT NULL,
                    fallback_enabled INTEGER NOT NULL,
                    max_premium_cost_per_request REAL,
                    soft_budget_usd REAL,
                    prompt_capture_enabled INTEGER NOT NULL DEFAULT 0,
                    response_capture_enabled INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL UNIQUE,
                    key_prefix TEXT NOT NULL,
                    tenant_id TEXT REFERENCES tenants(id) ON DELETE SET NULL,
                    allowed_tenant_ids_json TEXT NOT NULL,
                    revoked_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS usage_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    requested_model TEXT NOT NULL,
                    final_route_target TEXT NOT NULL,
                    final_provider TEXT,
                    fallback_used INTEGER NOT NULL,
                    cache_hit INTEGER NOT NULL,
                    response_model TEXT,
                    prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    completion_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    estimated_cost REAL,
                    latency_ms REAL,
                    timestamp TEXT NOT NULL,
                    terminal_status TEXT NOT NULL,
                    route_reason TEXT,
                    policy_outcome TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_usage_ledger_tenant_timestamp
                ON usage_ledger (tenant_id, timestamp DESC);
                """
            )
            self.connection.commit()
        self.ensure_bootstrap()

    def close(self) -> None:
        if self.connection is None:
            return
        self.connection.close()
        self.connection = None

    def ensure_bootstrap(self) -> None:
        self.create_tenant(
            tenant_id=self.settings.bootstrap_tenant_id,
            name=self.settings.bootstrap_tenant_name,
            description="Bootstrap workspace for local development and smoke tests.",
            metadata={"bootstrap": True},
            active=True,
            policy=self.default_policy(),
            upsert=True,
        )
        self.ensure_api_key(
            raw_key=self.settings.bootstrap_api_key,
            name=self.settings.bootstrap_api_key_name,
            tenant_id=self.settings.bootstrap_tenant_id,
            allowed_tenant_ids=[self.settings.bootstrap_tenant_id],
        )

    def default_policy(self) -> TenantPolicy:
        return TenantPolicy(allowed_premium_models=[self.settings.premium_model])

    def list_tenants(self) -> list[TenantRecord]:
        rows = self._execute("SELECT * FROM tenants ORDER BY id").fetchall()
        return [self._tenant_from_row(row) for row in rows]

    def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        row = self._execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
        return self._tenant_from_row(row) if row else None

    def create_tenant(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str | None,
        metadata: dict[str, object],
        active: bool,
        policy: TenantPolicy | None = None,
        upsert: bool = False,
    ) -> TenantRecord:
        now = self._now()
        statement = """
            INSERT INTO tenants (id, name, description, metadata_json, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            tenant_id,
            name,
            description,
            json.dumps(metadata),
            int(active),
            now,
            now,
        )
        if upsert:
            statement += """
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    metadata_json = excluded.metadata_json,
                    active = excluded.active,
                    updated_at = excluded.updated_at
            """
        self._execute(statement, params)
        self._commit()
        resolved_policy = policy or self.default_policy()
        self.upsert_policy(tenant_id, resolved_policy)
        tenant = self.get_tenant(tenant_id)
        assert tenant is not None
        return tenant

    def update_tenant(
        self,
        tenant_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, object] | None = None,
        active: bool | None = None,
    ) -> TenantRecord | None:
        current = self.get_tenant(tenant_id)
        if current is None:
            return None
        updated = {
            "name": name if name is not None else current.name,
            "description": description if description is not None else current.description,
            "metadata_json": json.dumps(metadata if metadata is not None else current.metadata),
            "active": int(active if active is not None else current.active),
            "updated_at": self._now(),
            "tenant_id": tenant_id,
        }
        self._execute(
            """
            UPDATE tenants
            SET name = :name,
                description = :description,
                metadata_json = :metadata_json,
                active = :active,
                updated_at = :updated_at
            WHERE id = :tenant_id
            """,
            updated,
        )
        self._commit()
        return self.get_tenant(tenant_id)

    def get_policy(self, tenant_id: str) -> TenantPolicy:
        row = self._execute(
            "SELECT * FROM tenant_policies WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchone()
        if row is None:
            policy = self.default_policy()
            self.upsert_policy(tenant_id, policy)
            return policy
        return TenantPolicy(
            routing_mode_default=row["routing_mode_default"],
            allowed_premium_models=json.loads(row["allowed_premium_models_json"]),
            semantic_cache_enabled=bool(row["semantic_cache_enabled"]),
            fallback_enabled=bool(row["fallback_enabled"]),
            max_premium_cost_per_request=row["max_premium_cost_per_request"],
            soft_budget_usd=row["soft_budget_usd"],
            prompt_capture_enabled=bool(row["prompt_capture_enabled"]),
            response_capture_enabled=bool(row["response_capture_enabled"]),
        )

    def upsert_policy(self, tenant_id: str, policy: TenantPolicy) -> TenantPolicy:
        self._execute(
            """
            INSERT INTO tenant_policies (
                tenant_id,
                routing_mode_default,
                allowed_premium_models_json,
                semantic_cache_enabled,
                fallback_enabled,
                max_premium_cost_per_request,
                soft_budget_usd,
                prompt_capture_enabled,
                response_capture_enabled,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tenant_id) DO UPDATE SET
                routing_mode_default = excluded.routing_mode_default,
                allowed_premium_models_json = excluded.allowed_premium_models_json,
                semantic_cache_enabled = excluded.semantic_cache_enabled,
                fallback_enabled = excluded.fallback_enabled,
                max_premium_cost_per_request = excluded.max_premium_cost_per_request,
                soft_budget_usd = excluded.soft_budget_usd,
                prompt_capture_enabled = excluded.prompt_capture_enabled,
                response_capture_enabled = excluded.response_capture_enabled,
                updated_at = excluded.updated_at
            """,
            (
                tenant_id,
                policy.routing_mode_default,
                json.dumps(policy.allowed_premium_models),
                int(policy.semantic_cache_enabled),
                int(policy.fallback_enabled),
                policy.max_premium_cost_per_request,
                policy.soft_budget_usd,
                int(policy.prompt_capture_enabled),
                int(policy.response_capture_enabled),
                self._now(),
            ),
        )
        self._commit()
        return self.get_policy(tenant_id)

    def create_api_key(
        self,
        *,
        name: str,
        tenant_id: str | None,
        allowed_tenant_ids: list[str],
        raw_key: str | None = None,
    ) -> tuple[ApiKeyRecord, str]:
        if tenant_id is None and not allowed_tenant_ids:
            raise ValueError("API keys must be bound to at least one tenant.")
        resolved_allowed_tenant_ids = allowed_tenant_ids or ([tenant_id] if tenant_id else [])
        for allowed_tenant_id in resolved_allowed_tenant_ids:
            if self.get_tenant(allowed_tenant_id) is None:
                raise ValueError(f"Unknown tenant: {allowed_tenant_id}")
        if tenant_id and self.get_tenant(tenant_id) is None:
            raise ValueError(f"Unknown tenant: {tenant_id}")

        now = self._now()
        secret = raw_key or f"nbk_{secrets.token_urlsafe(24)}"
        self._execute(
            """
            INSERT INTO api_keys (
                id,
                name,
                key_hash,
                key_prefix,
                tenant_id,
                allowed_tenant_ids_json,
                revoked_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (
                str(uuid4()),
                name,
                self._hash_key(secret),
                secret[:8],
                tenant_id,
                json.dumps(sorted(set(resolved_allowed_tenant_ids))),
                now,
                now,
            ),
        )
        self._commit()
        stored = self.find_api_key(secret)
        assert stored is not None
        return stored.to_record(), secret

    def ensure_api_key(
        self,
        *,
        raw_key: str,
        name: str,
        tenant_id: str | None,
        allowed_tenant_ids: list[str],
    ) -> ApiKeyRecord:
        stored = self.find_api_key(raw_key)
        if stored is not None:
            return stored.to_record()
        record, _ = self.create_api_key(
            name=name,
            tenant_id=tenant_id,
            allowed_tenant_ids=allowed_tenant_ids,
            raw_key=raw_key,
        )
        return record

    def list_api_keys(self, tenant_id: str | None = None) -> list[ApiKeyRecord]:
        query = "SELECT * FROM api_keys"
        params: tuple[object, ...] = ()
        if tenant_id:
            query += " WHERE tenant_id = ?"
            params = (tenant_id,)
        query += " ORDER BY created_at DESC"
        rows = self._execute(query, params).fetchall()
        return [self._stored_api_key_from_row(row).to_record() for row in rows]

    def revoke_api_key(self, api_key_id: str) -> ApiKeyRecord | None:
        row = self._execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
        if row is None:
            return None
        self._execute(
            "UPDATE api_keys SET revoked_at = ?, updated_at = ? WHERE id = ?",
            (self._now(), self._now(), api_key_id),
        )
        self._commit()
        updated = self._execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
        assert updated is not None
        return self._stored_api_key_from_row(updated).to_record()

    def find_api_key(self, raw_key: str) -> StoredApiKey | None:
        row = self._execute(
            """
            SELECT * FROM api_keys
            WHERE key_hash = ? AND revoked_at IS NULL
            """,
            (self._hash_key(raw_key),),
        ).fetchone()
        return self._stored_api_key_from_row(row) if row else None

    def record_usage(self, record: UsageLedgerRecord) -> UsageLedgerRecord:
        self._execute(
            """
            INSERT INTO usage_ledger (
                request_id,
                tenant_id,
                requested_model,
                final_route_target,
                final_provider,
                fallback_used,
                cache_hit,
                response_model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                estimated_cost,
                latency_ms,
                timestamp,
                terminal_status,
                route_reason,
                policy_outcome
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.request_id,
                record.tenant_id,
                record.requested_model,
                record.final_route_target,
                record.final_provider,
                int(record.fallback_used),
                int(record.cache_hit),
                record.response_model,
                record.prompt_tokens,
                record.completion_tokens,
                record.total_tokens,
                record.estimated_cost,
                record.latency_ms,
                record.timestamp.isoformat(),
                record.terminal_status,
                record.route_reason,
                record.policy_outcome,
            ),
        )
        self._commit()
        return record

    def list_usage_records(
        self,
        *,
        tenant_id: str | None = None,
        terminal_status: str | None = None,
        route_target: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 100,
    ) -> list[UsageLedgerRecord]:
        clauses: list[str] = []
        params: list[object] = []
        if tenant_id:
            clauses.append("tenant_id = ?")
            params.append(tenant_id)
        if terminal_status:
            clauses.append("terminal_status = ?")
            params.append(terminal_status)
        if route_target:
            clauses.append("final_route_target = ?")
            params.append(route_target)
        if from_timestamp:
            clauses.append("timestamp >= ?")
            params.append(from_timestamp.isoformat())
        if to_timestamp:
            clauses.append("timestamp <= ?")
            params.append(to_timestamp.isoformat())
        query = "SELECT * FROM usage_ledger"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = self._execute(query, tuple(params)).fetchall()
        return [self._usage_from_row(row) for row in rows]

    def tenant_spend_total(self, tenant_id: str) -> float:
        row = self._execute(
            """
            SELECT COALESCE(SUM(estimated_cost), 0.0) AS total
            FROM usage_ledger
            WHERE tenant_id = ?
              AND terminal_status IN ('completed', 'fallback_completed', 'cache_hit')
            """,
            (tenant_id,),
        ).fetchone()
        return float(row["total"]) if row else 0.0

    def health_status(self) -> dict[str, object]:
        if self.connection is None:
            return {
                "status": "not_ready",
                "required": True,
                "detail": "Governance store connection is not initialized.",
            }
        try:
            self._execute("SELECT 1").fetchone()
            schema_row = self._execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name IN ('tenants', 'tenant_policies', 'api_keys', 'usage_ledger')
                """
            ).fetchall()
        except sqlite3.Error as exc:
            return {
                "status": "not_ready",
                "required": True,
                "detail": f"Governance store query failed: {exc}",
            }
        if len(schema_row) < 4:
            return {
                "status": "not_ready",
                "required": True,
                "detail": "Governance schema is incomplete.",
            }
        return {
            "status": "ready",
            "required": True,
            "detail": "Governance store is connected and schema is present.",
        }

    def _execute(
        self,
        statement: str,
        params: tuple[object, ...] | dict[str, object] = (),
    ) -> sqlite3.Cursor:
        if self.connection is None:
            raise RuntimeError("GovernanceStore is not initialized.")
        with self._lock:
            return self.connection.execute(statement, params)

    def _commit(self) -> None:
        if self.connection is None:
            raise RuntimeError("GovernanceStore is not initialized.")
        with self._lock:
            self.connection.commit()

    def _tenant_from_row(self, row: sqlite3.Row) -> TenantRecord:
        return TenantRecord(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            metadata=json.loads(row["metadata_json"]),
            active=bool(row["active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _stored_api_key_from_row(self, row: sqlite3.Row) -> StoredApiKey:
        return StoredApiKey(
            id=row["id"],
            name=row["name"],
            key_hash=row["key_hash"],
            key_prefix=row["key_prefix"],
            tenant_id=row["tenant_id"],
            allowed_tenant_ids=json.loads(row["allowed_tenant_ids_json"]),
            revoked_at=row["revoked_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _usage_from_row(self, row: sqlite3.Row) -> UsageLedgerRecord:
        return UsageLedgerRecord(
            request_id=row["request_id"],
            tenant_id=row["tenant_id"],
            requested_model=row["requested_model"],
            final_route_target=row["final_route_target"],
            final_provider=row["final_provider"],
            fallback_used=bool(row["fallback_used"]),
            cache_hit=bool(row["cache_hit"]),
            response_model=row["response_model"],
            prompt_tokens=row["prompt_tokens"],
            completion_tokens=row["completion_tokens"],
            total_tokens=row["total_tokens"],
            estimated_cost=row["estimated_cost"],
            latency_ms=row["latency_ms"],
            timestamp=row["timestamp"],
            terminal_status=row["terminal_status"],
            route_reason=row["route_reason"],
            policy_outcome=row["policy_outcome"],
        )

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()
