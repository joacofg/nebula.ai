from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.services.embeddings_service import EmbeddingsResult, EmbeddingVector
from tests.support import admin_headers, configured_app


MIGRATED_EMBEDDINGS_REQUEST = {
    "model": "nomic-embed-text",
    "input": [
        "minimal migration keeps the provider-style request body",
        "only the base URL and auth header change",
    ],
}


def test_embeddings_reference_migration_proves_public_headers_and_usage_ledger_correlation() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            async def stub_create_embeddings(*, model: str, input: str | list[str]) -> EmbeddingsResult:
                inputs = [input] if isinstance(input, str) else input
                return EmbeddingsResult(
                    model=model,
                    data=[
                        EmbeddingVector(index=index, embedding=[float(index), float(index) + 0.25])
                        for index, _ in enumerate(inputs)
                    ],
                )

            app.state.container.embeddings_service.create_embeddings = stub_create_embeddings

            response = client.post(
                "/v1/embeddings",
                headers={"X-Nebula-API-Key": "nebula-dev-key"},
                json=MIGRATED_EMBEDDINGS_REQUEST,
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers=admin_headers(),
            )

    body = response.json()
    ledger_body = ledger.json()

    assert response.status_code == 200
    assert body == {
        "object": "list",
        "data": [
            {"object": "embedding", "index": 0, "embedding": [0.0, 0.25]},
            {"object": "embedding", "index": 1, "embedding": [1.0, 1.25]},
        ],
        "model": "nomic-embed-text",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }

    public_evidence = {
        "request_id": request_id,
        "tenant_id": response.headers["X-Nebula-Tenant-ID"],
        "route_target": response.headers["X-Nebula-Route-Target"],
        "route_reason": response.headers["X-Nebula-Route-Reason"],
        "provider": response.headers["X-Nebula-Provider"],
        "cache_hit": response.headers["X-Nebula-Cache-Hit"],
        "fallback_used": response.headers["X-Nebula-Fallback-Used"],
        "policy_mode": response.headers["X-Nebula-Policy-Mode"],
        "policy_outcome": response.headers["X-Nebula-Policy-Outcome"],
    }

    assert public_evidence == {
        "request_id": request_id,
        "tenant_id": "default",
        "route_target": "embeddings",
        "route_reason": "embeddings_direct",
        "provider": "ollama",
        "cache_hit": "false",
        "fallback_used": "false",
        "policy_mode": "embeddings_direct",
        "policy_outcome": "embeddings=completed",
    }

    assert ledger.status_code == 200
    assert len(ledger_body) == 1
    assert ledger_body[0]["request_id"] == public_evidence["request_id"]
    assert ledger_body[0]["tenant_id"] == public_evidence["tenant_id"]
    assert ledger_body[0]["requested_model"] == MIGRATED_EMBEDDINGS_REQUEST["model"]
    assert ledger_body[0]["final_route_target"] == public_evidence["route_target"]
    assert ledger_body[0]["final_provider"] == public_evidence["provider"]
    assert ledger_body[0]["fallback_used"] is False
    assert ledger_body[0]["cache_hit"] is False
    assert ledger_body[0]["response_model"] == body["model"]
    assert ledger_body[0]["prompt_tokens"] == body["usage"]["prompt_tokens"]
    assert ledger_body[0]["completion_tokens"] == 0
    assert ledger_body[0]["total_tokens"] == body["usage"]["total_tokens"]
    assert ledger_body[0]["terminal_status"] == "completed"
    assert ledger_body[0]["route_reason"] == public_evidence["route_reason"]
    assert ledger_body[0]["policy_outcome"] == public_evidence["policy_outcome"]

    assert "input" not in ledger_body[0]
    assert "inputs" not in ledger_body[0]
    assert "embedding" not in ledger_body[0]
    assert "embeddings" not in ledger_body[0]
    assert MIGRATED_EMBEDDINGS_REQUEST["input"][0] not in str(ledger_body[0])
    assert MIGRATED_EMBEDDINGS_REQUEST["input"][1] not in str(ledger_body[0])
    assert str(body["data"][0]["embedding"]) not in str(ledger_body[0])
    assert str(body["data"][1]["embedding"]) not in str(ledger_body[0])
