"""Embeddings for the cache evaluation: Ollama vectors, unit-normalized, cached on disk.

The cache holds one JSON file per model under ``artifacts/cache-eval/vectors/``, keyed by the
SHA-256 of the exact text, so re-running a stage never embeds the same text twice. No prefix is
ever added: the gateway embeds the latest user message as it is.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections.abc import Callable, Sequence
from pathlib import Path

import httpx

VECTORS_DIR = Path("artifacts/cache-eval/vectors")
BATCH = 32

Fetch = Callable[[str, list[str]], list[list[float]]]


def normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0:
        raise ValueError("Cannot normalize a zero vector.")
    return [x / norm for x in vector]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(normalize(a), normalize(b), strict=True))


def ollama_fetch(model: str, texts: list[str]) -> list[list[float]]:
    base_url = os.environ.get("NEBULA_OLLAMA_BASE_URL", "http://localhost:11434")
    response = httpx.post(
        f"{base_url}/api/embed",
        json={"model": model, "input": texts},
        timeout=httpx.Timeout(600.0, connect=5.0),
    )
    response.raise_for_status()
    vectors = response.json()["embeddings"]
    if len(vectors) != len(texts):
        raise RuntimeError(f"Ollama returned {len(vectors)} vectors for {len(texts)} texts.")
    return vectors


def _text_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cache_path(cache_dir: Path, model: str) -> Path:
    return cache_dir / f"{model.replace('/', '_').replace(':', '_')}.json"


def embed_texts(
    texts: list[str],
    *,
    model: str,
    cache_dir: Path = VECTORS_DIR,
    fetch: Fetch | None = None,
    batch: int = BATCH,
) -> list[list[float]]:
    """Unit-normalized vector of every text, in order; only texts missing from the cache are fetched."""
    fetch = fetch or ollama_fetch
    path = _cache_path(cache_dir, model)
    cached: dict[str, list[float]] = json.loads(path.read_text()) if path.exists() else {}

    todo = list(dict.fromkeys(t for t in texts if _text_key(t) not in cached))
    try:
        for start in range(0, len(todo), batch):
            chunk = todo[start : start + batch]
            for text, vector in zip(chunk, fetch(model, chunk), strict=True):
                cached[_text_key(text)] = normalize(vector)
    finally:
        if todo:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(cached))
    return [cached[_text_key(t)] for t in texts]
