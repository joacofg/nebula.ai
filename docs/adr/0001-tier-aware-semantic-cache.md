# Tier-aware semantic cache keyed by conversation context

A cached answer is reused only for the same conversation context (`context_hash`: SHA-256 of every message except the latest user message) and only by a request whose routed tier it satisfies (the entry's `tier_rank` >= the rank of the chosen tier, with local = 0, economy = 1, frontier = 2). We chose quality over hit rate: a frontier-routed request must never receive an answer produced by a weaker tier, and the same last user message under a different system prompt or history is a different question.

## Considered Options

- **Any similar entry serves** (match on the embedding of the latest user message alone): rejected. It maximizes hit rate, but it can serve a local or economy answer to a request the router sent to frontier, and it ignores the system prompt and prior turns, so it returns answers written for another conversation.

## Consequences

- Lower hit rate than a context-blind, tier-blind cache.
- Cold start after upgrade: existing Qdrant points lack `tier_rank` and can never match, so they are deleted at startup and the cache starts empty once.
