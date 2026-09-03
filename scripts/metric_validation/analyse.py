"""Turn the graded pairs into the metric-validation report.

    python -m scripts.metric_validation.analyse --reference-rater human-1

Reads every ``labels/<rater>.jsonl`` in the study directory, sweeps the task
prefixes against the reference rater's grades, measures separation by
similarity band, and reports agreement between every pair of raters.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.metric_validation import analysis, corpus, labels, raters, report

DEFAULT_ROOT = Path("benchmarks/metric-validation")


def read_all_grades(label_dir: Path) -> dict[str, dict[str, str]]:
    grades: dict[str, dict[str, str]] = {}
    for path in sorted(label_dir.glob("*.jsonl")):
        rater_grades = {label.pair_id: label.grade for label in labels.read(path)}
        if rater_grades:
            grades[path.stem] = rater_grades
    return grades


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--reference-rater", default="human-1")
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()

    root: Path = args.root
    pairs = corpus.read_pairs(root / "pairs.jsonl")
    grades = read_all_grades(root / "labels")
    if not grades:
        raise SystemExit(f"No labels found under {root / 'labels'}. Run the labeller first.")

    built = analysis.build_report(
        pairs,
        grades,
        reference_rater=args.reference_rater,
        roster=raters.load_roster(root / "raters.json"),
        seed=args.seed,
        resamples=args.resamples,
    )

    (root / "report.md").write_text(report.render_markdown(built), encoding="utf-8")
    (root / "report.json").write_text(
        json.dumps(report.to_payload(built), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print(f"report → {root / 'report.md'}")
    print(f"payload → {root / 'report.json'}")
    print(f"chosen prefix: {built.chosen_prefix}")
    if built.human_to_human_pending:
        print("human-to-human agreement: PENDING (one human rater)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
