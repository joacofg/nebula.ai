"""Embed every training prompt with nomic-embed-text, once per prefix variant.

    python -m scripts.router.embed

The gateway embeds the latest user message with no prefix for the semantic
cache; "none" is that same vector, so a router trained on it costs no extra
embedding at request time. "classification" is nomic's documented prefix for
this task, kept as the one alternative the training stage may choose.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from scripts.ground_truth import cli
from scripts.router import data

PREFIXES: tuple[str, ...] = ("none", "classification")
EMBEDDING_MODEL = "nomic-embed-text"
BATCH = 32
OUT_DIR = Path("artifacts/router-embeddings")


def apply_prefix(text: str, prefix: str) -> str:
    return text if prefix == "none" else f"{prefix}: {text}"


def embeddings_path(prefix: str) -> Path:
    return OUT_DIR / f"{prefix}.json"


def load_embeddings(prefix: str) -> dict[str, list[float]]:
    return json.loads(embeddings_path(prefix).read_text())


async def run() -> int:
    examples = data.load_examples(data.GROUND_TRUTH, "tiers.jsonl")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    async with cli.ollama_client() as client:
        for prefix in PREFIXES:
            path = embeddings_path(prefix)
            done: dict[str, list[float]] = json.loads(path.read_text()) if path.exists() else {}
            todo = [e for e in examples if e.key not in done]
            for start in range(0, len(todo), BATCH):
                chunk = todo[start : start + BATCH]
                response = await client.post("/api/embed", json={
                    "model": EMBEDDING_MODEL, "input": [apply_prefix(e.text, prefix) for e in chunk]})
                response.raise_for_status()
                for example, vector in zip(chunk, response.json()["embeddings"], strict=True):
                    done[example.key] = vector
                path.write_text(json.dumps(done))
            print(f"{prefix}: {len(done)} vectors → {path}")
        tags = (await client.get("/api/tags")).json().get("models", [])
    digest = next((m.get("digest", "") for m in tags if m["model"].startswith(EMBEDDING_MODEL)), "")
    (OUT_DIR / "provenance.json").write_text(json.dumps({"model": EMBEDDING_MODEL, "digest": digest}))
    return 0


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
