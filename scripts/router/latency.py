"""Time each candidate on a fixed sample of Spanish prompts.

    python -m scripts.router.latency [--n 30]

The frontier puts the local model at zero cost; its price is time. This
measures it on this machine, sequentially, so the numbers are per-request
latencies and not throughput under concurrency.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
from pathlib import Path
from time import perf_counter

from scripts.ground_truth import capture, cli, llm, records, spend

OUT = Path("benchmarks/router/v1")
CAP_USD = 1.0


def sample(rows: list[records.PromptRow], n: int) -> list[records.PromptRow]:
    tasks = sorted({r.task_type for r in rows})
    per_task = max(1, n // len(tasks))
    out = []
    for task in tasks:
        out += sorted((r for r in rows if r.task_type == task), key=lambda r: r.prompt_id)[:per_task]
    return out


def summarise(seconds: list[float]) -> dict[str, float]:
    ordered = sorted(seconds)
    return {"n": len(ordered), "median_s": statistics.median(ordered),
            "p90_s": ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))], "mean_s": statistics.mean(ordered)}


async def run(n: int) -> int:
    rows = sample(records.read_rows(Path("benchmarks/ground-truth/v1/prompts.es.jsonl"), records.PromptRow), n)
    ledger = spend.SpendLedger(OUT / "spend.jsonl", cap_usd=CAP_USD)
    OUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    async with cli.openrouter_client() as premium, cli.ollama_client() as ollama:
        for role, (kind, model) in capture.ROLES.items():
            chat = (llm.ollama_chat(ollama, model, max_tokens=capture.MAX_TOKENS) if kind == "ollama"
                    else llm.openrouter_chat(premium, model, max_tokens=capture.MAX_TOKENS))
            if kind == "ollama":
                await chat("hola")  # load the weights before timing
            seconds = []
            for row in rows:
                if kind == "openrouter":
                    ledger.check()
                start = perf_counter()
                completion = await llm.with_retries(chat, row.prompt)
                seconds.append(perf_counter() - start)
                if kind == "openrouter":
                    ledger.record(stage="latency", model=model, completion=completion)
            results[role] = {"model": model, **summarise(seconds)}
            print(role, results[role], flush=True)
    (OUT / "latency.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30)
    return asyncio.run(run(parser.parse_args().n))


if __name__ == "__main__":
    raise SystemExit(main())
