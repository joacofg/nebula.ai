"""Gateway-side outbound enrollment exchange and local credential storage."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nebula.core.config import Settings
from nebula.db.models import LocalHostedIdentityModel
from nebula.models.deployment import EnrollmentExchangeRequest, EnrollmentExchangeResponse

logger = logging.getLogger(__name__)


def _nebula_version() -> str:
    try:
        from importlib.metadata import version

        return version("nebula")
    except Exception:
        return "unknown"


class GatewayEnrollmentService:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker[Session],
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._session_factory = session_factory
        self._http_transport = http_transport

    async def attempt_enrollment(self, enrollment_token: str) -> bool:
        """Attempt outbound enrollment exchange with the hosted plane.

        Returns True if already enrolled or successfully enrolled.
        Returns False on any failure — enrollment failure is NOT fatal.
        """
        # Check if local identity already exists
        existing = self.get_local_identity()
        if existing is not None:
            logger.info(
                "Already enrolled as %s, skipping enrollment",
                existing.deployment_id,
            )
            return True

        if not self.settings.hosted_plane_url:
            logger.warning(
                "NEBULA_HOSTED_PLANE_URL not set, cannot enroll"
            )
            return False

        request_body = EnrollmentExchangeRequest(
            enrollment_token=enrollment_token,
            nebula_version=_nebula_version(),
            capability_flags=["semantic_cache", "premium_routing"],
        )

        try:
            client_kwargs: dict = {"timeout": 30.0}
            if self._http_transport is not None:
                client_kwargs["transport"] = self._http_transport
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(
                    f"{self.settings.hosted_plane_url}/v1/enrollment/exchange",
                    json=request_body.model_dump(),
                )
                response.raise_for_status()

            exchange = EnrollmentExchangeResponse.model_validate(response.json())
            self._store_local_identity(exchange)

            logger.info(
                "Enrolled as %s (%s)",
                exchange.deployment_id,
                exchange.display_name,
            )

            # Warn if token is still in environment (per D-06)
            if self.settings.enrollment_token:
                logger.warning(
                    "NEBULA_ENROLLMENT_TOKEN is still set in environment. "
                    "Remove it — the token has been consumed and is no longer needed."
                )

            # Heartbeat sender started in lifespan, not here

            return True

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logger.error(
                    "Enrollment token is invalid, expired, or already consumed. "
                    "Generate a new token from the hosted console."
                )
            else:
                logger.error(
                    "Enrollment exchange failed: %s. "
                    "Gateway will start without hosted features.",
                    exc,
                )
            return False
        except Exception as exc:
            logger.error(
                "Enrollment exchange failed: %s. "
                "Gateway will start without hosted features.",
                exc,
            )
            return False

    def get_deployment_credential(self) -> str | None:
        """Return the raw deployment credential for heartbeat auth, or None if not enrolled."""
        identity = self.get_local_identity()
        if identity is None:
            return None
        return identity.credential_raw if identity.credential_raw else None

    def get_local_identity(self) -> LocalHostedIdentityModel | None:
        """Return the current active local hosted identity, or None if not enrolled."""
        with self._session() as session:
            return session.scalars(
                select(LocalHostedIdentityModel).where(
                    LocalHostedIdentityModel.unlinked_at.is_(None)
                )
            ).first()

    def clear_local_identity(self) -> None:
        """Mark the local identity as unlinked. Used during unlink flow."""
        with self._session() as session:
            identity = session.scalars(
                select(LocalHostedIdentityModel).where(
                    LocalHostedIdentityModel.unlinked_at.is_(None)
                )
            ).first()
            if identity is not None:
                identity.unlinked_at = datetime.now(UTC)
                session.commit()

    def _store_local_identity(self, exchange: EnrollmentExchangeResponse) -> None:
        """Persist the enrollment exchange result to local_hosted_identity table."""
        cred_hash = hashlib.sha256(
            exchange.deployment_credential.encode("utf-8")
        ).hexdigest()
        cred_prefix = exchange.deployment_credential[:12]
        now = datetime.now(UTC)

        with self._session() as session:
            identity = LocalHostedIdentityModel(
                deployment_id=exchange.deployment_id,
                display_name=exchange.display_name,
                environment=exchange.environment,
                credential_hash=cred_hash,
                credential_prefix=cred_prefix,
                credential_raw=exchange.deployment_credential,  # needed for heartbeat auth
                enrolled_at=now,
                unlinked_at=None,
            )
            session.merge(identity)
            session.commit()

    def _session(self) -> Session:
        return self._session_factory()
