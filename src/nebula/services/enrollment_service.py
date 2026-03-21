from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nebula.core.config import Settings
from nebula.db.models import DeploymentModel, EnrollmentTokenModel
from nebula.models.deployment import (
    DeploymentRecord,
    EnrollmentExchangeResponse,
    EnrollmentTokenResponse,
)


class EnrollmentService:
    def __init__(self, settings: Settings, session_factory: sessionmaker[Session]) -> None:
        self.settings = settings
        self._session_factory = session_factory

    def create_deployment_slot(self, display_name: str, environment: str) -> DeploymentRecord:
        now = self._now()
        deployment = DeploymentModel(
            id=str(uuid4()),
            display_name=display_name,
            environment=environment,
            enrollment_state="pending",
            nebula_version=None,
            capability_flags_json=[],
            credential_hash=None,
            credential_prefix=None,
            enrolled_at=None,
            revoked_at=None,
            unlinked_at=None,
            created_at=now,
            updated_at=now,
        )
        with self._session() as session:
            session.add(deployment)
            session.commit()
            session.refresh(deployment)
            return self._to_record(deployment)

    def generate_enrollment_token(self, deployment_id: str) -> EnrollmentTokenResponse:
        with self._session() as session:
            deployment = session.get(DeploymentModel, deployment_id)
            if deployment is None:
                raise KeyError(f"Deployment not found: {deployment_id}")
            if deployment.enrollment_state == "active":
                raise ValueError(
                    f"Deployment {deployment_id} is already active. Unlink or revoke it first."
                )

            # For relink (revoked/unlinked), reset state to pending
            if deployment.enrollment_state in ("revoked", "unlinked"):
                deployment.enrollment_state = "pending"
                deployment.updated_at = self._now()

            raw_token = f"nbet_{secrets.token_urlsafe(32)}"
            token_hash = self._hash_token(raw_token)
            token_prefix = raw_token[:12]
            now = self._now()
            expires_at = now + timedelta(hours=1)

            token_record = EnrollmentTokenModel(
                id=str(uuid4()),
                deployment_id=deployment_id,
                token_hash=token_hash,
                token_prefix=token_prefix,
                expires_at=expires_at,
                consumed_at=None,
                created_at=now,
            )
            session.add(token_record)
            session.commit()

        return EnrollmentTokenResponse(
            token=raw_token,
            expires_at=expires_at.isoformat(),
            deployment_id=deployment_id,
        )

    def consume_enrollment_token(
        self,
        raw_token: str,
        nebula_version: str,
        capability_flags: list[str],
    ) -> EnrollmentExchangeResponse | None:
        token_hash = self._hash_token(raw_token)
        now = self._now()
        with self._session() as session:
            # Pessimistic lock to prevent concurrent double-consumption
            token_row = session.scalars(
                select(EnrollmentTokenModel)
                .where(
                    EnrollmentTokenModel.token_hash == token_hash,
                    EnrollmentTokenModel.consumed_at.is_(None),
                    EnrollmentTokenModel.expires_at > now,
                )
                .with_for_update()
            ).first()

            if token_row is None:
                return None

            # Generate steady-state deployment credential
            raw_credential = f"nbdc_{secrets.token_urlsafe(32)}"
            cred_hash = hashlib.sha256(raw_credential.encode("utf-8")).hexdigest()
            cred_prefix = raw_credential[:12]

            # Update deployment to active
            deployment = session.get(DeploymentModel, token_row.deployment_id)
            if deployment is None:
                return None

            deployment.enrollment_state = "active"
            deployment.credential_hash = cred_hash
            deployment.credential_prefix = cred_prefix
            deployment.enrolled_at = now
            deployment.nebula_version = nebula_version
            deployment.capability_flags_json = capability_flags
            deployment.updated_at = now

            # Mark token as consumed
            token_row.consumed_at = now

            session.commit()
            session.refresh(deployment)

            return EnrollmentExchangeResponse(
                deployment_id=deployment.id,
                deployment_credential=raw_credential,
                display_name=deployment.display_name,
                environment=deployment.environment,
            )

    def revoke_deployment(self, deployment_id: str) -> DeploymentRecord | None:
        with self._session() as session:
            deployment = session.get(DeploymentModel, deployment_id)
            if deployment is None:
                return None
            if deployment.enrollment_state != "active":
                raise ValueError("Can only revoke active deployments")
            now = self._now()
            deployment.enrollment_state = "revoked"
            deployment.revoked_at = now
            deployment.credential_hash = None
            deployment.credential_prefix = None
            deployment.updated_at = now
            session.commit()
            session.refresh(deployment)
            return self._to_record(deployment)

    def unlink_deployment(self, deployment_id: str) -> DeploymentRecord | None:
        with self._session() as session:
            deployment = session.get(DeploymentModel, deployment_id)
            if deployment is None:
                return None
            if deployment.enrollment_state != "active":
                raise ValueError("Can only unlink active deployments")
            now = self._now()
            deployment.enrollment_state = "unlinked"
            deployment.unlinked_at = now
            deployment.credential_hash = None
            deployment.credential_prefix = None
            deployment.updated_at = now
            session.commit()
            session.refresh(deployment)
            return self._to_record(deployment)

    def list_deployments(self) -> list[DeploymentRecord]:
        with self._session() as session:
            rows = session.scalars(
                select(DeploymentModel).order_by(DeploymentModel.created_at.desc())
            ).all()
            return [self._to_record(row) for row in rows]

    def get_deployment(self, deployment_id: str) -> DeploymentRecord | None:
        with self._session() as session:
            row = session.get(DeploymentModel, deployment_id)
            return self._to_record(row) if row else None

    def _to_record(self, model: DeploymentModel) -> DeploymentRecord:
        def _iso(dt: datetime | None) -> str | None:
            return dt.isoformat() if dt is not None else None

        return DeploymentRecord(
            id=model.id,
            display_name=model.display_name,
            environment=model.environment,
            enrollment_state=model.enrollment_state,  # type: ignore[arg-type]
            nebula_version=model.nebula_version,
            capability_flags=model.capability_flags_json or [],
            enrolled_at=_iso(model.enrolled_at),
            revoked_at=_iso(model.revoked_at),
            unlinked_at=_iso(model.unlinked_at),
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

    def _hash_token(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _session(self) -> Session:
        return self._session_factory()
