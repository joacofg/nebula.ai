"""Stage 1: draw the stratified English corpus.

    python -m scripts.ground_truth.sample

200 prompts per task type plus a reserve of 20 that replaces prompts the
translation stage rejects, so every stratum stays at 200 in Spanish.
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence
from pathlib import Path

from scripts.ground_truth import cli, records, sources
from scripts.metric_validation.corpus import TASK_TYPES

PER_TASK = 200
RESERVE_PER_TASK = 20
EN_PER_TASK = 50
SEED = 20260927
MAX_PROMPT_CHARS = 6000  # ~1500 tokens
MIN_PROMPT_CHARS = 12


def _eligible(candidates: Sequence[sources.Candidate]) -> list[sources.Candidate]:
    seen: set[str] = set()
    out: list[sources.Candidate] = []
    for candidate in sorted(candidates, key=lambda c: c.source_id):
        text = candidate.prompt.strip()
        if not MIN_PROMPT_CHARS <= len(text) <= MAX_PROMPT_CHARS or text in seen:
            continue
        seen.add(text)
        out.append(candidate)
    return out


def stratified_sample(
    candidates: Sequence[sources.Candidate], *, per_task: int, reserve_per_task: int, seed: int
) -> list[records.PromptRow]:
    by_task: dict[str, list[sources.Candidate]] = {}
    for candidate in _eligible(candidates):
        by_task.setdefault(candidate.task_type, []).append(candidate)

    rows: list[records.PromptRow] = []
    for task in TASK_TYPES:
        pool = by_task.get(task, [])
        wanted = per_task + reserve_per_task
        if len(pool) < wanted:
            raise ValueError(f"Task {task!r} has {len(pool)} eligible prompts; {wanted} needed.")
        picked = random.Random(f"{seed}:{task}").sample(pool, wanted)
        for index, candidate in enumerate(picked):
            rows.append(
                records.PromptRow(
                    prompt_id=f"{task}-{index:04d}",
                    task_type=task,
                    source=candidate.source_id,
                    prompt=candidate.prompt.strip(),
                    role="corpus" if index < per_task else "reserve",
                )
            )
    return rows


def notice() -> str:
    lines = ["Prompts in this directory are derived from the following datasets.", ""]
    for source in sources.SOURCES.values():
        lines.append(f"- {source.name}: {source.citation}. License: {source.license}. {source.url}")
    lines += ["", "Spanish prompts are machine translations of the originals (same licenses)."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    args = parser.parse_args()

    loaders = {
        "dolly": sources.dolly_candidates,
        "gsm8k": sources.gsm8k_candidates,
        "mbpp": sources.mbpp_candidates,
    }
    candidates: list[sources.Candidate] = []
    for name, loader in loaders.items():
        path = sources.fetch(sources.SOURCES[name], cli.SOURCES_DIR)
        candidates += loader(sources.read_jsonl(path))

    rows = stratified_sample(
        candidates, per_task=PER_TASK, reserve_per_task=RESERVE_PER_TASK, seed=SEED
    )
    records.write_rows(rows, args.root / "prompts.en.jsonl")
    (args.root / "NOTICE").write_text(notice(), encoding="utf-8")
    cli.update_provenance(
        args.root,
        sample_seed=SEED,
        sources={n: {"url": s.url, "sha256": s.sha256, "license": s.license} for n, s in sources.SOURCES.items()},
        prompts_en_sha256=cli.sha256_of(args.root / "prompts.en.jsonl"),
    )
    print(f"{len(rows)} prompts → {args.root / 'prompts.en.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
