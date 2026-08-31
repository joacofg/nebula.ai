"""Run the auxiliary LLM rater over the blinded pairs.

    python -m scripts.metric_validation.run_judge --model <model>

It sees exactly what a human rater sees — the same blinded payload, its own
presentation order, no provenance — and its grades land in the same
append-only store under the rater id ``llm-judge``. It is a stand-in for the
second human evaluator, not a replacement: the report labels it auxiliary and
keeps the human-to-human slot open.

A reply that does not carry a rubric grade is not recorded. The pair stays
unlabelled and a re-run retries it, because a defaulted grade would inflate
agreement on exactly the pairs that were hardest to call.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import httpx

from scripts.metric_validation import blinding, capture, corpus, labels, llm_judge
from scripts.metric_validation.build_pilot_corpus import load_dotenv

DEFAULT_ROOT = Path("benchmarks/metric-validation")


async def run(args: argparse.Namespace) -> int:
    load_dotenv()
    provider = os.environ.get("NEBULA_PREMIUM_PROVIDER", "")
    base_url = os.environ.get("NEBULA_PREMIUM_BASE_URL", "")
    api_key = os.environ.get("NEBULA_PREMIUM_API_KEY", "")
    capture.ensure_real_premium(provider=provider, base_url=base_url, model=args.model)
    if not api_key:
        raise RuntimeError("NEBULA_PREMIUM_API_KEY is unset; refusing to run the judge.")

    root: Path = args.root
    pairs = {pair.pair_id: pair for pair in corpus.read_pairs(root / "pairs.jsonl")}
    label_path = root / "labels" / f"{llm_judge.RATER_ID}.jsonl"
    queue = labels.remaining(list(pairs), label_path, rater_id=llm_judge.RATER_ID)
    print(f"{len(queue)} pairs left for {llm_judge.RATER_ID}.")

    unparseable = 0
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=httpx.Timeout(180.0, connect=10.0),
    ) as client:
        for position, pair_id in enumerate(queue, start=1):
            payload = blinding.blinded_payload(pairs[pair_id], rater_id=llm_judge.RATER_ID)
            response = await client.post(
                "/chat/completions",
                json={
                    "model": args.model,
                    "messages": [{"role": "user", "content": llm_judge.judge_prompt(payload)}],
                    "temperature": 0.0,
                },
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]

            try:
                grade = llm_judge.parse_grade(reply)
            except ValueError as error:
                unparseable += 1
                print(f"  [{position}/{len(queue)}] {pair_id}: {error}")
                continue

            labels.append(
                labels.Label(pair_id=pair_id, rater_id=llm_judge.RATER_ID, grade=grade),
                label_path,
            )
            print(f"  [{position}/{len(queue)}] {pair_id}: {grade}")

    if unparseable:
        print(f"\n{unparseable} replies carried no rubric grade and were left unlabelled.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--model", required=True, help="judge model, e.g. openai/gpt-4o-mini")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
