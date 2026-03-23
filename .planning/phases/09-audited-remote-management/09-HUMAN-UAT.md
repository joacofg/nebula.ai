---
status: passed
phase: 09-audited-remote-management
source: [09-VERIFICATION.md]
started: 2026-03-23T19:00:19Z
updated: 2026-03-23T19:01:57Z
---

## Current Test

[complete — all tests passed]

## Tests

### 1. Hosted drawer queue flow in a running console
expected: Active deployment detail drawer shows the rotate action, requires a note, confirms intent, queues one action, and shows the new history row
result: passed
evidence: Playwright session against `http://127.0.0.1:3000/deployments` showed the active deployment drawer, accepted the confirmation dialog, and rendered the queued history row with note `Milestone closeout live rotation smoke test.`

### 2. End-to-end hosted-to-gateway credential rotation against a live linked deployment
expected: Hosted plane queues one rotation, gateway polls outbound, applies only the hosted-link credential change, old credential is replaced, and the new credential is accepted on subsequent polls
result: passed
evidence: Hosted API recorded action `89c0d98d-18d1-4d0c-ae76-ba80bcc9f7dd` as `applied` at `2026-03-23T19:01:57.498005Z`; hosted and gateway SQLite stores both ended with credential prefix `nbdc_5MLEug2`

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
