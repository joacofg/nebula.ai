# Professor Demo Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A flawless 5–10 minute live demo of Nebula's routing + cost story on the user's laptop, with seeded observability data, a written runbook, and a verified rehearsal.

**Architecture:** No product architecture changes. One new operational script (`scripts/seed_demo_data.py`) drives the real gateway HTTP API to seed governance data and ledger history. One new doc (`docs/demo-runbook.md`). UI fixes limited to defects visible on the Playground and Observability pages.

**Tech Stack:** Python 3.12 + httpx (already a project dep), FastAPI gateway on :8000, Next.js console on :3000, Ollama (llama3.2:3b + nomic-embed-text), Qdrant via docker compose, real premium key already in `.env` (`NEBULA_PREMIUM_PROVIDER=openai_compatible`).

## Global Constraints

- Demo scope only: do NOT touch the 18 failing backend tests, console test/tsc debt, or the structural design backlog (spec: out of scope).
- Auth headers (from `src/nebula/services/auth_service.py:12-14`): chat `X-Nebula-API-Key`, tenant override `X-Nebula-Tenant-ID`, admin `X-Nebula-Admin-Key`.
- Local defaults (`.env` / `.env.example`): admin key `nebula-admin-key`, bootstrap tenant `default` with key `nebula-dev-key`, gateway `http://localhost:8000`, API prefix `/v1`, default model `nebula-auto`.
- Routing levers (`src/nebula/services/router_service.py:62`, `.env.example:27`): prompts containing any of `analyze, reason, contract, debug, architecture, design` (case-insensitive) OR longer than `NEBULA_ROUTER_COMPLEXITY_CHARS=400` chars route premium; short hint-free prompts route local; semantic-cache threshold 0.90.
- Console UI copy is asserted verbatim in vitest — any copy change needs the matching test updated in the same commit.
- Console admin session is memory-only: a full page reload logs out. Tailwind config changes need `rm -rf console/.next` + dev-server restart.
- Seeding sends ~8–10 real premium calls (gpt-4o-mini class via OpenRouter) — cost is cents, but keep `max_tokens` low (60).

---

### Task 1: Environment verification

**Files:** none created/modified — this task proves the stack works and records baseline facts the later tasks rely on.

**Interfaces:**
- Produces: a running stack (gateway :8000, console :3000, Qdrant, Ollama) and confirmation that all three route targets (`local`, `premium`, `cache`) trigger with real providers.

- [ ] **Step 1: Start dependencies and gateway**

```bash
docker compose up -d qdrant
ollama list | grep -E "llama3.2:3b|nomic-embed-text" || make ollama-pull
make migrate
```

Then start the gateway in the background: `make run` (uvicorn on :8000). Wait for `Application startup complete`.

- [ ] **Step 2: Health checks**

Run: `curl -s http://localhost:8000/health/dependencies`
Expected: JSON with every dependency healthy (Qdrant, governance store, Ollama). If Ollama is unreachable, start `ollama serve` first.

- [ ] **Step 3: Prove the local route**

```bash
curl -sD - http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" -H "X-Nebula-API-Key: nebula-dev-key" \
  -d '{"model":"nebula-auto","messages":[{"role":"user","content":"Say hello in five words."}],"max_tokens":30}' \
  -o /dev/null | grep -i x-nebula
```

Expected headers: `X-Nebula-Route-Target: local`, `X-Nebula-Provider: ollama`, `X-Nebula-Cache-Hit: false`.

- [ ] **Step 4: Prove the premium route (real key)**

```bash
curl -sD - http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" -H "X-Nebula-API-Key: nebula-dev-key" \
  -d '{"model":"nebula-auto","messages":[{"role":"user","content":"Analyze the trade-offs between eventual and strong consistency in two sentences."}],"max_tokens":80}' \
  -o /dev/null | grep -i x-nebula
```

Expected: `X-Nebula-Route-Target: premium` (keyword `analyze`). If this returns 4xx/5xx, the premium key/base URL in `.env` is the problem — STOP and surface it to the user before anything else; the demo depends on it.

- [ ] **Step 5: Prove the cache route**

