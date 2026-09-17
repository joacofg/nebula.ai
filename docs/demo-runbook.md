# Nebula Demo Runbook (professor demo)

## Pre-demo checklist (15 min before)

1. `ollama serve` running — `ollama list` shows `llama3.2:3b`, `nomic-embed-text`.
2. `docker compose up -d qdrant`
3. **Reset the semantic cache** (gateway must NOT be running yet):
   `curl -s -X DELETE http://localhost:6333/collections/nebula-semantic-cache`
   Why: the gateway recreates the collection automatically at startup if it's
   missing, and semantic cache persists in Qdrant across restarts. Resetting
   it here guarantees the demo starts from a known cache state — only the
   prompts the seed script sends will be cached — so Beats 2–3 route fresh
   (local / premium) instead of accidentally cache-hitting, and Beat 4
   reliably cache-hits. A 404 response here just means the cache was already empty — that's fine.
4. `make run` (in its own terminal) — wait for "Application startup complete"; `curl -s localhost:8000/health/dependencies` all healthy.
5. `make console-dev` (in its own terminal) — open http://localhost:3000, sign in with admin key.
   ⚠️ Session is memory-only: do NOT reload the tab mid-demo (you'd be logged out).
6. Fresh data: `python scripts/seed_demo_data.py` (idempotent; ~2 min).
7. Keep a terminal visible with `curl` ready (recovery + wow moments).

## The story (5–10 min)

**Beat 1 — the problem (30s).** "Teams burn premium-LLM budget on questions a
local model answers fine. Nebula is a self-hosted gateway that routes each
request to the cheapest tier that can handle it — and proves it with metadata."

**Beat 2 — local route (Playground).** Tenant: Acme Robotics. Prompt:
`What year did the first web browser appear?`
Point at the response metadata: route target **local**, provider **ollama** —
"this request cost $0."

**Beat 3 — premium escalation.** Prompt:
`Analyze whether a university lab should buy GPUs or rent cloud compute.`
Route target **premium**, provider **openai-compatible** — "the router saw a complex, analysis-type request and
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
Note: this prompt is one of the seeded ones, so `x-nebula-route-target` will
read **cache**, not local — that's expected and fine. The point of this beat
isn't which tier it hits; it's the `X-Nebula-*` header block itself: "It's
OpenAI-compatible — any existing client works unchanged; the routing story
rides in the response headers."

## Recovery moves

| Symptom | Move |
| --- | --- |
| Ollama hangs / slow first token | It cold-loads the model. The seed script in checklist step 6 pre-warms it; if you skipped seeding, send one throwaway prompt now. If it hangs live: "the local model is warming up," send the premium-tier prompt first, come back. |
| Premium 401/429 | Say "premium provider is rate-limiting" and continue: local + cache beats still carry the story. Don't debug live. |
| Console logged out (reload) | Sign back in with the admin key — 10 seconds. Narrate: "sessions are deliberately memory-only; operator keys are never persisted client-side." |
| Cache doesn't hit | Re-send the *identical* prompt (similarity 1.0 always hits). |
| Beat 2/3 unexpectedly routes cache | You skipped the cache-reset step; any prompt sent before the demo is cached. Use a fresh variation of the prompt (different topic, keep/omit the hint keyword accordingly). |
| Everything on fire | Terminal fallback: the Beat 6 curl works with just the gateway up and demonstrates the full routing story headlessly. |
| Gateway fails at startup with "Can't locate revision identified by ..." | The local database predates the September 2026 migration collapse. Delete `.nebula/nebula.db`, run `make migrate`, then re-run `scripts/seed_demo_data.py`. |
