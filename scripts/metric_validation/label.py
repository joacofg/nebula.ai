"""Blind labelling session for one rater.

Run it once per rater. The session is resumable: it presents only the pairs
this rater has not graded, in this rater's own presentation order, so position
in the queue never correlates with similarity band.

    python -m scripts.metric_validation.label --rater human-1
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from scripts.metric_validation import blinding, corpus, labels, rubric

DEFAULT_PAIRS = Path("benchmarks/metric-validation/pairs.jsonl")
DEFAULT_LABEL_DIR = Path("benchmarks/metric-validation/labels")

_RULE = "─" * 78


def parse_response(raw: str) -> str | None:
    """Map a keystroke to a grade. ``None`` means skip, and skip means skip.

    A pair the rater could not call has to stay unlabelled and resumable.
    Coercing it into the nearest grade would put a guess into the ground truth.
    """
    cleaned = raw.strip().lower()
    if cleaned in {"s", "skip"}:
        return None
    if cleaned.isdigit() and 1 <= int(cleaned) <= len(rubric.SCALE):
        return rubric.SCALE[int(cleaned) - 1]
    if cleaned in rubric.SCALE:
        return cleaned
    raise ValueError(
        f"Unrecognised response {raw!r}. Enter 1-{len(rubric.SCALE)}, a grade name, or 's'."
    )


def render_pair(payload: dict[str, str], *, position: int, total: int) -> str:
    legend = "\n".join(
        f"  {index}. {grade:<12} {rubric.DESCRIPTIONS[grade]}"
        for index, grade in enumerate(rubric.SCALE, start=1)
    )

    def wrap(text: str) -> str:
        return textwrap.fill(text, width=78)

    return "\n".join(
        [
            _RULE,
            f"Pair {position}/{total}",
            _RULE,
            "PROMPT",
            wrap(payload["prompt"]),
            "",
            "RESPONSE A",
            wrap(payload["response_a"]),
            "",
            "RESPONSE B",
            wrap(payload["response_b"]),
            "",
            _RULE,
            rubric.QUESTION,
            legend,
            "  s. skip (leave unlabelled)",
            "",
        ]
    )


def run_session(*, rater_id: str, pairs_path: Path, label_dir: Path) -> int:
    pairs = {pair.pair_id: pair for pair in corpus.read_pairs(pairs_path)}
    label_path = label_dir / f"{rater_id}.jsonl"
    queue = labels.remaining(list(pairs), label_path, rater_id=rater_id)

    if not queue:
        print(f"Nothing left to label for {rater_id}.")
        return 0

    done = len(pairs) - len(queue)
    print(f"{len(queue)} pairs left for {rater_id} ({done} already graded). Ctrl-C to stop.\n")

    for offset, pair_id in enumerate(queue, start=1):
        payload = blinding.blinded_payload(pairs[pair_id], rater_id=rater_id)
        print(render_pair(payload, position=done + offset, total=len(pairs)))
        while True:
            try:
                grade = parse_response(input("grade> "))
            except ValueError as error:
                print(f"  {error}")
                continue
            except (EOFError, KeyboardInterrupt):
                print("\nStopped. Progress is saved.")
                return 0
            break
        if grade is None:
            continue
        labels.append(labels.Label(pair_id=pair_id, rater_id=rater_id, grade=grade), label_path)

    print("Done.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rater", required=True, help="rater id, e.g. human-1")
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABEL_DIR)
    args = parser.parse_args()
    return run_session(rater_id=args.rater, pairs_path=args.pairs, label_dir=args.labels)


if __name__ == "__main__":
    raise SystemExit(main())
