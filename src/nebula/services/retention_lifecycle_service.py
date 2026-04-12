from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from nebula.services.governance_store import GovernanceStore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetentionLifecycleSnapshot:
    enabled: bool
    interval_seconds: int
    last_run_at: datetime | None = None
    last_attempted_run_at: datetime | None = None
    last_status: str = "idle"
    last_deleted_count: int = 0
    last_eligible_count: int = 0
    last_cutoff: datetime | None = None
    last_error: str | None = None

    def to_health_payload(self) -> dict[str, Any]:
        detail = self._detail()
        payload: dict[str, Any] = {
            "status": self._dependency_status(),
            "required": False,
            "detail": detail,
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "last_status": self.last_status,
            "last_run_at": self._iso(self.last_run_at),
            "last_attempted_run_at": self._iso(self.last_attempted_run_at),
            "last_deleted_count": self.last_deleted_count,
            "last_eligible_count": self.last_eligible_count,
            "last_cutoff": self._iso(self.last_cutoff),
            "last_error": self.last_error,
        }
        return payload

    def _dependency_status(self) -> str:
        if not self.enabled:
            return "ready"
        if self.last_status == "failed":
            return "degraded"
        return "ready"

    def _detail(self) -> str:
        if not self.enabled:
            return "Retention lifecycle is disabled by configuration."
        if self.last_status == "idle":
            return "Retention lifecycle has not completed a cleanup run yet."
        if self.last_status == "running":
            return "Retention lifecycle cleanup is currently running."
        if self.last_status == "failed":
            return "Retention lifecycle cleanup failed on its last attempt."
        return "Retention lifecycle cleanup completed successfully."

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()


class RetentionLifecycleService:
    def __init__(
        self,
        *,
        enabled: bool,
        interval_seconds: int,
        governance_store: GovernanceStore,
    ) -> None:
        self._enabled = enabled
        self._interval_seconds = interval_seconds
        self._governance_store = governance_store
        self._task: asyncio.Task | None = None
        self._snapshot = RetentionLifecycleSnapshot(
            enabled=enabled,
            interval_seconds=interval_seconds,
        )

    def start(self) -> None:
        if not self._enabled or self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval_seconds)
            await self._run_once_catching()

    async def run_cleanup_once(self, *, now: datetime | None = None) -> dict[str, object]:
        return await self._execute_cleanup(now=now)

    async def _run_once_catching(self) -> None:
        try:
            await self._execute_cleanup()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Retention cleanup failed: %s", exc)

    async def health_status(self) -> dict[str, object]:
        return self._snapshot.to_health_payload()

    async def _execute_cleanup(self, *, now: datetime | None = None) -> dict[str, object]:
        attempt_time = self._normalize(now or datetime.now(UTC))
        self._snapshot.last_attempted_run_at = attempt_time
        self._snapshot.last_status = "running"
        self._snapshot.last_error = None

        try:
            result = self._governance_store.delete_expired_usage_records(now=attempt_time)
        except Exception as exc:  # noqa: BLE001
            self._snapshot.last_status = "failed"
            self._snapshot.last_error = str(exc)
            raise

        cutoff = result.get("cutoff")
        self._snapshot.last_status = "ok"
        self._snapshot.last_run_at = attempt_time
        self._snapshot.last_deleted_count = int(result.get("deleted_count", 0) or 0)
        self._snapshot.last_eligible_count = int(result.get("eligible_count", 0) or 0)
        self._snapshot.last_cutoff = self._normalize(cutoff) if isinstance(cutoff, datetime) else None
        self._snapshot.last_error = None
        return {
            "deleted_count": self._snapshot.last_deleted_count,
            "eligible_count": self._snapshot.last_eligible_count,
            "cutoff": self._snapshot.last_cutoff,
            "ran_at": self._snapshot.last_run_at,
            "status": self._snapshot.last_status,
        }

    @staticmethod
    def _normalize(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
