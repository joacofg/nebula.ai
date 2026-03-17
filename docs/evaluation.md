# Nebula Evaluation Guide

Nebula's evaluation package is designed to prove one claim: the gateway can reduce estimated premium spend on repeatable traffic while keeping route, cache, and fallback behavior legible to operators.

## Benchmark entrypoints

Run the canonical benchmark suite:

```bash
make benchmark
```

Run the faster live-demo subset:

```bash
make benchmark-demo
```

Run against an existing server:

```bash
BASE_URL=http://127.0.0.1:8000 .venv/bin/python -m nebula.benchmarking.run
```

When `BASE_URL` is set, fallback-only scenarios are skipped because the benchmark runner cannot safely mutate an external runtime.

## Benchmark datasets

Nebula ships two versioned datasets:

- `benchmarks/v1/scenarios.jsonl`: the canonical full proof suite
- `benchmarks/v1/demo-scenarios.jsonl`: the smaller live-demo subset

The demo subset intentionally covers one scenario each for:

- premium control
- local control
- auto-routing cold
- auto-routing warm cache
- fallback resilience

The full suite keeps additional supporting evidence such as `auto_complex`.

## Output artifacts

Each run writes artifacts under `artifacts/benchmarks/<timestamp>/`:

- `report.json`: machine-readable summary and per-scenario rows
- `report.md`: human-readable evaluation package

The Phase 5 `report.md` layout is summary-first:

1. key takeaways
2. comparison groups
3. route and cost highlights
4. raw scenario results
5. expectation mismatches

For a concrete example, see `artifacts/benchmarks/20260314T193127Z/report.md`.

## How to read the benchmark proof

### Key takeaways

This section answers the first evaluation questions:

- how much estimated premium spend Nebula avoided
- how much traffic still went to premium
- whether cache hits and fallbacks were explicit
- whether any scenarios diverged from expected behavior

### Comparison groups

The comparison-group summary exists to tell the product story without making readers infer everything from raw rows. It organizes results into:

- premium baseline
- local-control savings
- cold auto-routing behavior
- warm-cache reuse
- fallback resilience
- supporting premium-routed evidence

### Raw scenario rows

The raw rows are still important. They preserve:

- route target
- provider
- cache-hit and fallback flags
- latency
- estimated premium cost
- avoided cost where applicable

## Estimated premium cost and avoided cost

Nebula estimates premium spend using `benchmarks/pricing.json`.

That means:

- cost values are consistent and repeatable within the repo
- cost values are useful for product comparison
- cost values are not invoice reconciliation

Treat them as proof-friendly estimates, not a billing export.

## What counts as strong evidence

A convincing benchmark run should show:

- premium control scenarios that establish the expensive baseline
- local or cache paths that avoid premium spend
- fallback scenarios that prove degraded behavior stays explicit
- no unexplained expectation mismatches

If expectation mismatches do occur, they should be investigated rather than hidden. The benchmark package is supposed to surface those failures directly.

## Manual review checklist

After running `make benchmark` or `make benchmark-demo`, check:

- the first screen of `report.md` explains savings and route mix before the raw table
- fallback behavior is visible instead of buried
- the route and cost story lines up with the gateway and console behavior you see elsewhere in the repo

## Related docs

- [README](../README.md)
- [Architecture](architecture.md)
- [Demo script](demo-script.md)
- [Self-hosting](self-hosting.md)
