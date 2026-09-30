"""Put the demo tenant in the state the defense demo expects.

Usage: python -m scripts.demo_prepare  (gateway must be running on :8000; `make demo` runs it)
Idempotent: creates acme-demo and its key if missing, sets the policy the three Playground
examples are tuned for (local / economy / frontier at objective 0.90), and warms Ollama so the
first local answer does not pay the model's cold load.
"""
from __future__ import annotations

import os
import sys
from typing import Any

import httpx

from scripts.seed_demo_data import ADMIN_HEADERS, BASE, DEMO_TENANT_ID, ensure_governance

DEMO_QUALITY_TARGET = 0.90
PREMIUM_MODELS = ("openai/gpt-4.1", "anthropic/claude-haiku-4.5")
OLLAMA = os.environ.get("NEBULA_OLLAMA_BASE_URL", "http://localhost:11434")
LOCAL_MODEL = os.environ.get("NEBULA_LOCAL_MODEL", "qwen2.5:7b")
EMBEDDING_MODEL = os.environ.get("NEBULA_EMBEDDING_MODEL", "nomic-embed-text")


def demo_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """The tenant policy with only what the demo depends on changed."""
    updated = dict(policy)
    updated["routing_quality_target"] = DEMO_QUALITY_TARGET
    allowed = list(updated.get("allowed_premium_models") or [])
    # An empty allowlist allows every model; a non-empty one must name both premium tiers.
    if allowed:
        allowed += [model for model in PREMIUM_MODELS if model not in allowed]
    updated["allowed_premium_models"] = allowed
    updated["hard_budget_limit_usd"] = None
    updated["hard_budget_enforcement"] = None
    updated["semantic_cache_enabled"] = True
    return updated


def apply_policy(client: httpx.Client) -> None:
    url = f"{BASE}/v1/admin/tenants/{DEMO_TENANT_ID}/policy"
    current = client.get(url, headers=ADMIN_HEADERS)
    current.raise_for_status()
    client.put(url, headers=ADMIN_HEADERS, json=demo_policy(current.json())).raise_for_status()
    print(f"política de {DEMO_TENANT_ID}: objetivo {DEMO_QUALITY_TARGET:.2f}, caché activa")


def warm_ollama(client: httpx.Client) -> None:
    client.post(
        f"{OLLAMA}/api/generate",
        json={"model": LOCAL_MODEL, "prompt": "hola", "stream": False, "keep_alive": "2h", "options": {"num_predict": 1}},
        timeout=180,
    ).raise_for_status()
    client.post(
        f"{OLLAMA}/api/embed", json={"model": EMBEDDING_MODEL, "input": "hola", "keep_alive": "2h"}, timeout=120
    ).raise_for_status()
    print(f"ollama: {LOCAL_MODEL} y {EMBEDDING_MODEL} cargados")


def main() -> int:
    with httpx.Client(timeout=30) as client:
        ensure_governance(client)
        apply_policy(client)
        warm_ollama(client)
    return 0


if __name__ == "__main__":
    sys.exit(main())