Re-send the Step 3 request twice with a near-identical prompt (`"Say hello in five words please."`). Second expected: `X-Nebula-Route-Target: cache`, `X-Nebula-Cache-Hit: true`. If threshold 0.90 doesn't trigger, send the *identical* prompt and note in the runbook that cache demos use identical repeats.

- [ ] **Step 6: Console boots and logs in**

Run `make console-dev`, open `http://localhost:3000`, sign in with admin key `nebula-admin-key`, confirm the Playground and Observability pages render. (Use the /browse skill headlessly.)

No commit — nothing changed.

---

### Task 2: Demo data seeding script

**Files:**
- Create: `scripts/seed_demo_data.py`

**Interfaces:**
- Consumes: running gateway from Task 1; admin header `X-Nebula-Admin-Key`; `POST /v1/admin/tenants` (`TenantCreateRequest`: id, name, description, metadata, active), `POST /v1/admin/api-keys` (`ApiKeyCreateRequest`: name, tenant_id, key), `GET /v1/admin/usage/ledger`, `POST /v1/chat/completions`.
- Produces: tenant `acme-demo` with deterministic API key `nebula-demo-acme-key`; ≥40 ledger rows spread across local/premium/cache routes. The runbook (Task 4) references this tenant and key verbatim.

- [ ] **Step 1: Write the script**

```python
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
```

- [ ] **Step 2: Run it against the live stack (this is the test)**

Run: `python scripts/seed_demo_data.py`
Expected: tenant + key created; 40 lines of `routed=`; totals showing all three targets present (`local` ≳ 20, `premium` ≳ 8, `cache` ≳ 4 — cache-hit lines may show `cache`); ledger rows ≥ 40; exit 0.

If premium prompts route `local`, the keyword list changed — check `RouterService.COMPLEXITY_HINTS` and adjust prompts. If cache-hit lines never show `cache`, similarity is under threshold — the identical repeat should hit; investigate Qdrant health before changing thresholds.

- [ ] **Step 3: Verify in the console**

Open Observability (`http://localhost:3000` → Observability, tenant Acme Robotics): charts/ledger show the seeded traffic with a visible route mix.

- [ ] **Step 4: Commit**

```bash
git add scripts/seed_demo_data.py
git commit -m "chore(demo): seed script for demo tenant and realistic ledger history"
```

---

### Task 3: Demo-visible polish

**Files:**
- Modify: only files backing the Playground and Observability screens (`console/src/app/(console)/playground/`, `console/src/app/(console)/observability/`, and shared components they render). Nothing else.

**Interfaces:**
- Consumes: seeded data from Task 2 (screens must be judged with realistic data, not empty states).

- [ ] **Step 1: Audit the two screens**

With the stack running and data seeded, use the /browse skill to screenshot the Playground (before and after sending one prompt of each tier) and Observability (default view + tenant-filtered). List every visible defect: clipped text, misaligned metadata, empty-looking panels, confusing labels, broken number formatting.

- [ ] **Step 2: Triage against scope**

Fix ONLY defects visible during the scripted flow. Anything structural (error-banner componentization, tracking tokens, mobile nav — the deferred backlog in TODOS.md) is out of scope even if noticed. If zero defects: skip to Task 4 and note "no visible defects" — do not invent work.

- [ ] **Step 3: Fix, test, commit — one commit per defect**

For each fix: make the minimal change; if UI copy changed, update the vitest assertion in the same commit; run the focused test:

```bash
npm --prefix console run test -- --run src/<path-to-affected>.test.tsx
```

Expected: PASS (pre-existing failures in `ledger-filters.test.tsx` stay untouched). Commit as `style(demo): <defect> on <screen>`.

- [ ] **Step 4: Re-screenshot both screens**

Confirm each fixed defect is gone and nothing regressed.

---

### Task 4: Demo runbook

**Files:**
- Create: `docs/demo-runbook.md`

**Interfaces:**
- Consumes: tenant `acme-demo` / key `nebula-demo-acme-key` from Task 2; verified prompts from Task 1. Prompts below are the defaults — replace any that misbehaved during Task 1/2 with the variant that actually worked.

- [ ] **Step 1: Write the runbook**

