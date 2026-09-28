"""Shared plumbing for the stage commands: paths, provenance, HTTP clients."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

from scripts.metric_validation.build_pilot_corpus import load_dotenv

DEFAULT_ROOT = Path("benchmarks/ground-truth/v1")
SOURCES_DIR = Path("artifacts/ground-truth-sources")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_provenance(root: Path, **fields: Any) -> None:
    path = root / "provenance.json"
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    current.update(fields)
    root.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def openrouter_client() -> httpx.AsyncClient:
    load_dotenv()
    base_url = os.environ.get("NEBULA_PREMIUM_BASE_URL", "")
    api_key = os.environ.get("NEBULA_PREMIUM_API_KEY", "")
    if "openrouter.ai" not in base_url:
        raise RuntimeError(f"Premium calls go through OpenRouter only; base URL is {base_url!r}.")
    if not api_key:
        raise RuntimeError("NEBULA_PREMIUM_API_KEY is unset.")
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=httpx.Timeout(180.0, connect=10.0),
    )


def ollama_client() -> httpx.AsyncClient:
    load_dotenv()
    return httpx.AsyncClient(
        base_url=os.environ.get("NEBULA_OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=httpx.Timeout(600.0, connect=5.0),
    )
