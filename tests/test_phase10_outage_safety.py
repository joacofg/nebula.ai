from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nebula.db.models import DeploymentModel
from nebula.models.deployment import EnrollmentExchangeResponse
from nebula.providers.base import CompletionResult
from tests.support import (
    FakeCacheService,
    StubProvider,
    admin_headers,
    auth_headers,
    configured_app,
    usage,
)


def _hosted_outage_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if "heartbeat" in request.url.path:
            raise httpx.ConnectError("hosted outage", request=request)
        raise httpx.ReadTimeout("hosted outage", request=request)

    return httpx.MockTransport(handler)


@asynccontextmanager
async def configured_outage_client():
    with configured_app(
        NEBULA_HOSTED_PLANE_URL="http://hosted.invalid/v1",
        NEBULA_REMOTE_MANAGEMENT_ENABLED="true",
        NEBULA_REMOTE_MANAGEMENT_ALLOWED_ACTIONS='["rotate_deployment_credential"]',
        NEBULA_PREMIUM_PROVIDER="mock",
    ) as app:
        transport = httpx.ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            app.state.container.gateway_enrollment_service._http_transport = transport
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=True,
            ) as client:
                deployment_id, _ = await _create_active_deployment(app, client)
                _install_serving_stubs(app)
                outage_transport = _hosted_outage_transport()
                app.state.container.heartbeat_service._http_transport = outage_transport
                app.state.container.remote_management_service._http_transport = outage_transport
                yield app, client, deployment_id


async def _create_active_deployment(app: FastAPI, client: httpx.AsyncClient) -> tuple[str, str]:
    create_response = await client.post(
        "/v1/admin/deployments",
        json={"display_name": "phase10-gw", "environment": "production"},
        headers=admin_headers(),
    )
    assert create_response.status_code == 201
    deployment_id = create_response.json()["id"]

    token_response = await client.post(
        f"/v1/admin/deployments/{deployment_id}/enrollment-token",
        headers=admin_headers(),
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]

    exchange_response = await client.post(
        "/v1/enrollment/exchange",
        json={
            "enrollment_token": token,
            "nebula_version": "2.0.0",
            "capability_flags": ["semantic_cache"],
        },
    )
    assert exchange_response.status_code == 200
    exchange = EnrollmentExchangeResponse.model_validate(exchange_response.json())
    app.state.container.gateway_enrollment_service._store_local_identity(exchange)
    return deployment_id, exchange.deployment_credential


def _install_serving_stubs(app: FastAPI) -> None:
    container = app.state.container
    container.local_provider = StubProvider(
        "ollama",
        completion_result=CompletionResult(
            content="local outage-safe response",
            model=container.settings.local_model,
            provider="ollama",
            usage=usage(),
        ),
    )
    container.provider_registry.local_provider = container.local_provider
    container.cache_service = FakeCacheService()
    container.chat_service.cache_service = container.cache_service


def _session_factory(app: FastAPI) -> sessionmaker:
    engine = create_engine(
        app.state.container.settings.database_url,
        connect_args={"check_same_thread": False},
    )
    return sessionmaker(bind=engine)


def _set_last_seen_at(app: FastAPI, deployment_id: str, last_seen_at: datetime) -> None:
    Session = _session_factory(app)
    with Session() as session:
        deployment = session.get(DeploymentModel, deployment_id)
        assert deployment is not None
        deployment.last_seen_at = last_seen_at
        session.commit()


@pytest.mark.asyncio
async def test_hosted_outage_keeps_chat_completion_serving_and_readiness_green(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    async with configured_outage_client() as (app, client, _deployment_id):
        await app.state.container.heartbeat_service._send_once()
        await app.state.container.remote_management_service.poll_and_apply_once()

        response = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hosted outage should not block local serving",
                    }
                ],
            },
        )
        readiness = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.headers["X-Nebula-Route-Target"] == "local"
    assert response.headers["X-Nebula-Fallback-Used"] == "false"
    assert readiness.status_code == 200
    assert readiness.json()["status"] in {"ready", "degraded"}
    assert "Heartbeat failed:" in caplog.text
    assert "Remote management poll/apply failed:" in caplog.text


@pytest.mark.asyncio
async def test_stale_and_offline_hosted_visibility_do_not_imply_serving_failure() -> None:
    async with configured_outage_client() as (app, client, deployment_id):
        stale_time = datetime.now(UTC) - timedelta(minutes=45)
        _set_last_seen_at(app, deployment_id, stale_time)

        stale_response = await client.get(
            f"/v1/admin/deployments/{deployment_id}",
            headers=admin_headers(),
        )
        stale_chat = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {"role": "user", "content": "stale visibility should not break serving"}
                ],
            },
        )

        offline_time = datetime.now(UTC) - timedelta(hours=2)
        _set_last_seen_at(app, deployment_id, offline_time)

        offline_response = await client.get(
            f"/v1/admin/deployments/{deployment_id}",
            headers=admin_headers(),
        )
        offline_chat = await client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "nebula-auto",
                "messages": [
                    {"role": "user", "content": "offline visibility should not break serving"}
                ],
            },
        )

    assert stale_response.status_code == 200
    assert stale_response.json()["freshness_status"] == "stale"
    assert stale_chat.status_code == 200
    assert offline_response.status_code == 200
    assert offline_response.json()["freshness_status"] == "offline"
    assert offline_chat.status_code == 200
