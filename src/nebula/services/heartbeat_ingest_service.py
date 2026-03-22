from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nebula.db.models import DeploymentModel

CONNECTED_WINDOW = timedelta(minutes=10)  # D-08
DEGRADED_WINDOW = timedelta(minutes=30)   # D-08
STALE_WINDOW = timedelta(hours=1)         # D-08


def compute_freshness(last_seen_at: datetime | None) -> tuple[str | None, str | None]:
    """Compute (freshness_status, freshness_reason) from last_seen_at.

    Returns (None, None) for never-enrolled deployments (D-14).
    """
    if last_seen_at is None:
        return None, None
    now = datetime.now(UTC)
    delta = max(now - last_seen_at, timedelta(0))  # Clamp for clock skew
    if delta <= CONNECTED_WINDOW:
        return "connected", f"Last heartbeat {_human_delta(delta)} ago"
    elif delta <= DEGRADED_WINDOW:
        return "degraded", f"No heartbeat for {_human_delta(delta)}"
    elif delta <= STALE_WINDOW:
        return "stale", f"No heartbeat for {_human_delta(delta)}"
    else:
        return "offline", f"No heartbeat since {last_seen_at.strftime('%b %-d %H:%M')}"


def _human_delta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes} minutes" if minutes != 1 else "1 minute"
    hours = minutes // 60
    return f"{hours} hours" if hours != 1 else "1 hour"


class HeartbeatIngestService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def record_heartbeat(
        self,
        raw_credential: str | None,
        nebula_version: str,
        capability_flags: list[str],
        dependency_summary: dict[str, list[str]],
    ) -> bool:
        """Record a heartbeat. Returns True if valid credential, False otherwise."""
        if not raw_credential:
            return False
        cred_hash = hashlib.sha256(raw_credential.encode("utf-8")).hexdigest()
        with self._session_factory() as session:
            deployment = session.scalars(
                select(DeploymentModel).where(
                    DeploymentModel.credential_hash == cred_hash,
                    DeploymentModel.enrollment_state == "active",
                )
            ).first()
            if deployment is None:
                return False
            now = datetime.now(UTC)
            deployment.last_seen_at = now
            deployment.nebula_version = nebula_version
            deployment.capability_flags_json = capability_flags
            deployment.dependency_summary_json = dependency_summary
            deployment.updated_at = now
            session.commit()
            return True
