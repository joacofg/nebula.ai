"""Stage 6: how well the ensemble agrees with a human reader.

    python -m scripts.ground_truth.validate

English picks the rule; Spanish, drawn before the judges ran, tests it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.ground_truth import cli, ensemble, holdout, judge, records
from scripts.metric_validation import labels as mv_labels
from scripts.metric_validation import rubric, stats

SEED = 20260927
JUDGE_LIMITED_BELOW = 0.4


def rule_kappas(pair_grades: dict[str, list[str]], human: dict[str, str]) -> dict[str, float | None]:
    common = sorted(set(pair_grades) & set(human))
    if not common:
        raise ValueError("No pair has both a full set of judge grades and a human grade.")
    out: dict[str, float | None] = {}
    truth = [rubric.is_substitutable(human[p]) for p in common]
    for rule in ensemble.RULES:
        predicted = [ensemble.substitutable(rule, pair_grades[p]) for p in common]
        try:
            out[rule] = stats.cohens_kappa(predicted, truth)
        except ValueError:
            out[rule] = None
    return out


def position_flip_rate(judgements: list[records.Judgement], judge_model: str) -> float:
    latest = records.latest(
        (r for r in judgements if r.judge == judge_model and r.status == "ok"),
        key=lambda r: (r.pair_id, r.orientation),
    )
    both = [p for p in {k[0] for k in latest} if (p, "ab") in latest and (p, "ba") in latest]
    if not both:
        raise ValueError(f"No pair graded both ways by {judge_model}.")
    flips = sum(
        1 for p in both
        if rubric.is_substitutable(latest[(p, "ab")].grade) != rubric.is_substitutable(latest[(p, "ba")].grade)
    )
    return flips / len(both)


def inter_judge_kappa(judgements: list[records.Judgement]) -> float:
    latest = records.latest((r for r in judgements if r.status == "ok"),
                            key=lambda r: (r.pair_id, r.orientation, r.judge))
    first, second = judge.JUDGES
    keys = sorted({(k[0], k[1]) for k in latest if (k[0], k[1], first) in latest and (k[0], k[1], second) in latest})
    return stats.cohens_kappa(
        [rubric.is_substitutable(latest[(*k, first)].grade) for k in keys],
        [rubric.is_substitutable(latest[(*k, second)].grade) for k in keys],
    )


def holdout_agreement(pair_grades: dict[str, list[str]], human: dict[str, str], rule: str, *, seed: int) -> dict:
    common = sorted(set(pair_grades) & set(human))
    if not common:
        return {"status": "pending", "labelled": len(human), "compared": 0}
    sample = [(ensemble.substitutable(rule, pair_grades[p]), rubric.is_substitutable(human[p])) for p in common]
    interval = stats.bootstrap_ci(
        sample, lambda draw: stats.cohens_kappa([a for a, _ in draw], [b for _, b in draw]), seed=seed
    )
    per_rule = rule_kappas(pair_grades, human)
    return {
        "status": "complete" if len(common) >= holdout.HOLDOUT_PER_TASK * 5 else "partial",
        "labelled": len(human),
        "compared": len(common),
        "excluded_without_full_grades": len(set(human) - set(pair_grades)),
        "kappa": interval.point,
        "ci95": [interval.low, interval.high],
        "resamples_used": interval.resamples_used,
        "judge_limited": interval.point < JUDGE_LIMITED_BELOW,
        "all_rules_for_reference": per_rule,
    }


def _judgements(root: Path, set_name: str) -> list[records.Judgement]:
    rows: list[records.Judgement] = []
    for model in judge.JUDGES:
        rows += records.read_rows(judge.judgements_path(root, model, set_name), records.Judgement)
    return rows


def validate(root: Path) -> dict:
    pilot = _judgements(root, "pilot")
    pilot_grades = ensemble.grades_by_pair(pilot, judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    human3 = {lab.pair_id: lab.grade for lab in mv_labels.read(judge.PILOT_ROOT / "labels" / f"{judge.PILOT_RATER}.jsonl")}
    en = rule_kappas(pilot_grades, human3)
    chosen = ensemble.choose_rule(en)

    corpus = _judgements(root, "corpus")
    corpus_grades = ensemble.grades_by_pair(corpus, judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    label_path = holdout.holdout_dir(root) / "labels" / f"{holdout.RATER}.jsonl"
    human_es = {lab.pair_id: lab.grade for lab in mv_labels.read(label_path) if not lab.pair_id.startswith("xpr:")}

    return {
        "rule_selection": {"set": "pilot-en", "rater": judge.PILOT_RATER,
                           "compared": len(set(pilot_grades) & set(human3)), "kappas": en, "chosen": chosen},
        "holdout_es": holdout_agreement(corpus_grades, human_es, chosen, seed=SEED),
        "position_flip_rate": {m: position_flip_rate(corpus, m) for m in judge.JUDGES},
        "inter_judge_kappa": inter_judge_kappa(corpus),
        "corpus_pairs_with_full_grades": len(corpus_grades),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    result = validate(root)
    (root / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
