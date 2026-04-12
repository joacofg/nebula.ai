from __future__ import annotations

from fastapi.testclient import TestClient

from nebula.api.dependencies import get_embeddings_service
from tests.support import auth_headers, configured_app


class StubEmbeddingsResult:
    def __init__(self, *, model: str, vectors: list[list[float]]) -> None:
        self.model = model
        self.data = [
            type("EmbeddingVector", (), {"index": index, "embedding": vector})
            for index, vector in enumerate(vectors)
        ]


class StubEmbeddingsService:
    def __init__(self, *, result: StubEmbeddingsResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def create_embeddings(self, *, model: str, input: str | list[str]):
        self.calls.append({"model": model, "input": input})
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result

    async def close(self) -> None:
        return None


def test_embeddings_api_accepts_authenticated_single_and_batch_requests() -> None:
    with configured_app() as app:
        service = StubEmbeddingsService(
            result=StubEmbeddingsResult(
                model="nomic-embed-text",
                vectors=[[0.1, 0.2]],
            )
        )
        app.dependency_overrides[get_embeddings_service] = lambda: service

        with TestClient(app) as client:
            single = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": "hello world"},
            )

        batch_service = StubEmbeddingsService(
            result=StubEmbeddingsResult(
                model="nomic-embed-text",
                vectors=[[0.1, 0.2], [0.3, 0.4]],
            )
        )
        app.dependency_overrides[get_embeddings_service] = lambda: batch_service

        with TestClient(app) as client:
            batch = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": ["first", "second"]},
            )

        app.dependency_overrides.clear()

    assert single.status_code == 200
    assert single.headers["X-Request-ID"]
    assert single.json() == {
        "object": "list",
        "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
        "model": "nomic-embed-text",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
    assert batch.status_code == 200
    assert batch.json() == {
        "object": "list",
        "data": [
            {"object": "embedding", "index": 0, "embedding": [0.1, 0.2]},
            {"object": "embedding", "index": 1, "embedding": [0.3, 0.4]},
        ],
        "model": "nomic-embed-text",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
    assert service.calls == [{"model": "nomic-embed-text", "input": "hello world"}]
    assert batch_service.calls == [
        {"model": "nomic-embed-text", "input": ["first", "second"]},
    ]


def test_embeddings_api_reuses_existing_auth_contract() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            missing = client.post(
                "/v1/embeddings",
                json={"model": "nomic-embed-text", "input": "hello"},
            )
            invalid = client.post(
                "/v1/embeddings",
                headers=auth_headers(api_key="invalid-key"),
                json={"model": "nomic-embed-text", "input": "hello"},
            )

    assert missing.status_code == 401
    assert missing.json() == {"detail": "Missing client API key."}
    assert invalid.status_code == 401
    assert invalid.json() == {"detail": "Invalid client API key."}


def test_embeddings_api_rejects_unsupported_shapes_before_runtime() -> None:
    with configured_app() as app:
        with TestClient(app) as client:
            nested = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": [["nested"]]},
            )
            extra_option = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": "hello", "encoding_format": "base64"},
            )

    assert nested.status_code == 422
    assert extra_option.status_code == 422


def test_embeddings_api_maps_upstream_failures_to_bad_gateway() -> None:
    from nebula.services.embeddings_service import EmbeddingsUpstreamError

    with configured_app() as app:
        app.dependency_overrides[get_embeddings_service] = lambda: StubEmbeddingsService(
            error=EmbeddingsUpstreamError("Ollama embeddings request failed.")
        )
        with TestClient(app) as client:
            response = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": "hello"},
            )

        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "Ollama embeddings request failed."}


def test_embeddings_api_persist_governed_ledger_markers_from_tenant_policy() -> None:
    with configured_app() as app:
        service = StubEmbeddingsService(
            result=StubEmbeddingsResult(
                model="nomic-embed-text",
                vectors=[[0.1, 0.2]],
            )
        )
        app.dependency_overrides[get_embeddings_service] = lambda: service

        with TestClient(app) as client:
            app.state.container.governance_store.upsert_policy(
                "default",
                app.state.container.governance_store.get_policy("default").model_copy(
                    update={
                        "evidence_retention_window": "24h",
                        "metadata_minimization_level": "strict",
                    }
                ),
            )
            response = client.post(
                "/v1/embeddings",
                headers=auth_headers(),
                json={"model": "nomic-embed-text", "input": "hello world"},
            )
            request_id = response.headers["X-Request-ID"]
            ledger = client.get(
                f"/v1/admin/usage/ledger?request_id={request_id}",
                headers={"X-Nebula-Admin-Key": "nebula-admin-key"},
            )

        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert ledger.status_code == 200
    body = ledger.json()
    assert len(body) == 1
    row = body[0]
    assert row["request_id"] == request_id
    assert row["message_type"] == "embeddings"
    assert row["evidence_retention_window"] == "24h"
    assert row["metadata_minimization_level"] == "strict"
    assert row["metadata_fields_suppressed"] == []
    assert row["route_signals"] is None
    assert row["governance_source"] == "tenant_policy"
    assert row["evidence_expires_at"] is not None
