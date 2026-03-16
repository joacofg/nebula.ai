from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from nebula.core.config import Settings
from nebula.models.governance import ApiKeyRecord, TenantPolicy, TenantRecord
from nebula.services.governance_store import GovernanceStore

API_KEY_HEADER = "X-Nebula-API-Key"
TENANT_HEADER = "X-Nebula-Tenant-ID"
ADMIN_API_KEY_HEADER = "X-Nebula-Admin-Key"


@dataclass(slots=True, frozen=True)
class AuthenticatedTenantContext:
    tenant: TenantRecord
    api_key: ApiKeyRecord
    policy: TenantPolicy


class AuthService:
    def __init__(self, settings: Settings, store: GovernanceStore) -> None:
        self.settings = settings
        self.store = store

    def authenticate_admin(self, raw_admin_key: str | None) -> None:
        if not raw_admin_key or raw_admin_key != self.settings.admin_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid admin API key.",
            )

    def resolve_tenant_context(
        self,
        *,
        raw_api_key: str | None,
        explicit_tenant_id: str | None,
    ) -> AuthenticatedTenantContext:
        if not raw_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing client API key.",
            )

        stored_key = self.store.find_api_key(raw_api_key)
        if stored_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client API key.",
            )

        resolved_tenant_id = explicit_tenant_id
        if resolved_tenant_id:
            if resolved_tenant_id not in stored_key.allowed_tenant_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key is not authorized for the requested tenant.",
                )
        elif stored_key.tenant_id:
            resolved_tenant_id = stored_key.tenant_id
        elif len(stored_key.allowed_tenant_ids) == 1:
            resolved_tenant_id = stored_key.allowed_tenant_ids[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant header is required for this API key.",
            )

        tenant = self.store.get_tenant(resolved_tenant_id)
        if tenant is None or not tenant.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Resolved tenant is inactive or does not exist.",
            )

        return AuthenticatedTenantContext(
            tenant=tenant,
            api_key=stored_key.to_record(),
            policy=self.store.get_policy(tenant.id),
        )

    def resolve_playground_context(self, tenant_id: str) -> AuthenticatedTenantContext:
        tenant = self.store.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found.",
            )
        if not tenant.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant is inactive.",
            )

        bootstrap_key = self.store.find_api_key(self.settings.bootstrap_api_key)
        if bootstrap_key is None:
            bootstrap_record = self.store.ensure_api_key(
                raw_key=self.settings.bootstrap_api_key,
                name=self.settings.bootstrap_api_key_name,
                tenant_id=self.settings.bootstrap_tenant_id,
                allowed_tenant_ids=[self.settings.bootstrap_tenant_id],
            )
        else:
            bootstrap_record = bootstrap_key.to_record()

        return AuthenticatedTenantContext(
            tenant=tenant,
            api_key=bootstrap_record,
            policy=self.store.get_policy(tenant.id),
        )
