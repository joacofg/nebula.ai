from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from nebula.core.config import Settings
from nebula.db.models import ApiKeyModel, TenantModel, TenantPolicyModel, UsageLedgerModel
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
    def __init__(self, settings: Settings, session_factory: sessionmaker[Session]) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self._lock = RLock()
        self.engine = session_factory.kw["bind"]

    def initialize(self) -> None:
        required_tables = {"tenants", "tenant_policies", "api_keys", "usage_ledger"}
        table_names = set(inspect(self.engine).get_table_names())
        missing_tables = required_tables - table_names
        if missing_tables:
            missing = ", ".join(sorted(missing_tables))
            raise RuntimeError(
                f"Governance schema is not migrated. Missing tables: {missing}. Run `alembic upgrade head`."
            )
        self.ensure_bootstrap()

    def close(self) -> None:
        self.engine.dispose()

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
        with self._session() as session:
            rows = session.scalars(select(TenantModel).order_by(TenantModel.id)).all()
            return [self._tenant_from_model(row) for row in rows]

    def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        with self._session() as session:
            row = session.get(TenantModel, tenant_id)
            return self._tenant_from_model(row) if row else None

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
        with self._session() as session:
            tenant = session.get(TenantModel, tenant_id)
            if tenant is None:
                tenant = TenantModel(
                    id=tenant_id,
                    name=name,
                    description=description,
                    metadata_json=metadata,
                    active=active,
                    created_at=now,
                    updated_at=now,
                )
                session.add(tenant)
            elif upsert:
                tenant.name = name
                tenant.description = description
                tenant.metadata_json = metadata
                tenant.active = active
                tenant.updated_at = now
            else:
                raise ValueError(f"Tenant already exists: {tenant_id}")
            session.commit()
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
        with self._session() as session:
            tenant = session.get(TenantModel, tenant_id)
            if tenant is None:
                return None
            tenant.name = name if name is not None else tenant.name
            tenant.description = description if description is not None else tenant.description
            tenant.metadata_json = metadata if metadata is not None else tenant.metadata_json
            tenant.active = active if active is not None else tenant.active
            tenant.updated_at = self._now()
            session.commit()
            session.refresh(tenant)
            return self._tenant_from_model(tenant)

    def get_policy(self, tenant_id: str) -> TenantPolicy:
        with self._session() as session:
            row = session.get(TenantPolicyModel, tenant_id)
        if row is None:
            policy = self.default_policy()
            self.upsert_policy(tenant_id, policy)
            return policy
        return self._policy_from_model(row)

    def upsert_policy(self, tenant_id: str, policy: TenantPolicy) -> TenantPolicy:
        with self._session() as session:
            current = session.get(TenantPolicyModel, tenant_id)
            if current is None:
                current = TenantPolicyModel(tenant_id=tenant_id, updated_at=self._now())
                session.add(current)
            current.routing_mode_default = policy.routing_mode_default
            current.allowed_premium_models_json = policy.allowed_premium_models
            current.semantic_cache_enabled = policy.semantic_cache_enabled
            current.fallback_enabled = policy.fallback_enabled
            current.max_premium_cost_per_request = policy.max_premium_cost_per_request
            current.soft_budget_usd = policy.soft_budget_usd
            current.prompt_capture_enabled = policy.prompt_capture_enabled
            current.response_capture_enabled = policy.response_capture_enabled
            current.updated_at = self._now()
            session.commit()
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
        now = self._now()
        secret = raw_key or f"nbk_{secrets.token_urlsafe(24)}"
        with self._session() as session:
            for allowed_tenant_id in resolved_allowed_tenant_ids:
                if session.get(TenantModel, allowed_tenant_id) is None:
                    raise ValueError(f"Unknown tenant: {allowed_tenant_id}")
            if tenant_id and session.get(TenantModel, tenant_id) is None:
                raise ValueError(f"Unknown tenant: {tenant_id}")
            api_key = ApiKeyModel(
                id=str(uuid4()),
                name=name,
                key_hash=self._hash_key(secret),
                key_prefix=secret[:8],
                tenant_id=tenant_id,
                allowed_tenant_ids_json=sorted(set(resolved_allowed_tenant_ids)),
                revoked_at=None,
                created_at=now,
                updated_at=now,
            )
            session.add(api_key)
            session.commit()
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
        with self._session() as session:
            stmt = select(ApiKeyModel)
            if tenant_id:
                stmt = stmt.where(ApiKeyModel.tenant_id == tenant_id)
            rows = session.scalars(stmt.order_by(ApiKeyModel.created_at.desc())).all()
            return [self._stored_api_key_from_model(row).to_record() for row in rows]

    def revoke_api_key(self, api_key_id: str) -> ApiKeyRecord | None:
        with self._session() as session:
            row = session.get(ApiKeyModel, api_key_id)
            if row is None:
                return None
            row.revoked_at = self._now()
            row.updated_at = self._now()
            session.commit()
            session.refresh(row)
            return self._stored_api_key_from_model(row).to_record()

    def find_api_key(self, raw_key: str) -> StoredApiKey | None:
        with self._session() as session:
            row = session.scalar(
                select(ApiKeyModel).where(
                    ApiKeyModel.key_hash == self._hash_key(raw_key),
                    ApiKeyModel.revoked_at.is_(None),
                )
            )
            return self._stored_api_key_from_model(row) if row else None

    def record_usage(self, record: UsageLedgerRecord) -> UsageLedgerRecord:
        with self._session() as session:
            session.add(
                UsageLedgerModel(
                    request_id=record.request_id,
                    tenant_id=record.tenant_id,
                    requested_model=record.requested_model,
                    final_route_target=record.final_route_target,
                    final_provider=record.final_provider,
                    fallback_used=record.fallback_used,
                    cache_hit=record.cache_hit,
                    response_model=record.response_model,
                    prompt_tokens=record.prompt_tokens,
                    completion_tokens=record.completion_tokens,
                    total_tokens=record.total_tokens,
                    estimated_cost=record.estimated_cost,
                    latency_ms=record.latency_ms,
                    timestamp=record.timestamp,
                    terminal_status=record.terminal_status,
                    route_reason=record.route_reason,
                    policy_outcome=record.policy_outcome,
                    route_signals=record.route_signals,
                )
            )
            session.commit()
        return record

    def list_usage_records(
        self,
        *,
        request_id: str | None = None,
        tenant_id: str | None = None,
        terminal_status: str | None = None,
        route_target: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 100,
    ) -> list[UsageLedgerRecord]:
        with self._session() as session:
            stmt = select(UsageLedgerModel)
            if request_id:
                stmt = stmt.where(UsageLedgerModel.request_id == request_id)
            if tenant_id:
                stmt = stmt.where(UsageLedgerModel.tenant_id == tenant_id)
            if terminal_status:
                stmt = stmt.where(UsageLedgerModel.terminal_status == terminal_status)
            if route_target:
                stmt = stmt.where(UsageLedgerModel.final_route_target == route_target)
            if from_timestamp:
                stmt = stmt.where(UsageLedgerModel.timestamp >= from_timestamp)
            if to_timestamp:
                stmt = stmt.where(UsageLedgerModel.timestamp <= to_timestamp)
            rows = session.scalars(stmt.order_by(UsageLedgerModel.timestamp.desc()).limit(limit)).all()
            return [self._usage_from_model(row) for row in rows]

    def tenant_spend_total(self, tenant_id: str) -> float:
        with self._session() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(UsageLedgerModel.estimated_cost), 0.0)).where(
                    UsageLedgerModel.tenant_id == tenant_id,
                    UsageLedgerModel.terminal_status.in_(
                        ["completed", "fallback_completed", "cache_hit"]
                    ),
                )
            )
            return float(total or 0.0)

    def health_status(self) -> dict[str, object]:
        try:
            with self._session() as session:
                session.execute(select(1)).scalar_one()
            table_names = set(inspect(self.engine).get_table_names())
        except Exception as exc:
            return {
                "status": "not_ready",
                "required": True,
                "detail": f"Governance store query failed: {exc}",
            }
        if {"tenants", "tenant_policies", "api_keys", "usage_ledger"} - table_names:
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

    def list_known_premium_models(self) -> list[str]:
        models = {self.settings.premium_model}
        with self._session() as session:
            rows = session.scalars(select(TenantPolicyModel.allowed_premium_models_json)).all()
        for row in rows:
            models.update(model for model in row if model)
        return sorted(models)

    def _tenant_from_model(self, row: TenantModel) -> TenantRecord:
        return TenantRecord(
            id=row.id,
            name=row.name,
            description=row.description,
            metadata=row.metadata_json,
            active=row.active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _stored_api_key_from_model(self, row: ApiKeyModel) -> StoredApiKey:
        return StoredApiKey(
            id=row.id,
            name=row.name,
            key_hash=row.key_hash,
            key_prefix=row.key_prefix,
            tenant_id=row.tenant_id,
            allowed_tenant_ids=row.allowed_tenant_ids_json,
            revoked_at=row.revoked_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _usage_from_model(self, row: UsageLedgerModel) -> UsageLedgerRecord:
        return UsageLedgerRecord(
            request_id=row.request_id,
            tenant_id=row.tenant_id,
            requested_model=row.requested_model,
            final_route_target=row.final_route_target,
            final_provider=row.final_provider,
            fallback_used=row.fallback_used,
            cache_hit=row.cache_hit,
            response_model=row.response_model,
            prompt_tokens=row.prompt_tokens,
            completion_tokens=row.completion_tokens,
            total_tokens=row.total_tokens,
            estimated_cost=row.estimated_cost,
            latency_ms=row.latency_ms,
            timestamp=row.timestamp,
            terminal_status=row.terminal_status,
            route_reason=row.route_reason,
            policy_outcome=row.policy_outcome,
        )

    def _policy_from_model(self, row: TenantPolicyModel) -> TenantPolicy:
        return TenantPolicy(
            routing_mode_default=row.routing_mode_default,
            allowed_premium_models=row.allowed_premium_models_json,
            semantic_cache_enabled=row.semantic_cache_enabled,
            fallback_enabled=row.fallback_enabled,
            max_premium_cost_per_request=row.max_premium_cost_per_request,
            soft_budget_usd=row.soft_budget_usd,
            prompt_capture_enabled=row.prompt_capture_enabled,
            response_capture_enabled=row.response_capture_enabled,
        )

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _session(self) -> Session:
        return self.session_factory()
