---
status: partial
phase: 07-deployment-enrollment-and-identity
source: [07-VERIFICATION.md]
started: 2026-03-21T23:30:00Z
updated: 2026-03-21T23:30:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Empty state at /deployments
expected: Shows "No deployments linked" heading with "Create deployment slot" CTA button
result: [pending]

### 2. Token reveal dialog on deployment creation
expected: EnrollmentTokenRevealDialog opens showing nbet_ token in dark code slab, NEBULA_ENROLLMENT_TOKEN env var instruction, disclosure warning, functional Copy button
result: [pending]

### 3. Pending badge in table
expected: Amber "Pending enrollment" badge, correct display name
result: [pending]

### 4. Detail drawer on row click
expected: Split-panel layout, UUID in Fira Code, status badge, created date, trust boundary reminder
result: [pending]

### 5. Active state actions (revoke/unlink buttons)
expected: Sky-blue Active badge, Unlink/Revoke buttons, RevokeConfirmationDialog with pink-700 confirm
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
