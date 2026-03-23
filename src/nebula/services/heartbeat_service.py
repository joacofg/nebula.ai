"""Gateway-side background heartbeat sender."""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

import httpx

from nebula.core.config import Settings
from nebula.models.heartbeat import HeartbeatRequest

logger = logging.getLogger(__name__)
HEARTBEAT_INTERVAL_SECONDS = 300  # 5 minutes (D-01)


def _nebula_version() -> str:
    try:
        from importlib.metadata import version

        return version("nebula")
    except Exception:
        return "unknown"


def derive_capability_flags(settings: Settings) -> list[str]:
    """Derive capability flags from settings (D-15, RESEARCH.md recommendation)."""
    flags = ["local_provider"]  # always present
    flags.append("semantic_cache")  # always available in architecture
    if settings.premium_provider != "mock":
        flags.append("premium_routing")
    if (
        settings.remote_management_enabled
        and "rotate_deployment_credential" in settings.remote_management_allowed_actions
    ):
        flags.append("remote_credential_rotation")
    return flags


class HeartbeatService:
    def __init__(
        self,
        settings: Settings,
        gateway_enrollment_service,  # provides get_deployment_credential()
        runtime_health_service,  # provides dependencies()
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._enrollment = gateway_enrollment_service
        self._health = runtime_health_service
        self._http_transport = http_transport
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """Start the background heartbeat loop (D-04)."""
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Cancel the background heartbeat loop."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await self._send_once()

    async def _send_once(self) -> None:
        credential = self._enrollment.get_deployment_credential()
        if credential is None or self.settings.hosted_plane_url is None:
            return  # not enrolled or no hosted plane — skip silently

        try:
            dep_health = await self._health.dependencies()
            dep_summary = self._summarize_deps(dep_health)
            payload = HeartbeatRequest(
                nebula_version=_nebula_version(),
                capability_flags=derive_capability_flags(self.settings),
                dependency_summary=dep_summary,
            )
            client_kwargs: dict = {"timeout": 10.0}
            if self._http_transport is not None:
                client_kwargs["transport"] = self._http_transport
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(
                    f"{self.settings.hosted_plane_url}/v1/heartbeat",
                    json=payload.model_dump(),
                    headers={"X-Nebula-Deployment-Credential": credential},
                )
                response.raise_for_status()
            logger.debug("Heartbeat sent successfully")
        except Exception as exc:
            # D-05: log warning, retry at next interval. No backoff, no queuing.
            logger.warning("Heartbeat failed: %s. Will retry at next interval.", exc)

    @staticmethod
    def _summarize_deps(dep_health: dict[str, dict[str, object]]) -> dict[str, list[str]]:
        """Map RuntimeHealthService output to HostedDependencySummary shape."""
        summary: dict[str, list[str]] = {"healthy": [], "degraded": [], "unavailable": []}
        for name, info in dep_health.items():
            status = info.get("status", "not_ready")
            if status == "ready":
                summary["healthy"].append(name)
            elif status == "degraded":
                summary["degraded"].append(name)
            else:
                summary["unavailable"].append(name)
        return summary
