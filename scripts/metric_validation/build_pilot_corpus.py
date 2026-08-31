"""Capture the pilot corpus: run every prompt, embed the answers, write the pairs.

    python -m scripts.metric_validation.build_pilot_corpus --premium-b-model <model>

Capture is resumable. Responses land in a per-role cache as they arrive, so a
rate limit partway through costs nothing already paid for; re-running picks up
where it stopped.

The corpus is stratified under the provisional prefix only. Which task prefix
the study actually adopts is decided after labelling, by the sweep in
``analyse``, so that the choice cannot be read off the stratification.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from scripts.metric_validation import capture, corpus

DEFAULT_ROOT = Path("benchmarks/metric-validation")
DEFAULT_LOCAL_MODEL = "llama3.2:3b"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
TEMPERATURE = 0.0


def load_dotenv(path: Path = Path(".env")) -> None:
    """Fill in unset variables from .env, without adding a dependency."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_prompts(path: Path) -> list[capture.PromptRecord]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw = json.loads(line)
            records.append(
                capture.PromptRecord(
                    prompt_id=raw["prompt_id"],
                    task_type=raw["task_type"],
                    prompt=raw["prompt"],
                )
            )
    return records


def ollama_completer(client: httpx.AsyncClient, model: str) -> capture.Complete:
    async def complete(prompt: str) -> str:
        response = await client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": TEMPERATURE},
            },
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    return complete


def premium_completer(client: httpx.AsyncClient, model: str) -> capture.Complete:
    async def complete(prompt: str) -> str:
        response = await client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": TEMPERATURE,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    return complete


def ollama_embedder(client: httpx.AsyncClient, model: str, batch_size: int) -> capture.Embed:
    async def embed(texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            chunk = texts[start : start + batch_size]
            response = await client.post("/api/embed", json={"model": model, "input": chunk})
            response.raise_for_status()
            vectors.extend(response.json()["embeddings"])
        return vectors

    return embed


async def model_digests(client: httpx.AsyncClient) -> dict[str, str]:
    """Pin exactly which weights produced this corpus."""
    response = await client.get("/api/tags")
    response.raise_for_status()
    return {entry["model"]: entry.get("digest", "") for entry in response.json().get("models", [])}


async def build(args: argparse.Namespace) -> int:
    load_dotenv()

    provider = os.environ.get("NEBULA_PREMIUM_PROVIDER", "")
    base_url = os.environ.get("NEBULA_PREMIUM_BASE_URL", "")
    api_key = os.environ.get("NEBULA_PREMIUM_API_KEY", "")
    premium_a_model = os.environ.get("NEBULA_PREMIUM_MODEL", "")

    capture.ensure_real_premium(provider=provider, base_url=base_url, model=premium_a_model)
    capture.ensure_real_premium(provider=provider, base_url=base_url, model=args.premium_b_model)
    if not api_key:
        raise RuntimeError("NEBULA_PREMIUM_API_KEY is unset; refusing to capture.")
    if args.premium_b_model == premium_a_model:
        raise RuntimeError(
            "The noise floor needs two different premium answers. "
            f"--premium-b-model matches NEBULA_PREMIUM_MODEL ({premium_a_model})."
        )

    root: Path = args.root
    cache_dir = root / "cache"
    records = read_prompts(root / "prompts.jsonl")
    print(f"{len(records)} prompts from {root / 'prompts.jsonl'}")

    async with (
        httpx.AsyncClient(
            base_url=os.environ.get("NEBULA_OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=httpx.Timeout(300.0, connect=5.0),
        ) as ollama,
        httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(180.0, connect=10.0),
        ) as premium,
    ):
        digests = await model_digests(ollama)
        version = (await ollama.get("/api/version")).json().get("version", "unknown")

        print(f"local  ({args.local_model}) …")
        local = await capture.capture_responses(
            records,
            complete=ollama_completer(ollama, args.local_model),
            cache_path=cache_dir / "local.jsonl",
        )
        print(f"premium A ({premium_a_model}) …")
        premium_a = await capture.capture_responses(
            records,
            complete=premium_completer(premium, premium_a_model),
            cache_path=cache_dir / "premium_a.jsonl",
        )
        print(f"premium B ({args.premium_b_model}) …")
        premium_b = await capture.capture_responses(
            records,
            complete=premium_completer(premium, args.premium_b_model),
            cache_path=cache_dir / "premium_b.jsonl",
        )

        texts = sorted({*local.values(), *premium_a.values(), *premium_b.values()})
        print(f"embedding {len(texts)} texts × {len(corpus.PREFIX_VARIANTS)} prefixes …")
        similarity = await capture.build_similarity(
            texts,
            embed=ollama_embedder(ollama, args.embedding_model, args.embed_batch),
        )

    pairs = capture.build_pairs(
        records,
        local=local,
        premium_a=premium_a,
        premium_b=premium_b,
        similarity=similarity,
        noise_floor_count=args.noise_floor,
        cross_prompt_count=args.cross_prompt,
        local_model=args.local_model,
        premium_a_model=premium_a_model,
        premium_b_model=args.premium_b_model,
    )

    pairs_path = root / "pairs.jsonl"
    corpus.write_pairs(pairs, pairs_path)

    provenance = {
        "captured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "prompts_sha256": sha256_of(root / "prompts.jsonl"),
        "pairs_sha256": sha256_of(pairs_path),
        "pair_counts": {
            kind: sum(1 for pair in pairs if pair.kind == kind) for kind in corpus.PAIR_KINDS
        },
        "temperature": TEMPERATURE,
        "provisional_prefix": corpus.PROVISIONAL_PREFIX,
        "prefix_variants": list(corpus.PREFIX_VARIANTS),
        "ollama_version": version,
        "local_model": args.local_model,
        "local_model_digest": digests.get(args.local_model, ""),
        "embedding_model": args.embedding_model,
        "embedding_model_digest": next(
            (digest for name, digest in digests.items() if name.startswith(args.embedding_model)),
            "",
        ),
        "premium_provider": provider,
        "premium_base_url": base_url,
        "premium_a_model": premium_a_model,
        "premium_b_model": args.premium_b_model,
    }
    (root / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"\n{len(pairs)} pairs → {pairs_path}")
    print(f"provenance → {root / 'provenance.json'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--local-model", default=DEFAULT_LOCAL_MODEL)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument(
        "--premium-b-model",
        required=True,
        help=(
            "second premium model, for the noise floor. Deliberately not defaulted: "
            "the ceiling this measures depends entirely on which model it is."
        ),
    )
    parser.add_argument("--noise-floor", type=int, default=25)
    parser.add_argument("--cross-prompt", type=int, default=25)
    parser.add_argument("--embed-batch", type=int, default=16)
    return asyncio.run(build(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
