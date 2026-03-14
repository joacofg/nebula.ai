from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from nebula.providers.base import CompletionUsage


@dataclass(slots=True)
class ModelPricing:
    input_cost_per_1m_tokens: float
    output_cost_per_1m_tokens: float


class PricingCatalog:
    def __init__(self, models: dict[str, ModelPricing]) -> None:
        self.models = models

    @classmethod
    def from_path(cls, path: Path) -> "PricingCatalog":
        body = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            models={
                name: ModelPricing(
                    input_cost_per_1m_tokens=pricing["input_cost_per_1m_tokens"],
                    output_cost_per_1m_tokens=pricing["output_cost_per_1m_tokens"],
                )
                for name, pricing in body["models"].items()
            }
        )

    def has_pricing(self, model: str) -> bool:
        return self._resolve_model(model) is not None

    def estimate_cost(self, model: str, usage: CompletionUsage | None) -> float | None:
        if usage is None:
            return None

        resolved_model = self._resolve_model(model)
        if resolved_model is None:
            return None

        if resolved_model.input_cost_per_1m_tokens == 0 and resolved_model.output_cost_per_1m_tokens == 0:
            return 0.0

        return (
            usage.prompt_tokens / 1_000_000 * resolved_model.input_cost_per_1m_tokens
            + usage.completion_tokens / 1_000_000 * resolved_model.output_cost_per_1m_tokens
        )

    def _resolve_model(self, model: str) -> ModelPricing | None:
        if model in self.models:
            return self.models[model]
        if model.endswith(":free"):
            return ModelPricing(input_cost_per_1m_tokens=0.0, output_cost_per_1m_tokens=0.0)
        normalized_model = model.split("/", maxsplit=1)[-1]
        return self.models.get(normalized_model)
