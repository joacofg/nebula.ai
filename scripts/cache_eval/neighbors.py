"""Corpus neighbors: pairs of distinct Spanish corpus prompts that the cache would confuse.

Set (b) of ``benchmarks/cache/v1/preregistration.md``: every pair among the 1000 Spanish
prompts whose production-embedding cosine is at least 0.85. Descriptive only; the labels a
human gives them never enter the verdict.

    python -m scripts.cache_eval.neighbors

reads the production vectors (``nomic-embed-text``, no prefix) that the router stage already
computed for the corpus, ``artifacts/router-embeddings/none.json`` (regenerate it with
``python -m scripts.router.embed``), and writes ``benchmarks/cache/v1/neighbors/pairs.jsonl``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from scripts.ground_truth import records

MIN_COS = 0.85
DECLARED_COS = 0.90  # the pre-registration declares 20 Spanish pairs at or above this cosine
PROMPTS_PATH = Path("benchmarks/ground-truth/v1/prompts.es.jsonl")
VECTORS_PATH = Path("artifacts/router-embeddings/none.json")
OUT_PATH = Path("benchmarks/cache/v1/neighbors/pairs.jsonl")


@dataclass(frozen=True)
class NeighborPair:
    a_id: str
    b_id: str
    cosine: float


def find_pairs(vectors: dict[str, list[float]], *, min_cos: float) -> list[NeighborPair]:
    """Every pair of distinct ids with cosine >= min_cos, ids in sorted order (a_id < b_id),
    most similar first (ties by id)."""
    ids = sorted(vectors)
    if len(ids) < 2:
        return []
    matrix = np.array([vectors[i] for i in ids], dtype=np.float64)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if (norms == 0.0).any():
        raise ValueError("Cannot compare a zero vector.")
    unit = matrix / norms
    similarity = unit @ unit.T
    rows, cols = np.nonzero(np.triu(similarity >= min_cos, k=1))
    pairs = [NeighborPair(ids[i], ids[j], float(similarity[i, j])) for i, j in zip(rows, cols)]
    return sorted(pairs, key=lambda p: (-p.cosine, p.a_id, p.b_id))


def pair_records(pairs: list[NeighborPair], texts: dict[str, str]) -> list[dict]:
    """Rows of ``neighbors/pairs.jsonl``."""
    return [
        {
            "pair_id": f"{p.a_id}|{p.b_id}",
            "a_id": p.a_id,
            "b_id": p.b_id,
            "a": texts[p.a_id],
            "b": texts[p.b_id],
            "cos_nomic_v1": p.cosine,
        }
        for p in pairs
    ]


def main() -> int:
    prompts = records.read_rows(PROMPTS_PATH, records.PromptRow)
    texts = {f"es:{row.prompt_id}": row.prompt for row in prompts}
    stored = json.loads(VECTORS_PATH.read_text())
    vectors = {key: stored[key] for key in texts}  # a missing vector is an error, not a skip

    pairs = find_pairs(vectors, min_cos=MIN_COS)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for record in pair_records(pairs, texts):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    declared = sum(1 for p in pairs if p.cosine >= DECLARED_COS)
    print(f"{len(vectors)} Spanish prompts: {len(pairs)} pairs at cosine >= {MIN_COS} "
          f"({declared} at >= {DECLARED_COS}) -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
