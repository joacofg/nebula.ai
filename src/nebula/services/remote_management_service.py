from __future__ import annotations

import asyncio
import logging

import httpx

from nebula.models.deployment import (
    RemoteActionCompletionRequest,
    RemoteActionFailureReason,
    RemoteActionPollResponse,
    RemoteActionRecord,
)

logger = logging.getLogger(__name__)


def _remote_management_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}{path}"
    return f"{base}/v1{path}"


class RemoteManagementService:
    def __init__(
        self,
        settings,
        gateway_enrollment_service,
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._enrollment = gateway_enrollment_service
        self._http_transport = http_transport
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        interval = getattr(self.settings, "remote_management_poll_interval_seconds", 60)
        while True:
            await asyncio.sleep(interval)
            await self._poll_once()

    async def _poll_once(self) -> None:
        if not getattr(self.settings, "hosted_plane_url", None):
            return
        if not self._enrollment.get_deployment_credential():
            return
        if not getattr(self.settings, "remote_management_enabled", False):
            return
        await self.poll_and_apply_once()

    async def poll_and_apply_once(self) -> None:
        credential = self._enrollment.get_deployment_credential()
        if (
            credential is None
            or not self.settings.hosted_plane_url
            or not getattr(self.settings, "remote_management_enabled", False)
        ):
            return

        try:
            action = await self._poll(credential)
            if action is None:
                return

            allowed, failure_reason, failure_detail = self._authorize(action)
            if not allowed:
                await self._complete(
                    credential=credential,
                    action_id=action.id,
                    payload=RemoteActionCompletionRequest(
                        status="failed",
                        failure_reason=failure_reason,
                        failure_detail=failure_detail,
                    ),
                )
                return

            completion = await self._complete(
                credential=credential,
                action_id=action.id,
                payload=RemoteActionCompletionRequest(status="applied"),
            )
            if not completion.acknowledged:
                raise ValueError("Hosted plane did not acknowledge the remote action completion.")
            if not completion.new_deployment_credential:
                raise ValueError("Hosted plane did not return a rotated deployment credential.")
            self._enrollment.replace_deployment_credential(completion.new_deployment_credential)
        except Exception as exc:
            logger.warning("Remote management poll/apply failed: %s", exc)

    def _authorize(
        self,
        action: RemoteActionRecord,
    ) -> tuple[bool, RemoteActionFailureReason | None, str | None]:
        if self._enrollment.get_local_identity() is None:
            return False, "invalid_state", "No active local hosted identity exists."

        allowed_actions = set(getattr(self.settings, "remote_management_allowed_actions", []))
        if action.action_type not in allowed_actions:
            return (
                False,
                "unauthorized_local_policy",
                f"Action {action.action_type} is not allowed by local policy.",
            )
        return True, None, None

    async def _poll(self, credential: str) -> RemoteActionRecord | None:
        response = await self._request(
            "POST",
            "/remote-actions/poll",
            credential=credential,
        )
        if response.status_code == 401:
            return None
        response.raise_for_status()
        return RemoteActionPollResponse.model_validate(response.json()).action

    async def _complete(self, credential: str, action_id: str, payload: RemoteActionCompletionRequest):
        response = await self._request(
            "POST",
            f"/remote-actions/{action_id}/complete",
            credential=credential,
            json=payload.model_dump(),
        )
        response.raise_for_status()
        from nebula.models.deployment import RemoteActionCompletionResponse

        return RemoteActionCompletionResponse.model_validate(response.json())

    async def _request(
        self,
        method: str,
        path: str,
        credential: str,
        json: dict | None = None,
    ) -> httpx.Response:
        client_kwargs: dict = {"timeout": 10.0}
        if self._http_transport is not None:
            client_kwargs["transport"] = self._http_transport
        async with httpx.AsyncClient(**client_kwargs) as client:
            return await client.request(
                method,
                _remote_management_url(self.settings.hosted_plane_url, path),
                json=json,
                headers={"X-Nebula-Deployment-Credential": credential},
            )
