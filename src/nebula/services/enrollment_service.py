from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nebula.core.config import Settings
from nebula.db.models import DeploymentModel, DeploymentRemoteActionModel, EnrollmentTokenModel
from nebula.models.deployment import (
    DeploymentRecord,
    EnrollmentExchangeResponse,
    EnrollmentTokenResponse,
    RemoteActionCompletionRequest,
    RemoteActionCompletionResponse,
    RemoteActionRecord,
)
from nebula.services.heartbeat_ingest_service import compute_freshness


class DeploymentRemoteActionStateError(ValueError):
    pass


class RemoteActionValidationError(ValueError):
    pass


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

    def queue_rotate_deployment_credential(self, deployment_id: str, note: str) -> RemoteActionRecord:
        normalized_note = note.strip()
        if not 1 <= len(normalized_note) <= 280:
            raise RemoteActionValidationError(
                "Remote action note must be between 1 and 280 characters."
            )

        with self._session() as session:
            deployment = session.get(DeploymentModel, deployment_id)
            if deployment is None:
                raise KeyError(f"Deployment not found: {deployment_id}")
            if deployment.enrollment_state != "active":
                raise DeploymentRemoteActionStateError(
                    "Deployment is not in an active linked state."
                )

            existing = session.scalars(
                select(DeploymentRemoteActionModel)
                .where(
                    DeploymentRemoteActionModel.deployment_id == deployment_id,
                    DeploymentRemoteActionModel.action_type == "rotate_deployment_credential",
                    DeploymentRemoteActionModel.status.in_(("queued", "in_progress")),
                )
                .order_by(DeploymentRemoteActionModel.requested_at.desc())
                .with_for_update()
            ).first()
            if existing is not None:
                return self._to_remote_action_record(existing)

            now = self._now()
            action = DeploymentRemoteActionModel(
                id=str(uuid4()),
                deployment_id=deployment_id,
                action_type="rotate_deployment_credential",
                status="queued",
                note=normalized_note,
                requested_at=now,
                expires_at=now + timedelta(minutes=15),
                started_at=None,
                finished_at=None,
                failure_reason=None,
                failure_detail=None,
                result_credential_prefix=None,
                created_at=now,
                updated_at=now,
            )
            session.add(action)
            session.commit()
            session.refresh(action)
            return self._to_remote_action_record(action)

    def list_remote_actions(self, deployment_id: str, limit: int = 10) -> list[RemoteActionRecord]:
        with self._session() as session:
            deployment = session.get(DeploymentModel, deployment_id)
            if deployment is None:
                raise KeyError(f"Deployment not found: {deployment_id}")

            rows = session.scalars(
                select(DeploymentRemoteActionModel)
                .where(DeploymentRemoteActionModel.deployment_id == deployment_id)
                .order_by(DeploymentRemoteActionModel.requested_at.desc())
                .limit(limit)
            ).all()
            return [self._to_remote_action_record(row) for row in rows]

    def claim_next_remote_action(self, raw_credential: str) -> RemoteActionRecord | None:
        now = self._now()
        with self._session() as session:
            deployment = self._get_active_deployment_for_credential(session, raw_credential)
            if deployment is None:
                return None

            queued_actions = session.scalars(
                select(DeploymentRemoteActionModel)
                .where(
                    DeploymentRemoteActionModel.deployment_id == deployment.id,
                    DeploymentRemoteActionModel.status == "queued",
                )
                .order_by(DeploymentRemoteActionModel.requested_at.asc())
                .with_for_update()
            ).all()

            for action in queued_actions:
                expires_at = action.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=UTC)
                if expires_at <= now:
                    action.status = "failed"
                    action.finished_at = now
                    action.failure_reason = "expired"
                    action.failure_detail = "Remote action expired before the deployment claimed it."
                    action.updated_at = now
                    continue

                action.status = "in_progress"
                action.started_at = now
                action.updated_at = now
                session.commit()
                session.refresh(action)
                return self._to_remote_action_record(action)

            session.commit()
            return None

    def complete_remote_action(
        self,
        raw_credential: str,
        action_id: str,
        payload: RemoteActionCompletionRequest,
    ) -> RemoteActionCompletionResponse | None:
        now = self._now()
        with self._session() as session:
            deployment = self._get_active_deployment_for_credential(session, raw_credential)
            if deployment is None:
                return None

            action = session.scalars(
                select(DeploymentRemoteActionModel)
                .where(
                    DeploymentRemoteActionModel.id == action_id,
                    DeploymentRemoteActionModel.deployment_id == deployment.id,
                )
                .with_for_update()
            ).first()
            if action is None:
                return RemoteActionCompletionResponse(acknowledged=False)

            action.finished_at = now
            action.updated_at = now

            if payload.status == "failed":
                action.status = "failed"
                action.failure_reason = payload.failure_reason
                action.failure_detail = payload.failure_detail
                session.commit()
                return RemoteActionCompletionResponse(
                    acknowledged=True,
                    new_deployment_credential=None,
                )

            if action.action_type != "rotate_deployment_credential" or action.status != "in_progress":
                action.status = "failed"
                action.failure_reason = "invalid_state"
                action.failure_detail = "Remote action was not in progress for rotation."
                session.commit()
                return RemoteActionCompletionResponse(
                    acknowledged=True,
                    new_deployment_credential=None,
                )

            raw_credential = f"nbdc_{secrets.token_urlsafe(32)}"
            deployment.credential_hash = self._hash_token(raw_credential)
            deployment.credential_prefix = raw_credential[:12]
            deployment.updated_at = now
            action.status = "applied"
            action.failure_reason = None
            action.failure_detail = None
            action.result_credential_prefix = raw_credential[:12]
            session.commit()
            return RemoteActionCompletionResponse(
                acknowledged=True,
                new_deployment_credential=raw_credential,
            )

    def validate_deployment_credential(self, raw_credential: str | None) -> bool:
        if not raw_credential:
            return False
        with self._session() as session:
            return self._get_active_deployment_for_credential(session, raw_credential) is not None

    def _to_record(self, model: DeploymentModel) -> DeploymentRecord:
        def _iso(dt: datetime | None) -> str | None:
            return dt.isoformat() if dt is not None else None

        freshness_status, freshness_reason = compute_freshness(model.last_seen_at)

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
            last_seen_at=_iso(model.last_seen_at),
            freshness_status=freshness_status,
            freshness_reason=freshness_reason,
            dependency_summary=model.dependency_summary_json,
        )

    def _to_remote_action_record(
        self, model: DeploymentRemoteActionModel
    ) -> RemoteActionRecord:
        def _iso(dt: datetime | None) -> str | None:
            return dt.isoformat() if dt is not None else None

        return RemoteActionRecord(
            id=model.id,
            deployment_id=model.deployment_id,
            action_type=model.action_type,  # type: ignore[arg-type]
            status=model.status,  # type: ignore[arg-type]
            note=model.note,
            requested_at=model.requested_at.isoformat(),
            expires_at=model.expires_at.isoformat(),
            started_at=_iso(model.started_at),
            finished_at=_iso(model.finished_at),
            failure_reason=model.failure_reason,  # type: ignore[arg-type]
            failure_detail=model.failure_detail,
            result_credential_prefix=model.result_credential_prefix,
        )

    def _hash_token(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def _get_active_deployment_for_credential(
        self,
        session: Session,
        raw_credential: str,
    ) -> DeploymentModel | None:
        cred_hash = self._hash_token(raw_credential)
        return session.scalars(
            select(DeploymentModel)
            .where(
                DeploymentModel.credential_hash == cred_hash,
                DeploymentModel.enrollment_state == "active",
            )
            .with_for_update()
        ).first()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _session(self) -> Session:
        return self._session_factory()
