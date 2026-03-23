# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? | Made By |
|---|------|-------|----------|--------|-----------|------------|---------|
| D001 | M001 | arch | v3.0 API strategy | Hybrid: OpenAI-compatible inference plus Nebula-native control surfaces | A pure Nebula-native API increases adoption friction; a pure compatibility layer undersells Nebula’s differentiated value | No | collaborative |
| D002 | M001 | scope | v3.0 primary emphasis | Focus v3.0 on adoption path clarity, migration proof, and day-1 value visibility rather than broad new infrastructure | Nebula is already reasonably strong as infrastructure; the weak spot is how teams adopt and understand it | No | collaborative |
| D003 | M001 | scope | Compatibility promise | Keep the initial OpenAI-compatible promise tight and reliable around common chat-completions flows | Broad compatibility would expand surface area and maintenance risk before the contract is proven | Yes — if repeated adoption demand proves a wider surface is required | collaborative |
| D004 | M001 | pattern | Reference proof style | Use a realistic migration integration rather than a toy demo as the main adoption proof | Platform-minded teams trust believable migration proof more than greenfield showcase apps | Yes — if a stronger representative reference target emerges during execution | collaborative |
| D005 | M001 | pattern | Production structuring model in v3.0 | Make tenant / app / workload / operator boundaries explicit in M001, but keep enforcement lightweight unless adoption proof demands more | The model needs to be understandable now, but a heavy product-surface redesign would distract from the adoption milestone | Yes — if lightweight modeling proves insufficient during implementation | collaborative |
