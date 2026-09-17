# Nebula Benchmark Report

- Run ID: `20260819T225703Z`
- Generated At: `2026-08-19T22:57:13.478622+00:00`
- Dataset: `benchmarks/v1/scenarios.jsonl`
- Target: `managed-local`

## Summary

- Total Requests: `14`
- Passed: `14`
- Failed: `0`
- Skipped: `0`
- Cache Hit Rate: `0.2143`
- Fallback Rate: `0.1429`
- Estimated Premium Cost: `0.0002196`
- Estimated Premium Cost Avoided: `0.0001356`

## Key Takeaways

- Nebula avoided an estimated premium spend of 0.0001356 across 14 executed requests while keeping measured premium spend at 0.0002196.
- Route mix favored cache:3, local:5, premium:6, showing how local, cache, and premium paths split in one repeatable run.
- Warm-cache and fallback behavior stayed explicit with cache_hit_rate=0.2143 and fallback_rate=0.1429.
- All executed scenarios matched their expected route, cache, and fallback outcomes.

## Comparison Groups

| Group | Story Role | Scenarios | Passed | Median Latency (ms) | Route Mix |
| --- | --- | ---: | ---: | ---: | --- |
| Premium control | Premium baseline for cost and latency comparison. | 2 | 2 | 145.25 | premium:2 |
| Local control | Direct local execution proving avoided premium spend. | 2 | 2 | 1998.02 | local:2 |
| Auto-routing cold | Cold auto-routing behavior before cache reuse. | 3 | 3 | 368.09 | local:3 |
| Auto-routing warm cache | Warm-cache behavior showing low-latency repeat traffic. | 3 | 3 | 37.29 | cache:3 |
| Fallback resilience | Forced local failure path proving the premium fallback story. | 2 | 2 | 10.99 | premium:2 |
| Supporting premium-routed evidence | Supporting evidence for premium-routed complex prompts without replacing the top-line five-group story. | 2 | 2 | 69.09 | premium:2 |

## Route and Cost Highlights

- Route Distribution: `cache:3, local:5, premium:6`
- Cache Hit Rate: `0.2143`
- Fallback Rate: `0.1429`
- Estimated Premium Cost: `0.0002196`
- Estimated Premium Cost Avoided: `0.0001356`

## Scenario Results

| Scenario | Mode | Status | Latency (ms) | Route | Provider | Cache | Fallback | Premium Cost | Avoided Cost |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
| premium-direct-brief | premium_direct | passed | 183.55 | premium | mock-premium | False | False | 3.21e-05 | - |
| premium-direct-summary | premium_direct | passed | 106.95 | premium | mock-premium | False | False | 3.81e-05 | - |
| local-direct-brief | local_direct | passed | 382.35 | local | ollama | False | False | 0.0 | 8.4e-06 |
| local-direct-list | local_direct | passed | 3613.69 | local | ollama | False | False | 0.0 | 8.43e-05 |
| auto-simple-cold-1 | auto_simple_cold | passed | 353.97 | local | ollama | False | False | 0.0 | 1.005e-05 |
| auto-simple-cold-2 | auto_simple_cold | passed | 368.09 | local | ollama | False | False | 0.0 | 9.9e-06 |
| auto-simple-cold-3 | auto_simple_cold | passed | 368.49 | local | ollama | False | False | 0.0 | 9.9e-06 |
| auto-simple-warm-1 | auto_simple_warm | passed | 45.05 | cache | cache | True | False | 0.0 | 4.35e-06 |
| auto-simple-warm-2 | auto_simple_warm | passed | 34.05 | cache | cache | True | False | 0.0 | 4.35e-06 |
| auto-simple-warm-3 | auto_simple_warm | passed | 37.29 | cache | cache | True | False | 0.0 | 4.35e-06 |
| auto-complex-architecture | auto_complex | passed | 68.93 | premium | mock-premium | False | False | 4.3349999999999997e-05 | - |
| auto-complex-debug | auto_complex | passed | 69.25 | premium | mock-premium | False | False | 4.1849999999999994e-05 | - |
| auto-fallback-hello | auto_fallback | passed | 13.98 | premium | mock-premium | False | True | 3.21e-05 | - |
| auto-fallback-cache | auto_fallback | passed | 8.0 | premium | mock-premium | False | True | 3.21e-05 | - |
