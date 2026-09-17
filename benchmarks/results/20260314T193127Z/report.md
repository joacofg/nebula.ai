# Nebula Benchmark Report

- Run ID: `20260314T193127Z`
- Generated At: `2026-03-14T19:31:52.953177+00:00`
- Dataset: `benchmarks/v1/scenarios.jsonl`
- Target: `managed-local`

## Summary

- Total Requests: `14`
- Passed: `14`
- Failed: `0`
- Skipped: `0`
- Cache Hit Rate: `0.2143`
- Fallback Rate: `0.1429`
- Estimated Premium Cost: `0.0004884`
- Estimated Premium Cost Avoided: `0.000162`

## Scenario Results

| Scenario | Mode | Status | Latency (ms) | Route | Provider | Cache | Fallback | Premium Cost | Avoided Cost |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
| premium-direct-brief | premium_direct | passed | 838.21 | premium | openai-compatible | False | False | 5.1e-06 | - |
| premium-direct-summary | premium_direct | passed | 1038.41 | premium | openai-compatible | False | False | 2.28e-05 | - |
| local-direct-brief | local_direct | passed | 377.54 | local | ollama | False | False | 0.0 | 8.4e-06 |
| local-direct-list | local_direct | passed | 4434.1 | local | ollama | False | False | 0.0 | 9.39e-05 |
| auto-simple-cold-1 | auto_simple_cold | passed | 306.42 | local | ollama | False | False | 0.0 | 1.005e-05 |
| auto-simple-cold-2 | auto_simple_cold | passed | 306.01 | local | ollama | False | False | 0.0 | 9.9e-06 |
| auto-simple-cold-3 | auto_simple_cold | passed | 325.06 | local | ollama | False | False | 0.0 | 9.9e-06 |
| auto-simple-warm-1 | auto_simple_warm | passed | 26.85 | cache | cache | True | False | 0.0 | 1.005e-05 |
| auto-simple-warm-2 | auto_simple_warm | passed | 27.42 | cache | cache | True | False | 0.0 | 9.9e-06 |
| auto-simple-warm-3 | auto_simple_warm | passed | 30.91 | cache | cache | True | False | 0.0 | 9.9e-06 |
| auto-complex-architecture | auto_complex | passed | 4528.45 | premium | openai-compatible | False | False | 0.0001518 | - |
| auto-complex-debug | auto_complex | passed | 9197.05 | premium | openai-compatible | False | False | 0.00029805 | - |
| auto-fallback-hello | auto_fallback | passed | 788.94 | premium | openai-compatible | False | True | 5.7e-06 | - |
| auto-fallback-cache | auto_fallback | passed | 441.8 | premium | openai-compatible | False | True | 4.95e-06 | - |
