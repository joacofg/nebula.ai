"""Stage 4: draw the Spanish pairs a human grades, before any judge runs.

    python -m scripts.ground_truth.holdout

The draw depends on the seed and the corpus only, so it cannot lean toward
the pairs the judges find easy or hard. The two cross-prompt pairs exist for
the calibration round of the labelling session and are never scored.

Then:  python -m scripts.metric_validation.label --rater human-es-1 \\
         --pairs benchmarks/ground-truth/v1/holdout/pairs.jsonl \\
         --labels benchmarks/ground-truth/v1/holdout/labels
"""

from __future__ import annotations

import argparse
import random
from dataclasses import replace
from pathlib import Path

from scripts.ground_truth import capture, cli, pairs, records
from scripts.metric_validation import blinding, raters
from scripts.metric_validation.corpus import Pair, TASK_TYPES, write_pairs

HOLDOUT_PER_TASK = 10
SEED = 20260927
RATER = "human-es-1"


def holdout_dir(root: Path) -> Path:
    return root / "holdout"


def select_holdout(pairs_es: list[Pair], *, per_task: int, seed: int) -> list[Pair]:
    ordered = sorted(pairs_es, key=lambda p: p.pair_id)
    out: list[Pair] = []
    for task_index, task in enumerate(TASK_TYPES):
        rng = random.Random(f"{seed}:{task}")
        # Rotate who gets the extra slot so the totals differ by at most one.
        shares = [per_task // 3] * 3
        for extra in range(per_task % 3):
            shares[(task_index + extra) % 3] += 1
        used: set[str] = set()
        for candidate, share in zip(pairs.CANDIDATES, shares, strict=True):
            pool = [p for p in ordered if p.task_type == task
                    and pairs.split_pair_id(p.pair_id)[1] == candidate
                    and pairs.split_pair_id(p.pair_id)[2] not in used]
            if len(pool) < share:
                raise ValueError(f"{task}/{candidate}: {len(pool)} pairs for {share} slots.")
            for picked in rng.sample(pool, share):
                used.add(pairs.split_pair_id(picked.pair_id)[2])
                out.append(picked)
    return sorted(out, key=lambda p: p.pair_id)


def calibration_negatives(pairs_es: list[Pair], *, seed: int, count: int = 2) -> list[Pair]:
    """A reference answer shown against the reference answer to another prompt."""
    refs: dict[str, Pair] = {}
    for p in sorted(pairs_es, key=lambda p: p.pair_id):
        refs.setdefault(pairs.split_pair_id(p.pair_id)[2], p)
    prompt_ids = sorted(refs)
    rng = random.Random(f"{seed}:calibration")
    out: list[Pair] = []
    for prompt_id in rng.sample(prompt_ids, count):
        base = refs[prompt_id]
        siblings = [i for i in prompt_ids if i != prompt_id and refs[i].task_type == base.task_type]
        other = refs[rng.choice(siblings)]
        out.append(replace(
            base,
            pair_id=f"xpr:{prompt_id}",
            kind="cross_prompt",
            left=base.right,
            right=replace(other.right, origin="reference_offtarget"),
        ))
    return out


def calibration_positive(pairs_es: list[Pair], *, rater_id: str) -> Pair:
    """The pair label.py will turn into its identical and truncated items.

    label.py takes the first local-vs-premium pair in the rater's presentation
    order, and a pair shown with its answer is not graded. Taking the corpus-wide
    first one, and keeping it out of the draw, leaves all 50 drawn pairs graded.
    """
    local = [p for p in pairs_es if p.kind == "local_vs_premium"]
    first = blinding.presentation_order([p.pair_id for p in local], rater_id=rater_id)[0]
    return next(p for p in local if p.pair_id == first)


def build_holdout(pairs_es: list[Pair], *, seed: int, rater_id: str) -> list[Pair]:
    positive = calibration_positive(pairs_es, rater_id=rater_id)
    graded = select_holdout(
        [p for p in pairs_es if p.pair_id != positive.pair_id], per_task=HOLDOUT_PER_TASK, seed=seed
    )
    return graded + [positive] + calibration_negatives(pairs_es, seed=seed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    prompts = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    corpus_pairs, _ = pairs.build_pairs("es", prompts, capture.load_responses(root, "es"))
    built = build_holdout(corpus_pairs, seed=SEED, rater_id=RATER)
    target = holdout_dir(root) / "pairs.jsonl"
    if target.exists():
        raise RuntimeError(f"{target} exists; the hold-out is drawn once.")
    target.parent.mkdir(parents=True, exist_ok=True)
    write_pairs(built, target)
    raters.write_roster(
        {RATER: raters.RaterProfile(RATER, "human", "rater-a", "active",
                                    "Spanish hold-out, 50 pairs drawn before any judge ran")},
        holdout_dir(root) / "raters.json",
    )
    cli.update_provenance(root, holdout_seed=SEED, holdout_sha256=cli.sha256_of(target))
    print(f"{len(built)} hold-out pairs (50 graded + 3 calibration) → {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
