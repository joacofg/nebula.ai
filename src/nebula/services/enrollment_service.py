from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nebula.core.config import Settings
from nebula.db.models import DeploymentModel, EnrollmentTokenModel
from nebula.models.deployment import DeploymentRecord, EnrollmentTokenResponse


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
