# M010: Production Resilience and Failure Proof

**Vision:** Prove Nebula remains trustworthy under dependency outages, degraded infrastructure, and recovery scenarios by making failure behavior, operator-visible truth, and recovery verification explicit on existing runtime and operator surfaces.

## Success Criteria

- Nebula serves, degrades, or fails safely under the most important dependency outage classes with truthful runtime behavior.
- Operators can identify failed dependency, degraded mode, and recovery status using existing health/admin/observability surfaces.
- At least one documented recovery path is verified end to end and confirms restored healthy behavior plus trustworthy post-recovery evidence.
- The milestone proves production resilience without widening into a separate incident-management dashboard, chaos platform, or hosted-authoritative control plane.

## Slices

- [x] **S01: S01** `risk:high` `depends:[]`
  > After this: After this: Nebula has a stable typed resilience contract proving how serving-critical, serving-optional, and metadata-only dependency failures degrade, fail closed, and recover at the runtime truth layer.

- [x] **S02: S02** `risk:high` `depends:[]`
  > After this: After this: at least one serving-critical outage and one serving-optional outage are exercised end to end, proving truthful request behavior, safe degraded or fail-closed behavior, and correct runtime/admin evidence.

- [x] **S03: S03** `risk:medium` `depends:[]`
  > After this: After this: operators can use existing health/admin/request-detail/Observability surfaces to identify the failed dependency, understand the current degraded mode, and see recovery status without a new dashboard.

- [x] **S04: S04** `risk:medium` `depends:[]`
  > After this: After this: a documented recovery path for the highest-value outage classes is verified end to end, including restored healthy behavior and trustworthy post-recovery evidence.

- [x] **S05: S05** `risk:low` `depends:[]`
  > After this: After this: one integrated proof shows outage trigger, degraded runtime truth, operator inspection, and successful recovery confirmation in a pointer-first review path with anti-sprawl boundaries locked.

- [x] **S06: S06** `risk:low` `depends:[]`
  > After this: After this: M010 explicitly proves premium-provider and hosted-metadata outage behavior on existing runtime truth surfaces, closing the remaining R087 validation gap without adding new product surface area.

## Boundary Map

### S01 → S02
Produces:
- typed dependency-state vocabulary covering serving-critical, serving-optional, and metadata-only failures
- stable degraded/fail-closed invariants for request handling, health truth, and recovery-state transitions
- focused backend tests that lock the resilience contract

Consumes:
- nothing (first slice)

### S01 → S03
Produces:
- dependency-state and degraded-mode vocabulary reusable by health/admin/request-detail/Observability surfaces
- stable operator-facing truth model for current failure and recovery status

Consumes:
- nothing (first slice)

### S02 → S03
Produces:
- real outage-path runtime and admin evidence from serving-critical and serving-optional dependency failures
- request/evidence examples proving what operators must be able to inspect

Consumes from S01:
- dependency-state contract and degraded-mode invariants

### S02 → S04
Produces:
- verified outage and post-recovery runtime behavior for the highest-value dependency classes
- truthful failure-state transitions that recovery proof must restore or supersede

Consumes from S01:
- dependency-state contract and degraded-mode invariants

### S03 → S04
Produces:
- operator-visible failure/recovery truth on existing surfaces
- bounded UI/admin wording and evidence hierarchy for resilience inspection

Consumes from S01:
- dependency-state vocabulary
Consumes from S02:
- real outage-path evidence and degraded runtime behavior

### S02 → S05
Produces:
- end-to-end outage trigger and runtime truth for at least one serving-critical and one serving-optional dependency class

Consumes from S01:
- dependency-state contract

### S03 → S05
Produces:
- operator inspection path for degraded and recovered states using existing surfaces

Consumes from S01:
- operator-visible resilience vocabulary
Consumes from S02:
- real outage-path evidence

### S04 → S05
Produces:
- verified recovery path and post-recovery evidence-integrity proof

Consumes from S02:
- degraded runtime truth and outage behavior
Consumes from S03:
- operator-visible failure/recovery surfaces
