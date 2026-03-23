---
phase: 08-fleet-inventory-and-freshness-visibility
plan: "03"
subsystem: console-ui
tags: [frontend, fleet-inventory, freshness, components, react, vitest]
dependency_graph:
  requires: ["08-01", "08-02"]
  provides: ["fleet-inventory-ui", "freshness-badge", "dependency-health-pills"]
  affects: ["console/src/components/deployments/", "console/src/lib/freshness.ts"]
tech_stack:
  added: []
  patterns:
    - "Badge component pattern matching DeploymentStatusBadge (inline-flex rounded-full border)"
    - "Pill row with colored dot + name for multi-status dependency display"
    - "Row opacity dimming for stale/offline states (opacity-75/opacity-60)"
    - "Section dividers with mt-6 border-t border-border/50 pt-4"
    - "formatRelativeTime using Intl.RelativeTimeFormat for human-readable last-seen"
key_files:
  created:
    - console/src/lib/freshness.ts
    - console/src/components/deployments/freshness-badge.tsx
    - console/src/components/deployments/dependency-health-pills.tsx
    - console/src/components/deployments/freshness-badge.test.tsx
    - console/src/components/deployments/deployment-table.test.tsx
  modified:
    - console/src/components/deployments/deployment-table.tsx
    - console/src/components/deployments/deployment-detail-drawer.tsx
decisions:
  - "[Phase 08]: FreshnessBadge and DeploymentStatusBadge share identical base class for visual consistency"
  - "[Phase 08]: Enrollment state moves from table column to detail drawer identity section per D-11"
  - "[Phase 08]: Row opacity dimming uses opacity-75 for stale and opacity-60 for offline (not hidden)"
metrics:
  duration: "~12 minutes (2 tasks + checkpoint)"
  completed: "2026-03-22"
  tasks_completed: 3
  files_created: 5
  files_modified: 2
requirements-completed:
  - INVT-01
  - INVT-02
  - INVT-04
---

# Phase 8 Plan 3: Frontend Fleet Inventory UI Summary

Frontend fleet inventory UI surfacing heartbeat data: FreshnessBadge with five states, DependencyHealthPills with colored dots, extended fleet table with freshness/version/last-seen columns, and extended detail drawer with freshness section, dependency pills, trust-boundary card, and enrollment state.

## Objective

Build the console UI for fleet inventory visibility: new helper components, extended table columns, and extended detail drawer so operators can assess deployment health at a glance.

## What Was Built

### New Files

**`console/src/lib/freshness.ts`**
- `getFreshnessStyle(status)` maps FreshnessStatus | null to Tailwind className + label
- Color mapping: connected=emerald, degraded=amber, stale=orange, offline=rose, null=amber "Awaiting enrollment"
- `formatRelativeTime(lastSeenAt)` uses Intl.RelativeTimeFormat for minute/hour relative strings; falls back to absolute date for > 24 hours; returns "Never" for null

**`console/src/components/deployments/freshness-badge.tsx`**
- `FreshnessBadge({ status: FreshnessStatus | null })` — pill badge matching DeploymentStatusBadge base class exactly
- Five display states: Connected, Degraded, Stale, Offline, Awaiting enrollment
- No icons used (text carries the meaning per accessibility contract)

**`console/src/components/deployments/dependency-health-pills.tsx`**
- `DependencyHealthPills({ summary: DependencySummary | null })` — compact colored pill row
- Dot colors: healthy=bg-emerald-500, degraded=bg-amber-500, unavailable=bg-rose-500
- Renders "No data reported" in slate-400 when summary is null or empty

**`console/src/components/deployments/freshness-badge.test.tsx`**
- 7 tests covering all 4 status values, null state ("Awaiting enrollment"), and color class assertions

**`console/src/components/deployments/deployment-table.test.tsx`**
- 7 tests covering column headers (Freshness, Version, Last Seen), absence of old headers (Status, Enrolled), freshness badge content, version string, and empty state

### Modified Files

**`console/src/components/deployments/deployment-table.tsx`**
- Replaced columns: Name, Environment, Status, Enrolled → Name, Environment, Freshness, Version, Last Seen
- Added row opacity dimming: stale=opacity-75, offline=opacity-60
- Row hover: transition-colors duration-150 per UI-SPEC Interaction States
- Version column: monospace font-fira-code, em dash for null
- Last Seen column: formatRelativeTime output

**`console/src/components/deployments/deployment-detail-drawer.tsx`**
- Added Freshness section (after header): FreshnessBadge + freshness_reason + absolute timestamp
- Enrollment state moved from header badge to Identity section (per D-11)
- Added Dependencies section: DependencyHealthPills
- Added Trust Boundary section: TrustBoundaryCard
- Section dividers: mt-6 border-t border-border/50 pt-4 throughout
- Drawer layout order: Freshness → Identity (with enrollment state) → Dependencies → Trust Boundary → Lifecycle Actions

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | New components and helpers -- FreshnessBadge, DependencyHealthPills, freshness.ts | 004b9d4 | freshness-badge.tsx, dependency-health-pills.tsx, freshness.ts |
| 2 | Extend fleet table and detail drawer with freshness, dependencies, and trust-boundary | 6c11592 | deployment-table.tsx, deployment-detail-drawer.tsx, freshness-badge.test.tsx, deployment-table.test.tsx |
| 3 | Visual verification of fleet inventory UI | checkpoint | Approved by operator |

## Verification Results

- All freshness-badge.test.tsx tests pass (7/7)
- All deployment-table.test.tsx tests pass (7/7)
- Full console test suite green (`make console-test`)
- Visual verification approved: fleet table shows 5 columns, "Awaiting enrollment" badges shown in amber for pending deployments, detail drawer layout confirmed, "No data reported" shown for null dependency summary

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All freshness data flows from real DeploymentRecord fields (freshness_status, freshness_reason, last_seen_at, dependency_summary) populated by the heartbeat ingest service from Plan 08-01.

## Success Criteria Verification

1. Fleet table displays Name, Environment, Freshness badge, Version, Last Seen columns (INVT-01). **DONE.**
2. FreshnessBadge shows correct color per status: emerald/amber/orange/rose + "Awaiting enrollment" for null (INVT-02). **DONE.**
3. Stale and offline rows are visually dimmed but never hidden (D-10). **DONE** — opacity-75 for stale, opacity-60 for offline.
4. Detail drawer layout matches D-12: freshness then identity with enrollment state then dependencies then trust-boundary then lifecycle actions. **DONE.**
5. DependencyHealthPills render colored dots per status (INVT-01). **DONE.**
6. Capability flags shown as chips in drawer (INVT-04). **DONE** — existing chip rendering preserved in identity section.
7. Trust-boundary card imported from Phase 6 without modification. **DONE.**
8. Frontend and backend test suites green. **DONE.**

## Self-Check: PASSED
