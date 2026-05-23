# M003: M003: Broader Adoption Surface

**Vision:** Extend Nebula beyond the initial chat-completions adoption path with one narrowly scoped, high-demand public surface — embeddings — using a tight compatibility boundary, canonical docs, realistic migration proof, and only minimal optional helper ergonomics, while preserving v3 guardrails against broad parity push, SDK sprawl, hosted-plane expansion, and unrelated infrastructure work.

## Success Criteria

- A team can point a common OpenAI-style embeddings caller at Nebula through `POST /v1/embeddings` with minimal changes and receive a usable embeddings response within the documented narrow contract.
- Nebula documents the embeddings adoption boundary canonically, including explicit unsupported or deferred edges, and the migration proof matches runtime truth.
- An embeddings adoption request can be tied to durable backend/operator evidence so teams can explain what happened during evaluation without new helper layers.
- The assembled milestone widens the adoption story without adding broad parity work, SDK sprawl, hosted-plane expansion, or unrelated infrastructure.

## Slices

- [x] **S01: Public embeddings endpoint** `risk:high` `depends:[]`
  > After this: A client can send a strict happy-path authenticated `POST /v1/embeddings` request to Nebula and receive a usable embeddings response within the intended narrow contract.

- [x] **S02: Canonical embeddings contract docs** `risk:medium` `depends:[S01]`
  > After this: One canonical doc defines the public embeddings boundary, supported behavior, and explicit exclusions, grounded in the real S01 runtime path.

- [x] **S03: Realistic migration proof** `risk:medium` `depends:[S01,S02]`
  > After this: A believable OpenAI-style embeddings caller migration proves Nebula can replace a direct provider path with minimal caller changes.

- [x] **S04: Durable evidence correlation** `risk:medium` `depends:[S01,S03]`
  > After this: The same embeddings request can be tied to durable backend/operator evidence so teams can explain and validate the migration proof.

- [x] **S05: Final adoption assembly** `risk:low` `depends:[S02,S03,S04]`
  > After this: The full embeddings adoption story is assembled end-to-end — contract, migration path, and proof surfaces agree without widening scope.

## Boundary Map

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
