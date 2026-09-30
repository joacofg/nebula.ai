"""Runtime half of the learned router: a vector and a quality target in, a tier out.

Two logistic models score the latest user prompt's embedding: the probability
that the local model's answer would serve the reader as well as the frontier
model's, and the same for the economy model. A cascade over two thresholds
turns those into a tier. The thresholds come in pairs — operating points
measured out of fold during training — and a tenant picks one by stating the
quality it needs; the router takes the cheapest point that meets it.

Stdlib only: training needs numpy, serving a dot product does not.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Tier = Literal["local", "economy", "frontier"]
ARTIFACT_VERSION = 1


@dataclass(frozen=True, slots=True)
class OperatingPoint:
    tau_local: float
    tau_economy: float
    quality: float
    cost_per_prompt: float


# A target no measured point reaches: every prompt goes to the frontier model.
ALL_FRONTIER = OperatingPoint(
    tau_local=math.inf, tau_economy=math.inf, quality=1.0, cost_per_prompt=math.nan
)


@dataclass(frozen=True, slots=True)
class TierChoice:
    tier: Tier
    p_local: float
    p_economy: float
    point: OperatingPoint


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def tier_for(p_local: float, p_economy: float, point: OperatingPoint) -> Tier:
    if p_local >= point.tau_local:
        return "local"
    if p_economy >= point.tau_economy:
        return "economy"
    return "frontier"


@dataclass(frozen=True, slots=True)
class _Linear:
    weights: tuple[float, ...]
    bias: float

    def score(self, vector: Sequence[float]) -> float:
        return sum(w * x for w, x in zip(self.weights, vector, strict=True)) + self.bias


class LearnedRouterModel:
    def __init__(
        self,
        *,
        version: str,
        embedding_model: str,
        prefix: str,
        local: _Linear,
        economy: _Linear,
        points: list[OperatingPoint],
    ) -> None:
        self.version = version
        self.embedding_model = embedding_model
        self.prefix = prefix
        self._local = local
        self._economy = economy
        self._points = sorted(points, key=lambda p: (p.cost_per_prompt, -p.quality))

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LearnedRouterModel":
        if raw.get("version") != ARTIFACT_VERSION:
            raise ValueError(f"Unsupported learned-router artifact version {raw.get('version')!r}.")
        models = raw["models"]
        local = _Linear(tuple(float(w) for w in models["local"]["weights"]), float(models["local"]["bias"]))
        economy = _Linear(
            tuple(float(w) for w in models["economy"]["weights"]), float(models["economy"]["bias"])
        )
        if len(local.weights) != len(economy.weights) or not local.weights:
            raise ValueError("Learned-router models must share a non-zero dimension.")
        points = [
            OperatingPoint(
                tau_local=float(p["tau_local"]),
                tau_economy=float(p["tau_economy"]),
                quality=float(p["quality"]),
                cost_per_prompt=float(p["cost_per_prompt"]),
            )
            for p in raw.get("operating_points", [])
        ]
        if not points:
            raise ValueError("Learned-router artifact has no operating points.")
        return cls(
            version=str(raw.get("label", f"v{ARTIFACT_VERSION}")),
            embedding_model=str(raw["embedding_model"]),
            prefix=str(raw.get("prefix", "none")),
            local=local,
            economy=economy,
            points=points,
        )

    @classmethod
    def from_file(cls, path: Path | str) -> "LearnedRouterModel":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def dimension(self) -> int:
        return len(self._local.weights)

    def probabilities(self, vector: Sequence[float]) -> tuple[float, float]:
        if len(vector) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(vector)} does not match the router's {self.dimension}."
            )
        return _sigmoid(self._local.score(vector)), _sigmoid(self._economy.score(vector))

    def operating_point(self, quality_target: float) -> OperatingPoint:
        # A measured quality of 1.0 means no cheap pick failed out of fold, not
        # that none can: a tenant asking for perfection gets the reference model.
        if quality_target >= 1.0:
            return ALL_FRONTIER
        for point in self._points:
            if point.quality >= quality_target:
                return point
        return ALL_FRONTIER

    def choose(self, vector: Sequence[float], quality_target: float) -> TierChoice:
        p_local, p_economy = self.probabilities(vector)
        point = self.operating_point(quality_target)
        return TierChoice(tier_for(p_local, p_economy, point), p_local, p_economy, point)
