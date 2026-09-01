"""Pilot corpus types and on-disk format for the metric-validation study.

A pair is one prompt and two candidate responses to it. The metric under test
scores the two responses against each other; the study asks humans to do the
same thing and then measures whether the two rankings agree.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

# Candidate task prefixes for nomic-embed-text. "none" is the provisional
# variant the corpus is stratified under; the sweep decides the winner after
# the labels are in, so that the choice cannot be read off the labels.
PREFIX_VARIANTS: tuple[str, ...] = ("none", "search_query", "search_document", "clustering")
PROVISIONAL_PREFIX = "none"

TASK_TYPES: tuple[str, ...] = (
    "factual_qa",
    "summarisation",
    "code",
    "multistep_reasoning",
    "open_writing",
)

PAIR_KINDS: tuple[str, ...] = (
    "local_vs_premium",
    "premium_vs_premium",
    "cross_prompt",
)

BAND_EDGES: tuple[float, ...] = (0.0, 0.5, 0.65, 0.8, 0.9, 1.01)


@dataclass(frozen=True)
class ResponseSide:
    origin: str
    model: str
    text: str


@dataclass(frozen=True)
class Pair:
    pair_id: str
    kind: str
    task_type: str
    prompt: str
    left: ResponseSide
    right: ResponseSide
    cosine: dict[str, float]
    band: str


def band_for(similarity: float) -> str:
    """Name the stratification band a similarity falls into."""
    for low, high in zip(BAND_EDGES, BAND_EDGES[1:], strict=False):
        if low <= similarity < high:
            return f"{low:.2f}-{min(high, 1.0):.2f}"
    raise ValueError(f"Similarity {similarity} falls outside the band edges.")


def write_pairs(pairs: list[Pair], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(asdict(pair), ensure_ascii=False, sort_keys=True) + "\n")


def read_pairs(path: Path) -> list[Pair]:
    pairs: list[Pair] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            pairs.append(
                Pair(
                    pair_id=raw["pair_id"],
                    kind=raw["kind"],
                    task_type=raw["task_type"],
                    prompt=raw["prompt"],
                    left=ResponseSide(**raw["left"]),
                    right=ResponseSide(**raw["right"]),
                    cosine=raw["cosine"],
                    band=raw["band"],
                )
            )
    return pairs
