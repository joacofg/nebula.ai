"""Stage 5: both judges grade every candidate-vs-reference pair, both ways round.

    python -m scripts.ground_truth.judge --set pilot
    python -m scripts.ground_truth.judge --set corpus --langs es,en

The corpus set refuses to run until the pre-registration is committed and the
hold-out is drawn: the rules must be fixed before anyone sees a judge's grade.
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from collections.abc import Callable
from pathlib import Path

from scripts.ground_truth import capture, cli, holdout, llm, pairs, records, spend
from scripts.metric_validation import labels as mv_labels
from scripts.metric_validation import llm_judge
from scripts.metric_validation.corpus import Pair, read_pairs

JUDGES: tuple[str, ...] = ("google/gemini-2.5-flash", "deepseek/deepseek-chat-v3-0324")
ORIENTATIONS: tuple[str, ...] = ("ab", "ba")
JUDGE_MAX_TOKENS = 200
# Thinking tokens are billed and a grade needs none.
JUDGE_EXTRA: dict[str, dict] = {"google/gemini-2.5-flash": {"reasoning": {"max_tokens": 0}}}
CONCURRENCY = 8
PILOT_ROOT = Path("benchmarks/metric-validation")
PILOT_RATER = "human-3"


def judgements_path(root: Path, judge_model: str, set_name: str) -> Path:
    return root / "judgements" / f"{set_name}.{llm_judge.rater_id_for(judge_model)}.jsonl"


def payload(pair: Pair, orientation: str) -> dict[str, str]:
    first, second = (pair.left, pair.right) if orientation == "ab" else (pair.right, pair.left)
    return {"pair_id": pair.pair_id, "prompt": pair.prompt, "response_a": first.text, "response_b": second.text}


def judge_prompt_for(pair: Pair, orientation: str) -> str:
    return llm_judge.judge_prompt(payload(pair, orientation))


async def judge_pairs(
    pair_list: list[Pair],
    *,
    judge_model: str,
    chat: llm.Chat,
    out_path: Path,
    ledger: spend.SpendLedger,
    concurrency: int,
    parse_attempts: int = 3,
    orientations: tuple[str, ...] = ORIENTATIONS,
) -> None:
    done = records.latest(records.read_rows(out_path, records.Judgement), key=lambda r: (r.pair_id, r.orientation))
    gate = asyncio.Semaphore(concurrency)

    async def one(pair: Pair, orientation: str) -> None:
        async with gate:
            reply = ""
            grade: str | None = None
            for _ in range(parse_attempts):
                ledger.check()
                try:
                    c = await llm.with_retries(chat, judge_prompt_for(pair, orientation))
                except llm.CallFailed as error:
                    reply = f"call failed: {error}"
                    break
                ledger.record(stage="judge", model=judge_model, completion=c)
                reply = c.text
                try:
                    grade = llm_judge.parse_grade(reply)
                    break
                except ValueError:
                    continue
            row = records.Judgement(pair.pair_id, judge_model, orientation,
                                    "ok" if grade else "missing", grade, reply[:500])
            records.append_row(row, out_path)

    todo = [(p, o) for p in pair_list for o in orientations
            if (p.pair_id, o) not in done or done[(p.pair_id, o)].status != "ok"]
    await asyncio.gather(*(one(p, o) for p, o in todo))


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


def ensure_preregistered(root: Path, run_git: Callable[..., str] = _git) -> None:
    prereg = root / "preregistration.md"
    if not prereg.exists() or not run_git("log", "-1", "--format=%H", "--", str(prereg)) \
            or run_git("status", "--porcelain", "--", str(prereg)):
        raise RuntimeError(f"{prereg} must be committed, unmodified, before judging the corpus.")
    drawn = holdout.holdout_dir(root) / "pairs.jsonl"
    if (not drawn.exists() or not drawn.read_text(encoding="utf-8").strip()
            or not run_git("log", "-1", "--format=%H", "--", str(drawn))
            or run_git("status", "--porcelain", "--", str(drawn))):
        raise RuntimeError(
            "Draw the hold-out (python -m scripts.ground_truth.holdout) and commit it before judging."
        )


def pilot_pairs() -> list[Pair]:
    graded = {label.pair_id for label in mv_labels.read(PILOT_ROOT / "labels" / f"{PILOT_RATER}.jsonl")}
    return [p for p in read_pairs(PILOT_ROOT / "pairs.jsonl") if p.pair_id in graded]


def corpus_pairs(root: Path, langs: list[str]) -> list[Pair]:
    out: list[Pair] = []
    for lang in langs:
        prompts = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
        if lang == "en":
            english = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
            prompts = [english[r.prompt_id] for r in prompts if r.en_subset]
        built, skipped = pairs.build_pairs(lang, prompts, capture.load_responses(root, lang))
        print(f"{lang}: {len(built)} pairs; skipped {skipped}")
        out += built
    return out


async def run(args: argparse.Namespace) -> int:
    root: Path = args.root
    if args.set == "corpus":
        ensure_preregistered(root)
        pair_list = corpus_pairs(root, args.langs.split(","))
    else:
        pair_list = pilot_pairs()
    ledger = spend.SpendLedger(root / "spend.jsonl", cap_usd=args.cap)
    async with cli.openrouter_client() as client:
        for judge_model in JUDGES:
            chat = llm.openrouter_chat(client, judge_model, max_tokens=JUDGE_MAX_TOKENS,
                                       extra=JUDGE_EXTRA.get(judge_model))
            out = judgements_path(root, judge_model, args.set)
            print(f"{judge_model}: {len(pair_list)} pairs × {len(ORIENTATIONS)} …", flush=True)
            await judge_pairs(pair_list, judge_model=judge_model, chat=chat, out_path=out,
                              ledger=ledger, concurrency=CONCURRENCY)
            rows = records.latest(records.read_rows(out, records.Judgement), key=lambda r: (r.pair_id, r.orientation))
            missing = sum(1 for r in rows.values() if r.status != "ok")
            print(f"  {missing} missing; spent so far USD {ledger.total:.4f}", flush=True)
    cli.update_provenance(root, judges=list(JUDGES), judge_extra=JUDGE_EXTRA, judge_max_tokens=JUDGE_MAX_TOKENS)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    parser.add_argument("--set", choices=("pilot", "corpus"), required=True)
    parser.add_argument("--langs", default="es,en")
    parser.add_argument("--cap", type=float, default=spend.DEFAULT_CAP_USD)
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
