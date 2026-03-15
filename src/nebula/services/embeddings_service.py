from __future__ import annotations

import httpx

from nebula.core.config import Settings


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
            response = await self.client.post(
                "/api/embed",
                json={
                    "model": self.settings.embedding_model,
                    "input": text,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        body = response.json()
        embeddings = body.get("embeddings") or []
        if not embeddings:
            return None
        return embeddings[0]

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
