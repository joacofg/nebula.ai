# Professor Demo Polish — Design

**Date:** 2026-07-16
**Status:** Approved (approach 1: demo-path hardening, no Railway deploy)

## Context

Nebula.ai will be demoed live to a professor within a day. The user drives the
demo from their own laptop. The story: the Playground routing narrative
(local → cache → premium escalation, with `X-Nebula-*` metadata) plus
Observability & cost visibility. Providers: real local Ollama + a real
premium OpenAI-compatible API key.

Out of scope (explicitly deferred, invisible in a live demo):

- The 18 pre-existing backend test failures and console test/tsc debt (TODOS.md).
- The structural design backlog from the 2026-07-13 design review.
- Railway (or any cloud) deployment — the core story is the *local* model
  tier, which cannot run on Railway; a premium-only cloud demo is a weaker
  story with overnight deploy risk. The laptop with a rehearsed runbook is
  more reliable and reinforces the "self-hosted" pitch.

## Goal

A flawless 5–10 minute live demo of Nebula's routing + cost story, with a
written runbook and a verified rehearsal.

## Work items (in order)

### 1. Environment verification

Boot the full local stack (gateway on :8000, console on :3000, Qdrant,
PostgreSQL, Ollama) and confirm end-to-end:

- Ollama model responds through the gateway (`"local"` route).
- Premium key responds through the gateway (`"premium"` route).
- Semantic cache returns a `"cache"` route on a repeated/similar prompt.
- Console logs in and both demo pages render.

### 2. Demo data seeding

A repeatable script at `scripts/seed_demo_data.py` that:

- Creates a demo tenant + API key with a sensible policy.
- Generates ~30–50 varied completions across routing tiers so the usage
  ledger and observability charts have realistic shape — an empty dashboard
  is the top demo killer.

### 3. Demo-visible polish

Fix only defects visible on the Playground and Observability screens during
the scripted flow (the console is already at design grade B). Anything not
on-screen during the demo is out of scope.

### 4. Demo runbook

`docs/demo-runbook.md` containing:

- Pre-demo checklist (services to start, order, health checks).
- The scripted narrative beat by beat.
- Exact prompts that reliably trigger each routing tier (local, cache,
  premium), verified during rehearsal.
- Recovery moves: what to do if Ollama hangs, premium rate-limits, or the
  console session drops (console session is memory-only — a full page reload
  logs out; keep the tab alive).

### 5. Full rehearsal

Drive the entire runbook headlessly (browse skill) against the running
stack and confirm every beat lands: each routing tier triggers as scripted,
headers/metadata display, observability shows the seeded + live data.

## Success criteria

- Every step of the runbook executes without error on the user's machine.
- All three routing tiers demonstrably trigger with the scripted prompts.
- Observability page shows non-trivial usage/cost data.
- No visible UI defects on the two demo screens during the flow.
