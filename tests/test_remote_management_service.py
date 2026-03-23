from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from nebula.db.models import DeploymentModel, DeploymentRemoteActionModel, LocalHostedIdentityModel
from nebula.models.deployment import EnrollmentExchangeResponse, RemoteActionRecord
from nebula.providers.base import CompletionResult
from tests.support import (
    FakeCacheService,
    StubProvider,
    admin_headers,
    auth_headers,
    configured_app,
    usage,
)


def _deployment_headers(credential: str) -> dict[str, str]:
    return {"X-Nebula-Deployment-Credential": credential}


def _exchange_payload(capability_flags: list[str] | None = None) -> dict[str, object]:
    return {
        "enrollment_token": "",
        "nebula_version": "2.0.0",
        "capability_flags": capability_flags or ["semantic_cache"],
    }


@asynccontextmanager
async def configured_async_client(**env_overrides: str):
    with configured_app(**env_overrides) as app:
        transport = httpx.ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            if hasattr(app.state.container, "gateway_enrollment_service"):
                app.state.container.gateway_enrollment_service._http_transport = transport
            if hasattr(app.state.container, "remote_management_service"):
                app.state.container.remote_management_service._http_transport = transport
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=True,
            ) as client:
                yield app, client


async def _create_active_deployment(
    app: FastAPI,
    client: httpx.AsyncClient,
    capability_flags: list[str] | None = None,
) -> tuple[str, str]:
    create_resp = await client.post(
        "/v1/admin/deployments",
        json={"display_name": "remote-gw", "environment": "production"},
        headers=admin_headers(),
    )
    assert create_resp.status_code == 201
    deployment_id = create_resp.json()["id"]

    token_resp = await client.post(
        f"/v1/admin/deployments/{deployment_id}/enrollment-token",
        headers=admin_headers(),
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["token"]

    payload = _exchange_payload(capability_flags)
    payload["enrollment_token"] = token
    exchange_resp = await client.post("/v1/enrollment/exchange", json=payload)
    assert exchange_resp.status_code == 200
    exchange = EnrollmentExchangeResponse.model_validate(exchange_resp.json())
    app.state.container.gateway_enrollment_service._store_local_identity(exchange)
    credential = exchange.deployment_credential
    return deployment_id, credential


async def _queue_rotation_action(
    client: httpx.AsyncClient,
    deployment_id: str,
    note: str = "rotate now",
) -> str:
    response = await client.post(
        f"/v1/admin/deployments/{deployment_id}/remote-actions/rotate-credential",
        json={"note": note},
        headers=admin_headers(),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _session_factory(app: FastAPI) -> sessionmaker:
    db_url = app.state.container.settings.database_url
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine)


def _install_serving_stubs(app: FastAPI) -> None:
    container = app.state.container
    container.local_provider = StubProvider(
        "ollama",
        completion_result=CompletionResult(
            content="remote-management outage-safe response",
            model=container.settings.local_model,
            provider="ollama",
            usage=usage(),
        ),
    )
    container.provider_registry.local_provider = container.local_provider
    container.cache_service = FakeCacheService()
    container.chat_service.cache_service = container.cache_service


@pytest.mark.asyncio
async def test_poll_valid_credential_returns_next_queued_action_and_marks_in_progress() -> None:
    async with configured_async_client() as (app, client):
        deployment_id, credential = await _create_active_deployment(app, client)
        action_id = await _queue_rotation_action(client, deployment_id)

        response = await client.post(
            "/v1/remote-actions/poll",
            headers=_deployment_headers(credential),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["action"]["id"] == action_id
        assert body["action"]["status"] == "in_progress"

        Session = _session_factory(app)
        with Session() as session:
            action = session.get(DeploymentRemoteActionModel, action_id)
            assert action is not None
            assert action.status == "in_progress"
            assert action.started_at is not None


@pytest.mark.asyncio
async def test_allowlist_failure_completes_action_as_failed_with_unauthorized_local_policy() -> None:
    async with configured_async_client(
        NEBULA_HOSTED_PLANE_URL="http://testserver/v1",
        NEBULA_REMOTE_MANAGEMENT_ENABLED="true",
    ) as (app, client):
        deployment_id, _ = await _create_active_deployment(app, client)
        action_id = await _queue_rotation_action(client, deployment_id)

        await app.state.container.remote_management_service.poll_and_apply_once()

        Session = _session_factory(app)
        with Session() as session:
            action = session.get(DeploymentRemoteActionModel, action_id)
            assert action is not None
            assert action.status == "failed"
            assert action.failure_reason == "unauthorized_local_policy"


@pytest.mark.asyncio
async def test_successful_rotation_returns_new_credential_and_follow_up_poll_accepts_it() -> None:
    async with configured_async_client(
        NEBULA_HOSTED_PLANE_URL="http://testserver/v1",
        NEBULA_REMOTE_MANAGEMENT_ENABLED="true",
        NEBULA_REMOTE_MANAGEMENT_ALLOWED_ACTIONS='["rotate_deployment_credential"]',
    ) as (app, client):
        deployment_id, old_credential = await _create_active_deployment(app, client)
        action_id = await _queue_rotation_action(client, deployment_id)

        await app.state.container.remote_management_service.poll_and_apply_once()

        Session = _session_factory(app)
        with Session() as session:
            action = session.get(DeploymentRemoteActionModel, action_id)
            assert action is not None
            assert action.status == "applied"
            assert action.result_credential_prefix is not None

            identity = session.scalars(
                select(LocalHostedIdentityModel).where(LocalHostedIdentityModel.unlinked_at.is_(None))
            ).first()
            assert identity is not None
            assert identity.credential_raw != old_credential
            assert identity.credential_prefix == identity.credential_raw[:12]
            new_credential = identity.credential_raw

        second_action_id = await _queue_rotation_action(client, deployment_id, note="rotate again")

        old_poll = await client.post(
            "/v1/remote-actions/poll",
            headers=_deployment_headers(old_credential),
        )
        assert old_poll.status_code == 401

        new_poll = await client.post(
            "/v1/remote-actions/poll",
            headers=_deployment_headers(new_credential),
        )
        assert new_poll.status_code == 200
        assert new_poll.json()["action"]["id"] == second_action_id


@pytest.mark.asyncio
async def test_failed_completion_keeps_old_credential_active_and_records_failure_reason() -> None:
    async with configured_async_client() as (app, client):
        deployment_id, credential = await _create_active_deployment(app, client)
        action_id = await _queue_rotation_action(client, deployment_id)

        poll_resp = await client.post(
            "/v1/remote-actions/poll",
            headers=_deployment_headers(credential),
        )
        assert poll_resp.status_code == 200

        complete_resp = await client.post(
            f"/v1/remote-actions/{action_id}/complete",
            headers=_deployment_headers(credential),
            json={
                "status": "failed",
                "failure_reason": "apply_error",
                "failure_detail": "could not update local credential",
            },
        )

        assert complete_resp.status_code == 200
        assert complete_resp.json() == {
            "acknowledged": True,
            "new_deployment_credential": None,
        }

        heartbeat_resp = await client.post(
            "/v1/heartbeat",
            headers=_deployment_headers(credential),
            json={
                "nebula_version": "2.0.0",
                "capability_flags": ["semantic_cache"],
                "dependency_summary": {
                    "healthy": ["gateway"],
                    "degraded": [],
                    "unavailable": [],
                },
            },
        )
        assert heartbeat_resp.status_code == 200

        Session = _session_factory(app)
        with Session() as session:
            action = session.get(DeploymentRemoteActionModel, action_id)
            assert action is not None
            assert action.status == "failed"
            assert action.failure_reason == "apply_error"
            deployment = session.get(DeploymentModel, deployment_id)
            assert deployment is not None
            assert deployment.credential_prefix == credential[:12]


@pytest.mark.asyncio
async def test_disabled_remote_management_starts_poller_but_skips_polling() -> None:
    async with configured_async_client(
        NEBULA_HOSTED_PLANE_URL="http://testserver/v1",
        NEBULA_REMOTE_MANAGEMENT_ENABLED="false",
    ) as (app, client):
        deployment_id, _ = await _create_active_deployment(app, client)
        action_id = await _queue_rotation_action(client, deployment_id)

        assert app.state.container.remote_management_service._task is not None
        await app.state.container.remote_management_service._poll_once()

        Session = _session_factory(app)
        with Session() as session:
            action = session.get(DeploymentRemoteActionModel, action_id)
            assert action is not None
            assert action.status == "queued"


@pytest.mark.asyncio
async def test_hosted_outage_leaves_remote_action_queued_and_serving_unaffected() -> None:
    async with configured_async_client(
        NEBULA_HOSTED_PLANE_URL="http://hosted.invalid/v1",
        NEBULA_REMOTE_MANAGEMENT_ENABLED="true",
        NEBULA_REMOTE_MANAGEMENT_ALLOWED_ACTIONS='["rotate_deployment_credential"]',
        NEBULA_PREMIUM_PROVIDER="mock",
    ) as (app, client):
        deployment_id, _credential = await _create_active_deployment(app, client)
        action_id = await _queue_rotation_action(client, deployment_id)
        _install_serving_stubs(app)

        def outage_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("hosted outage", request=request)

        app.state.container.remote_management_service._http_transport = httpx.MockTransport(
            outage_handler
        )

        await app.state.container.remote_management_service.poll_and_apply_once()

        Session = _session_factory(app)
        with Session() as session:
            action = session.get(DeploymentRemoteActionModel, action_id)
            assert action is not None
            assert action.status == "queued"
            assert action.started_at is None
            assert action.finished_at is None

        chat_response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {"role": "user", "content": "hosted outage should not break local serving"}
                ],
            },
        )

    assert chat_response.status_code == 200


@pytest.mark.asyncio
async def test_missing_local_identity_reports_invalid_state_failure_reason() -> None:
    async with configured_async_client(
        NEBULA_HOSTED_PLANE_URL="http://hosted.invalid/v1",
        NEBULA_REMOTE_MANAGEMENT_ENABLED="true",
        NEBULA_REMOTE_MANAGEMENT_ALLOWED_ACTIONS='["rotate_deployment_credential"]',
    ) as (app, client):
        deployment_id, _credential = await _create_active_deployment(app, client)
        app.state.container.gateway_enrollment_service.clear_local_identity()

        action = RemoteActionRecord(
            id="test-action",
            deployment_id=deployment_id,
            action_type="rotate_deployment_credential",
            status="queued",
            note="rotate now",
            requested_at=datetime.now().isoformat(),
            expires_at=datetime.now().isoformat(),
            started_at=None,
            finished_at=None,
            failure_reason=None,
            failure_detail=None,
            result_credential_prefix=None,
        )

        allowed, failure_reason, failure_detail = (
            app.state.container.remote_management_service._authorize(action)
        )

    assert (allowed, failure_reason, failure_detail) == (
        False,
        "invalid_state",
        "No active local hosted identity exists.",
    )
