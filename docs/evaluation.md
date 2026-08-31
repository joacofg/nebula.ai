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

## Metric validation (v4.0 Phase 1, T1)

Everything Phase 1 measures rests on one assumption: that cosine similarity
between two responses, embedded with `nomic-embed-text`, tracks whether a
reader would accept one in place of the other. That assumption is not obvious
and it has never been checked in this repository. This study checks it.

It is a study, not a gate. Nothing here runs during `make benchmark`, and
nothing here touches the serving path.

### What it produces

- **A task prefix.** `nomic-embed-text` accepts `search_query:`,
  `search_document:` and `clustering:`. Comparing two answers is none of those
  three, so running the model bare is a fourth candidate. The prefix changes
  the numbers, so it has to be fixed and written down. The study picks it by
  ROC AUC against human grades, with Spearman against the ordinal grade as a
  secondary criterion, and reports all four variants so the choice is visible.
- **A separation table.** How often responses in each similarity band were
  judged substitutable. This is what tells you where the cosine stops carrying
  information.
- **An inter-rater agreement figure**, which is what makes the grades usable as
  ground truth in the first place.

### The rubric

Raters see a prompt and two candidate responses, labelled A and B, and answer:

> Could either response have replaced the other for the person who asked this
> question, without them being worse off?

The scale is ordinal, best to worst:

| grade | meaning |
|---|---|
| `equivalent` | Same substance. Wording, ordering or length may differ, but a reader would take away the same answer from either one. |
| `minor_loss` | Same substance, one side slightly poorer: an omitted caveat, a thinner example, a clumsier structure. A reader would still be served. |
| `partial` | Overlapping but materially different: one side answers only part of the question, or adds a claim the other does not support. |
| `divergent` | Different answers, or one side is wrong, off-topic, or unusable. A reader would notice the swap immediately. |

The binary the routing decision actually cares about is derived by cutting
between `minor_loss` and `partial`. The question is symmetric, which is what
allows the two sides to be shuffled without having to unblind anything later.

### Blinding

A rater must not be able to infer which response came from the local model,
what the cosine says, or which band the pair was sampled from. Any of the three
would turn the study into a check that the rater can read the metric.

- Which response is shown as A is decided per rater and per pair, by SHA-256 of
  the two ids. Not `hash()`: Python salts that per process, so a resumed
  labelling sitting would get a different orientation than the one it resumes.
- Presentation order is shuffled per rater, so position in the queue cannot
  correlate with similarity band.
- The payload handed to a rater carries four fields and no others: pair id,
  prompt, response A, response B.

The LLM rater receives that same payload, through the same function.

### The pilot corpus

80 prompts, 16 in each of five task types (`factual_qa`, `summarisation`,
`code`, `multistep_reasoning`, `open_writing`), committed at
`benchmarks/metric-validation/prompts.jsonl`. They are English-only, matching
the public routing benchmarks T12 will vendor; mixing languages would confound
the similarity scores.

130 pairs are assembled from them, in three kinds:

| kind | count | what it is | why |
|---|---|---|---|
| `local_vs_premium` | 80 | the local answer against the premium answer to the same prompt | the case the metric is actually used on |
| `premium_vs_premium` | 25 | two different premium models on the same prompt | the noise floor — the ceiling the metric can reach when both answers are good |
| `cross_prompt` | 25 | a premium answer against a premium answer to a *different* prompt of the same task type | a planted negative, so the low band is populated and AUC is measurable |

The planted pairs are drawn by round-robin over the task types, not off the
head of a sorted list, so all five types are represented in each planted kind.
A cross-prompt negative borrows from the cyclic successor within its own task
type: a single cycle over the group, so no two prompts can borrow from each
other and no two planted pairs hold the same two texts. Two pairs holding the
same texts would score identically and count one observation twice, in the AUC
and in every bootstrap resample.

The planted kinds exist because nothing guarantees the natural pairs span the
range. If the local model happened to answer well everywhere, every pair would
be substitutable and the separation would be unmeasurable. The report gives the
separation table twice — over all pairs, and restricted to `local_vs_premium`.
The restricted one is the honest one.

The noise floor uses two different premium models rather than one model sampled
twice, because at temperature 0 a model reproduces itself and the resulting
floor would measure nothing.

### Running it

```bash
# 1. Capture. ~240 completions, resumable; re-running costs nothing already paid for.
make metric-corpus PREMIUM_B=<a second premium model id>

# 2. Label, once per human rater. Resumable; Ctrl-C is safe.
make metric-label RATER=human-1

# 3. The auxiliary LLM rater, over the same blinded pairs.
make metric-judge JUDGE_MODEL=<model id>

# 4. Report.
make metric-report RATER=human-1
```

Capture refuses to run against Nebula's mock premium provider. The mock echoes
the prompt back, so every reference it produced would sit close to the prompt
rather than to a real answer, and the whole study would read as a success.

`provenance.json` pins the run: model digests, the Ollama version, the
temperature, and SHA-256 of both the prompt file and the pair file.

### What the numbers do and do not say

The LLM rater is **auxiliary**. Rigour point 3 of the Phase 1 plan asks for two
human evaluators, and one human plus a language model is not that. Its
agreement with the human rater is evidence that the rubric is specific enough
to be applied consistently; it is not the inter-rater agreement the plan
requires. The report prints `PENDING` in that slot and labels the LLM as
auxiliary in every table it appears in, until a second person labels the corpus.

Quantities that cannot be computed are reported as such. An AUC over grades
that all fall on one side of the substitutable cut comes back as "no measurable
separation", never as 0.5. Bootstrap intervals report how many resamples the
statistic could not score, because an interval built on part of the requested
resamples is a weaker claim than one built on all of them.

The statistics are implemented in `scripts/metric_validation/stats.py` in plain
Python — Cohen's kappa, quadratic-weighted kappa, Krippendorff's ordinal alpha,
ROC AUC, Spearman with midranks, and a percentile bootstrap. Each is checked in
`tests/test_metric_validation.py` against a value worked out by hand.

## Related docs

- [README](../README.md)
- [Architecture](architecture.md)
- [Demo runbook](demo-runbook.md)
- [Self-hosting](self-hosting.md)
