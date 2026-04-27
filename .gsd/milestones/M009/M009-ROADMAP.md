# M009: Outcome-Grounded Routing Quality

**Vision:** Improve Nebula’s routing decisions using bounded recent tenant-scoped outcome evidence so the gateway can make measurably better local-vs-premium choices while remaining explainable, simulation-verifiable, and operator-controlled.

## Success Criteria

- Live routing uses bounded recent tenant-scoped outcome evidence to improve local-vs-premium choices rather than prompt heuristics alone.
- Policy simulation replay uses the same outcome-grounded routing semantics as live runtime and degrades honestly when evidence is incomplete.
- Persisted request evidence records the actual outcome-grounded route factors that influenced the decision.
- Existing request-first operator surfaces explain grounded vs thin/stale/degraded routing without widening into a dashboard-heavy analytics product.
- The final integrated proof covers both a happy-path request and a degraded-path request while preserving local authority and the metadata-only hosted boundary.

## Slices

- [x] **S01: S01** `risk:high` `depends:[]`
  > After this: After this: one tenant’s recent ledger-backed outcome evidence can be derived deterministically with explicit sufficient/thin/stale/degraded states and proved through backend tests and typed artifacts.

- [x] **S02: S02** `risk:high` `depends:[]`
  > After this: After this: a real `POST /v1/chat/completions` request can route differently because of recent tenant-scoped outcome evidence, and the correlated persisted ledger row records the actual route factors used.

- [x] **S03: S03** `risk:medium` `depends:[]`
  > After this: After this: `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replays the same outcome-grounded semantics as runtime, including honest degraded behavior when evidence is incomplete.

- [x] **S04: S04** `risk:medium` `depends:[]`
  > After this: After this: the selected request in Observability and request detail explains whether routing was grounded, thin, stale, or degraded using the existing request-first evidence surfaces.

- [x] **S05: S05** `risk:low` `depends:[]`
  > After this: After this: one review path proves public request → persisted request evidence → replay parity → request-first operator inspection for both a happy path and a degraded path, with anti-drift boundaries locked in docs and tests.

## Boundary Map

## Boundary Map

### S01 → S02
Produces:
- tenant-scoped outcome evidence summary contract with deterministic windowing and explicit sufficient/thin/stale/degraded state
- typed backend factor vocabulary for outcome-grounded additive scoring
- tests that prove evidence-state transitions are stable and replayable

Consumes:
- existing usage-ledger rows and calibration-era routing evidence from prior milestones

### S02 → S03
Produces:
- live outcome-grounded route-score factors persisted on the selected request row
- runtime route decisions that can differ because of bounded recent tenant-scoped outcome evidence
- public-request-to-ledger correlation story extended with richer request-level route factors

Consumes from S01:
- outcome evidence summary contract and evidence-state vocabulary

### S02 → S04
Produces:
- persisted request-level route factors and grounded/thin/stale/degraded routing state for the selected request

Consumes from S01:
- outcome evidence summary contract and evidence-state vocabulary

### S03 → S04
Produces:
- replay parity semantics for outcome-grounded routing
- degraded replay semantics and approximation notes tied to the same evidence-state vocabulary

Consumes from S01:
- outcome evidence summary contract and evidence-state vocabulary
Consumes from S02:
- persisted live route factors and runtime scoring semantics

### S02 → S05
Produces:
- real live request path using outcome-grounded routing
- persisted ledger evidence for the same request

Consumes from S01:
- outcome evidence summary contract

### S03 → S05
Produces:
- replay parity path for the same tenant traffic class
- honest degraded replay proof path

Consumes from S01:
- outcome evidence summary contract
Consumes from S02:
- runtime route-factor persistence and scoring semantics

### S04 → S05
Produces:
- request-first operator inspection path for grounded/thin/stale/degraded route evidence

Consumes from S02:
- persisted request-level route factors
Consumes from S03:
- replay parity and degraded-state explanation vocabulary