```markdown
# Nebula Demo Runbook (professor demo)

## Pre-demo checklist (15 min before)

1. `ollama serve` running — `ollama list` shows `llama3.2:3b`, `nomic-embed-text`.
2. `docker compose up -d qdrant`
3. `make run` — wait for "Application startup complete"; `curl -s localhost:8000/health/dependencies` all healthy.
4. `make console-dev` — open http://localhost:3000, sign in with admin key.
   ⚠️ Session is memory-only: do NOT reload the tab mid-demo (you'd be logged out).
5. Fresh data: `python scripts/seed_demo_data.py` (idempotent; ~2 min).
6. Keep a terminal visible with `curl` ready (recovery + wow moments).

## The story (5–10 min)

**Beat 1 — the problem (30s).** "Teams burn premium-LLM budget on questions a
local model answers fine. Nebula is a self-hosted gateway that routes each
request to the cheapest tier that can handle it — and proves it with metadata."

**Beat 2 — local route (Playground).** Tenant: Acme Robotics. Prompt:
`What does HTTP status 429 mean?`
Point at the response metadata: route target **local**, provider **ollama** —
"this request cost $0."

**Beat 3 — premium escalation.** Prompt:
`Analyze the trade-offs between monolith and microservices for a 5-person startup.`
Route target **premium** — "the router saw a complex, analysis-type request and
escalated to the premium provider. The operator controls those rules."

**Beat 4 — cache hit.** Send:
`Summarize the benefits of semantic caching in one sentence.`
(seeded earlier, so it hits). Route target **cache**, cache hit **true** —
"semantically similar questions get answered from the vector cache: premium
quality at zero marginal cost."

**Beat 5 — receipts (Observability).** Switch to Observability, filter tenant
Acme Robotics: route mix, usage ledger, cost visibility. "Every request lands
in a ledger — this is how an operator sees exactly what routing saved."

**Beat 6 — under the hood (optional, terminal).**
`curl -sD - localhost:8000/v1/chat/completions -H "Content-Type: application/json" -H "X-Nebula-API-Key: nebula-demo-acme-key" -d '{"model":"nebula-auto","messages":[{"role":"user","content":"What is a webhook, briefly?"}],"max_tokens":40}' -o /dev/null | grep -i x-nebula`
"It's OpenAI-compatible — any existing client works unchanged; the routing
story rides in the response headers."

## Recovery moves

| Symptom | Move |
| --- | --- |
| Ollama hangs / slow first token | It cold-loads the model. Pre-warm in the checklist: send one throwaway prompt before the demo. If it hangs live: "the local model is warming up," send the premium-tier prompt first, come back. |
| Premium 401/429 | Say "premium provider is rate-limiting" and continue: local + cache beats still carry the story. Don't debug live. |
| Console logged out (reload) | Sign back in with the admin key — 10 seconds. Narrate: "sessions are deliberately memory-only; operator keys are never persisted client-side." |
| Cache doesn't hit | Re-send the *identical* prompt (similarity 1.0 always hits). |
| Everything on fire | Terminal fallback: the Beat 6 curl works with just the gateway up and demonstrates the full routing story headlessly. |
```

- [ ] **Step 2: Verify every command in the runbook by running it**

Each command must be executed verbatim and succeed before the doc is committed.

- [ ] **Step 3: Commit**

```bash
git add docs/demo-runbook.md
git commit -m "docs(demo): professor demo runbook with scripted beats and recovery moves"
```

---

### Task 5: Full rehearsal

**Files:** none — verification only.

**Interfaces:**
- Consumes: the committed runbook; the running stack.

- [ ] **Step 1: Cold-start rehearsal**

Stop gateway + console, then execute the pre-demo checklist from the runbook top to bottom, exactly as written.

- [ ] **Step 2: Drive every beat headlessly (/browse skill)**

Assert each beat: Beat 2 shows route **local**; Beat 3 shows **premium**; Beat 4 shows **cache** + cache-hit true; Beat 5 Observability shows non-trivial data for Acme Robotics; Beat 6 curl prints the `X-Nebula-*` header block.

- [ ] **Step 3: Fix-or-note loop**

Any beat that fails: fix (within demo scope) or amend the runbook with the working variant, re-run that beat, amend the runbook commit if needed.

- [ ] **Step 4: Report**

Tell the user: rehearsal result per beat, anything amended, and the one-line "start here" instruction for demo day.
