"""Stage 6b: a second Spanish labelling set, aimed at the judges' rejections.

    python -m scripts.ground_truth.negatives

The random hold-out came back 45/50 substitutable, which leaves five negatives
to say whether the judges are right when they reject a cheap answer. This set
draws 25 pairs the ensemble rejected and 10 it accepted, mixed and blind, so
the rater cannot infer the verdict from the set. It is not a random sample and
is reported as a targeted check, never pooled with the hold-out.

Code pairs are left out: the labelling terminal re-wraps code blocks, and the
rater flagged their code grades on the hold-out as low-confidence.

Then:  python -m scripts.metric_validation.label --rater human-es-1 \\
         --pairs benchmarks/ground-truth/v1/negatives/pairs.jsonl \\
         --labels benchmarks/ground-truth/v1/negatives/labels
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from scripts.ground_truth import capture, cli, ensemble, holdout, judge, pairs, records, validate
from scripts.metric_validation.corpus import TASK_TYPES, Pair, read_pairs, write_pairs

REJECTED = 25
DECOYS = 10
SEED = 20260930
SKIPPED_TASKS = frozenset({"code"})


def negatives_dir(root: Path) -> Path:
    return root / "negatives"


def _spread(total: int, tasks: list[str]) -> dict[str, int]:
    shares = {task: total // len(tasks) for task in tasks}
    for task in tasks[: total % len(tasks)]:
        shares[task] += 1
    return shares


def select(
    pairs_es: list[Pair],
    verdicts: dict[str, bool],
    *,
    exclude_prompts: set[str],
    rejected: int,
    decoys: int,
    seed: int,
) -> list[Pair]:
    tasks = [t for t in TASK_TYPES if t not in SKIPPED_TASKS]
    eligible = sorted(
        (p for p in pairs_es
         if p.pair_id in verdicts
         and p.task_type in tasks
         and pairs.split_pair_id(p.pair_id)[2] not in exclude_prompts),
        key=lambda p: p.pair_id,
    )
    out: list[Pair] = []
    used: set[str] = set()
    for accepted, total in ((False, rejected), (True, decoys)):
        for task, share in _spread(total, tasks).items():
            pool = [p for p in eligible if p.task_type == task and verdicts[p.pair_id] is accepted
                    and pairs.split_pair_id(p.pair_id)[2] not in used]
            if len(pool) < share:
                raise ValueError(f"{task}: {len(pool)} {'accepted' if accepted else 'rejected'} "
                                 f"pairs for {share} slots.")
            for picked in random.Random(f"{seed}:{task}:{accepted}").sample(pool, share):
                used.add(pairs.split_pair_id(picked.pair_id)[2])
                out.append(picked)
    return sorted(out, key=lambda p: p.pair_id)


def build(
    pairs_es: list[Pair],
    verdicts: dict[str, bool],
    *,
    exclude_prompts: set[str],
    seed: int,
    rater_id: str,
) -> list[Pair]:
    positive = holdout.calibration_positive(pairs_es, rater_id=rater_id)
    drawn = select(
        [p for p in pairs_es if p.pair_id != positive.pair_id], verdicts,
        exclude_prompts=exclude_prompts, rejected=REJECTED, decoys=DECOYS, seed=seed,
    )
    return drawn + [positive] + holdout.calibration_negatives(pairs_es, seed=seed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    rule = json.loads((root / "validation.json").read_text())["rule_selection"]["chosen"]
    prompts = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    corpus_pairs, _ = pairs.build_pairs("es", prompts, capture.load_responses(root, "es"))
    grades = ensemble.grades_by_pair(validate._judgements(root, "corpus"),
                                     judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    verdicts = {pid: ensemble.substitutable(rule, g) for pid, g in grades.items()}
    already = {pairs.split_pair_id(p.pair_id)[2]
               for p in read_pairs(holdout.holdout_dir(root) / "pairs.jsonl")
               if not p.pair_id.startswith("xpr:")}
    target = negatives_dir(root) / "pairs.jsonl"
    if target.exists():
        raise RuntimeError(f"{target} exists; the set is drawn once.")
    built = build(corpus_pairs, verdicts, exclude_prompts=already, seed=SEED, rater_id=holdout.RATER)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_pairs(built, target)
    cli.update_provenance(root, negatives_seed=SEED, negatives_rule=rule,
                          negatives_sha256=cli.sha256_of(target))
    print(f"{REJECTED} rejected + {DECOYS} accepted pairs (+ calibration) → {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
