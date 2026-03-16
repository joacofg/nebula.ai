from __future__ import annotations

import httpx

from nebula.core.config import Settings


class PremiumProviderHealthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    async def health_status(self) -> dict[str, object]:
        if self.settings.premium_provider == "mock":
            return {
                "status": "ready",
                "required": False,
                "detail": "Mock premium provider configured for local development.",
            }

        try:
            client = self._client or httpx.AsyncClient(
                base_url=self.settings.premium_base_url or "https://api.openai.com/v1",
                timeout=httpx.Timeout(5.0, connect=2.0),
            )
            if self._client is None:
                self._client = client
            response = await client.get(
                "/models",
                headers={
                    "Authorization": f"Bearer {self.settings.premium_api_key}",
                },
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "degraded",
                "required": False,
                "detail": str(exc),
            }

        return {
            "status": "ready",
            "required": False,
            "detail": "Premium provider responded to GET /models.",
        }

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
