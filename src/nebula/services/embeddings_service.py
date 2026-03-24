from __future__ import annotations

from dataclasses import dataclass

import httpx

from nebula.core.config import Settings


class EmbeddingsServiceError(Exception):
    """Base error for explicit embeddings service failure modes."""


class EmbeddingsValidationError(EmbeddingsServiceError):
    """Raised when the caller supplies unsupported or blank input."""


class EmbeddingsUpstreamError(EmbeddingsServiceError):
    """Raised when the upstream embeddings provider fails."""


class EmbeddingsEmptyResultError(EmbeddingsServiceError):
    """Raised when the upstream provider returns no usable embeddings."""


@dataclass(frozen=True)
class EmbeddingVector:
    index: int
    embedding: list[float]


@dataclass(frozen=True)
class EmbeddingsResult:
    model: str
    data: list[EmbeddingVector]


class OllamaEmbeddingsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=self.settings.ollama_base_url,
            timeout=httpx.Timeout(60.0, connect=5.0),
        )

    async def embed(self, text: str) -> list[float] | None:
        if not text.strip():
            return None

        try:
            result = await self.create_embeddings(
                model=self.settings.embedding_model,
                input=text,
            )
        except EmbeddingsServiceError:
            return None

        return result.data[0].embedding

    async def create_embeddings(
        self,
        *,
        model: str,
        input: str | list[str],
    ) -> EmbeddingsResult:
        normalized_input = self._normalize_input(input)

        try:
            response = await self.client.post(
                "/api/embed",
                json={
                    "model": model,
                    "input": normalized_input if len(normalized_input) > 1 else normalized_input[0],
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingsUpstreamError("Ollama embeddings request failed.") from exc

        body = response.json()
        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingsEmptyResultError("Ollama returned no embeddings.")
        if len(embeddings) != len(normalized_input):
            raise EmbeddingsEmptyResultError(
                "Ollama returned an unexpected number of embeddings."
            )

        ordered_vectors: list[EmbeddingVector] = []
        for index, vector in enumerate(embeddings):
            if not isinstance(vector, list) or not vector:
                raise EmbeddingsEmptyResultError(
                    "Ollama returned an empty or invalid embedding vector."
                )
            if not all(isinstance(value, int | float) for value in vector):
                raise EmbeddingsEmptyResultError(
                    "Ollama returned a non-numeric embedding vector."
                )
            ordered_vectors.append(
                EmbeddingVector(index=index, embedding=[float(value) for value in vector])
            )

        return EmbeddingsResult(model=model, data=ordered_vectors)

    def _normalize_input(self, input: str | list[str]) -> list[str]:
        if isinstance(input, str):
            if not input.strip():
                raise EmbeddingsValidationError("Embedding input must not be blank.")
            return [input]

        if not input:
            raise EmbeddingsValidationError("Embedding input list must not be empty.")

        normalized: list[str] = []
        for item in input:
            if not isinstance(item, str):
                raise EmbeddingsValidationError("Embedding input list must contain only strings.")
            if not item.strip():
                raise EmbeddingsValidationError(
                    "Embedding input list entries must not be blank."
                )
            normalized.append(item)
        return normalized

    async def close(self) -> None:
        await self.client.aclose()

    async def health_status(self) -> dict[str, object]:
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {
                "status": "degraded",
                "required": False,
                "detail": f"Local Ollama unavailable: {exc}",
            }
        return {
            "status": "ready",
            "required": False,
            "detail": "Local Ollama endpoint is reachable.",
        }
