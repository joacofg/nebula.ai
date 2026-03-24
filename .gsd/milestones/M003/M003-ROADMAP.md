# M003: Broader Adoption Surface

**Vision:** Extend Nebula beyond the initial chat-completions adoption path with one narrowly scoped, high-demand public surface — embeddings — using a tight compatibility boundary, canonical docs, realistic migration proof, and only minimal optional helper ergonomics, while preserving v3 guardrails against broad parity push, SDK sprawl, hosted-plane expansion, and unrelated infrastructure work.

## Success Criteria

- A team can point a common OpenAI-style embeddings caller at Nebula through `POST /v1/embeddings` with minimal changes and receive a usable embeddings response within the documented narrow contract.
- Nebula documents the embeddings adoption boundary canonically, including explicit unsupported or deferred edges, and the migration proof matches runtime truth.
- An embeddings adoption request can be tied to durable backend/operator evidence so teams can explain what happened during evaluation without new helper layers.
- The assembled milestone widens the adoption story without adding broad parity work, SDK sprawl, hosted-plane expansion, or unrelated infrastructure.

## Key Risks / Unknowns

- Public embeddings compatibility may expose more contract surface than the existing internal service can safely support — that would turn a narrow adoption milestone into a parity commitment.
- Durable evidence for embeddings requests may not be sufficient in current backend/operator surfaces — if proof needs more than existing leverage, scope could drift.
- Migration examples may become toy demos or Nebula-specific workflows instead of believable minimal-change caller swaps — that would weaken the adoption proof.

## Proof Strategy

- Public embeddings compatibility risk → retire in S01 by proving a real authenticated `POST /v1/embeddings` happy path works through Nebula with a narrow, test-backed request/response contract.
- Contract-sprawl risk → retire in S02 by proving the canonical docs define supported behavior and explicit exclusions in one place and align to tests/runtime behavior.
- Migration-credibility risk → retire in S03 by proving a common OpenAI-style embeddings caller can move to Nebula with minimal caller changes and realistic evidence.
- Evidence-gap risk → retire in S04 by proving the same embeddings request can be correlated to durable backend/operator evidence without requiring a new helper stack.

## Verification Classes

- Contract verification: pytest coverage for the public embeddings path, artifact checks for canonical docs and migration proof files, and source checks for boundary wiring.
- Integration verification: real authenticated `POST /v1/embeddings` requests flowing through the gateway into the existing embeddings capability and into durable backend/operator evidence.
- Operational verification: none beyond the existing gateway lifecycle; no new deployment or supervision layer should be required.
- UAT / human verification: confirm the migration guide and canonical docs read as credible, narrow, and non-ambiguous to a human evaluator.

## Milestone Definition of Done

This milestone is complete only when all are true:

- All slices deliver a real public embeddings adoption path, not just internal capability exposure.
- The public endpoint, canonical docs, migration proof, and durable evidence surfaces are actually wired together.
- The real `/v1/embeddings` entrypoint exists and is exercised through authenticated requests.
- The success criteria are re-checked against live behavior and assembled artifacts, not just planning intent.
- Final integrated acceptance passes without introducing broad parity, SDK sprawl, hosted-plane expansion, or unrelated infrastructure work.

## Requirement Coverage

- Covers: R020, R021, R022, R023, R024
- Partially covers: none
- Leaves for later: R025, R026, R027
- Orphan risks: none

## Slices

- [ ] **S01: Public embeddings endpoint** `risk:high` `depends:[]`
  > After this: A client can send a strict happy-path authenticated `POST /v1/embeddings` request to Nebula and receive a usable embeddings response within the intended narrow contract.

- [ ] **S02: Canonical embeddings contract docs** `risk:medium` `depends:[S01]`
  > After this: One canonical doc defines the public embeddings boundary, supported behavior, and explicit exclusions, grounded in the real S01 runtime path.

- [ ] **S03: Realistic migration proof** `risk:medium` `depends:[S01,S02]`
  > After this: A believable OpenAI-style embeddings caller migration proves Nebula can replace a direct provider path with minimal caller changes.

- [ ] **S04: Durable evidence correlation** `risk:medium` `depends:[S01,S03]`
  > After this: The same embeddings request can be tied to durable backend/operator evidence so teams can explain and validate the migration proof.

- [ ] **S05: Final adoption assembly** `risk:low` `depends:[S02,S03,S04]`
  > After this: The full embeddings adoption story is assembled end-to-end — contract, migration path, and proof surfaces agree without widening scope.

## Boundary Map

### S01 → S02

Produces:
- `POST /v1/embeddings` authenticated public route
- request schema invariant for strict happy-path embeddings input
- response schema matching the documented standard float embeddings shape
- wiring from the public route into the existing embeddings capability

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- stable minimal-change public embeddings path that a realistic caller can target
- authentication and tenant-handling behavior aligned with the existing public adoption contract
- test-backed request/response examples for the supported path

Consumes:
- nothing (first slice)

### S01 → S04

Produces:
- request identity and runtime outcome surfaces available for embeddings requests
- durable record shape or correlation path sufficient to connect a public embeddings request to backend/operator evidence

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- canonical embeddings contract doc naming supported behavior and exclusions
- agreed migration vocabulary for what counts as minimal caller change

Consumes from S01:
- public embeddings endpoint and stable happy-path contract

### S03 → S04

Produces:
- realistic embeddings migration proof artifact
- concrete request examples and expected evidence to correlate downstream

Consumes from S01:
- public embeddings endpoint and response behavior

Consumes from S02:
- canonical contract boundary and exclusions

### S02/S03/S04 → S05

Produces:
- assembled milestone proof package tying contract, migration, and durable evidence into one adoption story

Consumes from S02:
- canonical embeddings contract docs

Consumes from S03:
- realistic migration proof

Consumes from S04:
- durable evidence correlation path
