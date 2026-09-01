# Nebula Benchmark Report

- Run ID: `<run-id>`
- Generated At: `<generated-at>`
- Dataset: `benchmarks/v1/scenarios.jsonl`
- Target: `http://127.0.0.1:8000`

## Summary

- Total Requests: `3`
- Passed: `3`
- Failed: `0`
- Skipped: `0`
- Cache Hit Rate: `0.0`
- Fallback Rate: `0.0`
- Estimated Premium Cost: `0.0004`
- Estimated Premium Cost Avoided: `1.16e-05`

## Key Takeaways

- Nebula avoided an estimated premium spend of 1.16e-05 across 3 executed requests while keeping measured premium spend at 0.0004.
- Route mix favored local:2, premium:1, showing how local, cache, and premium paths split in one repeatable run.
- Warm-cache and fallback behavior stayed explicit with cache_hit_rate=0.0 and fallback_rate=0.0.
- All executed scenarios matched their expected route, cache, and fallback outcomes.

## Comparison Groups

| Group | Story Role | Scenarios | Passed | Median Latency (ms) | Route Mix |
| --- | --- | ---: | ---: | ---: | --- |
| Premium control | Premium baseline for cost and latency comparison. | 1 | 1 | 800.0 | premium:1 |
| Local control | Direct local execution proving avoided premium spend. | 1 | 1 | 42.0 | local:1 |
| Auto-routing cold | Cold auto-routing behavior before cache reuse. | 1 | 1 | 60.0 | local:1 |
| Auto-routing warm cache | Warm-cache behavior showing low-latency repeat traffic. | 0 | 0 | 0.0 | - |
| Fallback resilience | Forced local failure path proving the premium fallback story. | 0 | 0 | 0.0 | - |
| Supporting premium-routed evidence | Supporting evidence for premium-routed complex prompts without replacing the top-line five-group story. | 0 | 0 | 0.0 | - |

## Route and Cost Highlights

- Route Distribution: `local:2, premium:1`
- Cache Hit Rate: `0.0`
- Fallback Rate: `0.0`
- Estimated Premium Cost: `0.0004`
- Estimated Premium Cost Avoided: `1.16e-05`

## Scenario Results

| Scenario | Mode | Status | Latency (ms) | Route | Provider | Cache | Fallback | Premium Cost | Avoided Cost |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
| p1 | premium_direct | passed | 800.0 | premium | openai-compatible | False | False | 0.0004 | - |
| l1 | local_direct | passed | 42.0 | local | ollama | False | False | 0.0 | 6.6e-06 |
| c1 | auto_simple_cold | passed | 60.0 | local | ollama | False | False | 0.0 | 5e-06 |
