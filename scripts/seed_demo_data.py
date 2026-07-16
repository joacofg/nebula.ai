"""Seed realistic demo data through the live gateway.

Usage: python scripts/seed_demo_data.py  (gateway must be running on :8000)
Re-runnable: tenant/key creation tolerates 'already exists'; completions append.
"""
from __future__ import annotations

import os
import sys

import httpx

BASE = os.environ.get("NEBULA_BASE_URL", "http://localhost:8000")
ADMIN_KEY = os.environ.get("NEBULA_ADMIN_API_KEY", "nebula-admin-key")
DEMO_TENANT_ID = "acme-demo"
DEMO_API_KEY = "nebula-demo-acme-key"

ADMIN_HEADERS = {"X-Nebula-Admin-Key": ADMIN_KEY}

# Short, hint-free -> local route. Varied so the ledger looks organic.
LOCAL_PROMPTS = [
    "Summarize what a reverse proxy does in one sentence.",
    "Give me three names for a coffee shop loyalty app.",
    "What does HTTP status 429 mean?",
    "Write a friendly one-line out-of-office message.",
    "What is the capital of Australia?",
    "Explain what a vector embedding is in one sentence.",
    "Suggest a commit message for fixing a typo in the README.",
    "What port does PostgreSQL use by default?",
    "Give me a two-line haiku about servers.",
    "What does the acronym SLA stand for?",
    "Name three common HTTP methods.",
    "What is a webhook, briefly?",
    "One-sentence definition of rate limiting.",
    "What language is FastAPI written in?",
    "Give a short tagline for a robotics startup.",
    "What does CRUD stand for?",
    "Briefly, what is a Docker container?",
    "What time zone is UTC-3?",
    "Suggest a name for an internal cost dashboard.",
    "What is JSON short for?",
]

# Contains router COMPLEXITY_HINTS (analyze/reason/debug/architecture/design/contract) -> premium.
PREMIUM_PROMPTS = [
    "Analyze the trade-offs between monolith and microservices for a 5-person startup.",
    "Debug this reasoning: if all caches are fast and Redis is a cache, is Redis always fast?",
    "Design a rollback strategy for a schema migration gone wrong, in three steps.",
    "Analyze whether semantic caching can cut LLM spend for a support chatbot.",
    "Explain the architecture of a typical API gateway in four sentences.",
    "Reason step by step: why might p99 latency rise while p50 stays flat?",
    "Draft one contract clause covering API uptime guarantees.",
    "Analyze the cost difference between local and hosted LLM inference.",
]

# Sent twice each -> second send lands as a cache hit.
CACHE_PROMPTS = [
    "Summarize the benefits of semantic caching in one sentence.",
    "What are the main features of an AI gateway?",
    "Explain token-based pricing for LLM APIs in one sentence.",
    "How does request routing reduce cloud costs, briefly?",
    "What metadata should an LLM gateway attach to responses?",
    "Give one reason to self-host an AI gateway.",
]


def ensure_governance(client: httpx.Client) -> None:
    r = client.post(
        f"{BASE}/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json={
            "id": DEMO_TENANT_ID,
            "name": "Acme Robotics",
            "description": "Customer-support AI workloads (demo tenant)",
            "metadata": {"plan": "growth", "region": "us-east"},
            "active": True,
        },
    )
    if r.status_code not in (201, 409):
        r.raise_for_status()
    print(f"tenant {DEMO_TENANT_ID}: {'created' if r.status_code == 201 else 'exists'}")

    r = client.post(
        f"{BASE}/v1/admin/api-keys",
        headers=ADMIN_HEADERS,
        json={"name": "acme-demo-key", "tenant_id": DEMO_TENANT_ID, "key": DEMO_API_KEY},
    )
    if r.status_code not in (201, 409):
        r.raise_for_status()
    print(f"api key acme-demo-key: {'created' if r.status_code == 201 else 'exists'}")


def send(client: httpx.Client, prompt: str) -> str:
    r = client.post(
        f"{BASE}/v1/chat/completions",
        headers={"X-Nebula-API-Key": DEMO_API_KEY},
        json={
            "model": "nebula-auto",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 60,
        },
    )
    if r.status_code != 200:
        return f"error:{r.status_code}"
    return r.headers.get("X-Nebula-Route-Target", "?")


def main() -> int:
    counts: dict[str, int] = {}
    with httpx.Client(timeout=120) as client:
        ensure_governance(client)
        plan = (
            [(p, "local") for p in LOCAL_PROMPTS]
            + [(p, "premium") for p in PREMIUM_PROMPTS]
            + [(p, "cache-prime") for p in CACHE_PROMPTS]
            + [(p, "cache-hit") for p in CACHE_PROMPTS]
        )
        for i, (prompt, intent) in enumerate(plan, 1):
            target = send(client, prompt)
            counts[target] = counts.get(target, 0) + 1
            print(f"[{i:02d}/{len(plan)}] intent={intent:<11} routed={target}")

        ledger = client.get(
            f"{BASE}/v1/admin/usage/ledger",
            headers=ADMIN_HEADERS,
            params={"tenant_id": DEMO_TENANT_ID},
        )
        ledger.raise_for_status()
        rows = len(ledger.json())

    print(f"\nroute totals: {counts}")
    print(f"ledger rows for {DEMO_TENANT_ID}: {rows}")
    if counts.get("error:401", 0) or rows == 0:
        print("SEEDING FAILED — check gateway logs", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
