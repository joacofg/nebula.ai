# Nebula Benchmark Report
> **NOT COMPARABLE.** These dependencies were not ready when the run started: `semantic_cache`. Cache-dependent figures below reflect a degraded stack and cannot be compared with a healthy run.


- Run ID: `20260903T143128Z`
- Generated At: `2026-09-03T14:31:32.440385+00:00`
- Dataset: `benchmarks/v1/demo-scenarios.jsonl`
- Target: `managed-local`

## Summary

- Total Requests: `5`
- Passed: `4`
- Failed: `1`
- Skipped: `0`
- Cache Hit Rate: `0.0`
- Fallback Rate: `0.2`
- Estimated Premium Cost: `6.42e-05`
- Estimated Premium Cost Avoided: `2.85e-05`

## Key Takeaways

- Nebula avoided an estimated premium spend of 2.85e-05 across 5 executed requests while keeping measured premium spend at 6.42e-05.
- Route mix favored local:3, premium:2, showing how local, cache, and premium paths split in one repeatable run.
- Warm-cache and fallback behavior stayed explicit with cache_hit_rate=0.0 and fallback_rate=0.2.
- Expectation mismatches were detected in auto-simple-warm-1.

## Comparison Groups

| Group | Story Role | Scenarios | Passed | Median Latency (ms) | Route Mix |
| --- | --- | ---: | ---: | ---: | --- |
| Premium control | Premium baseline for cost and latency comparison. | 1 | 1 | 18.15 | premium:1 |
| Local control | Direct local execution proving avoided premium spend. | 1 | 1 | 300.96 | local:1 |
| Auto-routing cold | Cold auto-routing behavior before cache reuse. | 1 | 1 | 238.05 | local:1 |
| Auto-routing warm cache | Warm-cache behavior showing low-latency repeat traffic. | 1 | 0 | 253.39 | local:1 |
| Fallback resilience | Forced local failure path proving the premium fallback story. | 1 | 1 | 14.53 | premium:1 |
| Supporting premium-routed evidence | Supporting evidence for premium-routed complex prompts without replacing the top-line five-group story. | 0 | 0 | 0.0 | - |

## Route and Cost Highlights

- Route Distribution: `local:3, premium:2`
- Cache Hit Rate: `0.0`
- Fallback Rate: `0.2`
- Estimated Premium Cost: `6.42e-05`
- Estimated Premium Cost Avoided: `2.85e-05`

## Scenario Results

| Scenario | Mode | Status | Latency (ms) | Route | Provider | Cache | Fallback | Premium Cost | Avoided Cost |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
| premium-direct-brief | premium_direct | passed | 18.15 | premium | mock-premium | False | False | 3.21e-05 | - |
| local-direct-brief | local_direct | passed | 300.96 | local | ollama | False | False | 0.0 | 8.4e-06 |
| auto-simple-cold-1 | auto_simple_cold | passed | 238.05 | local | ollama | False | False | 0.0 | 1.005e-05 |
| auto-simple-warm-1 | auto_simple_warm | failed | 253.39 | local | ollama | False | False | 0.0 | 1.005e-05 |
| auto-fallback-hello | auto_fallback | passed | 14.53 | premium | mock-premium | False | True | 3.21e-05 | - |

## Expectation Mismatches

- `auto-simple-warm-1`: Expected route target cache, received local, Expected route reason cache_hit, received token_complexity, Expected cache_hit=True, received False
