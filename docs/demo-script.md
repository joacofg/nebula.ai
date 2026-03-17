# Nebula Demo Script

This script is the recommended Phase 5 live walkthrough. It is benchmark-led, but grounded in the operator product instead of slides or a demo-only surface.

## Goal

Make one clear claim:

Nebula reduces estimated premium spend on repeatable traffic patterns without hiding routing decisions, fallback behavior, or degraded optional dependencies from the operator.

## Demo setup

1. Start the supported stack.

   ```bash
   docker compose -f docker-compose.selfhosted.yml up -d
   ```

2. Open the operator console.

   ```bash
   open http://localhost:3000
   ```

3. Confirm the gateway is up.

   ```bash
   curl http://localhost:8000/health
   ```

## Walkthrough

### 1. Establish the operator surface

Start in the console and explain that Nebula is operated through:

- Playground for live request inspection
- Observability for recorded usage and dependency health
- tenant and policy screens for governance control

Keep this short. The demo is not a full product tour.

### 2. Run the benchmark-led proof

In the repo, run:

```bash
make benchmark-demo
```

Open the newest `artifacts/benchmarks/<timestamp>/report.md` and focus on:

- the key takeaways
- route and cost highlights
- the fallback resilience group

State the concrete savings claim from the artifact before moving on.

### 3. Show one live Playground request

Move to Playground and run a simple request. Explain:

- which route target was chosen
- whether the provider was local, cache, or premium
- whether fallback occurred
- how the immediate metadata differs from the recorded ledger outcome

This ties the benchmark evidence to the live product surface.

### 4. Finish on Observability

Open Observability and show:

- usage ledger evidence for the request
- dependency health cards
- how degraded optional dependencies remain visible

Use this moment to explain fallback or degraded behavior deliberately rather than treating it as an exception.

## What to emphasize

- Nebula is not hiding premium use; it is making the tradeoff measurable
- benchmark-demo is a smaller slice of the same proof model as the full benchmark suite
- fallback is part of the trust story, not an embarrassment to skip
- Observability closes the loop after Playground shows the immediate response metadata

## What not to claim

- do not describe estimated premium cost as invoice-accurate billing
- do not imply a hosted control plane or enterprise packaging that the repo does not ship
- do not present local development commands as a second supported deployment path

## Related docs

- [README](../README.md)
- [Evaluation](evaluation.md)
- [Architecture](architecture.md)
- [Self-hosting](self-hosting.md)
