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

from dataclasses import dataclass, replace

from scripts.metric_validation import blinding, corpus, labels, rubric

DEFAULT_PAIRS = Path("benchmarks/metric-validation/pairs.jsonl")
DEFAULT_LABEL_DIR = Path("benchmarks/metric-validation/labels")

_RULE = "─" * 78


CALIBRATION_NEGATIVES = 2


@dataclass(frozen=True)
class CalibrationItem:
    pair: corpus.Pair
    expected_substitutable: bool
    kind: str
    why: str


def calibration_items(
    pairs: list[corpus.Pair], *, rater_id: str
) -> list[CalibrationItem]:
    """Items whose correct verdict is fixed by construction, not by judgement.

    A rater who forms the wrong model of the task in the first few pairs keeps
    it for the whole session, and nothing in a blind queue can tell them. This
    round exists to catch that before any grade is recorded.

    Both directions are represented. A calibration round of negatives alone
    would simply teach the rater to answer "divergent".
    """
    ordered = blinding.presentation_order(
        [pair.pair_id for pair in pairs], rater_id=rater_id
    )
    by_id = {pair.pair_id: pair for pair in pairs}

    items: list[CalibrationItem] = []
    for pair_id in ordered:
        pair = by_id[pair_id]
        if pair.kind == "cross_prompt" and len(items) < CALIBRATION_NEGATIVES:
            items.append(
                CalibrationItem(
                    pair=pair,
                    expected_substitutable=False,
                    kind="off_topic",
                    why=(
                        "One of these answers a different question. It cannot stand "
                        "in for the other, however well written it is — the question "
                        "is not which response is good, it is whether one could "
                        "replace the other for the person who asked."
                    ),
                )
            )
        if len(items) == CALIBRATION_NEGATIVES:
            break

    # Nothing in the corpus is objectively substitutable: two premium models
    # genuinely differ sometimes. A response against itself is the only positive
    # that is not a matter of opinion.
    for pair_id in ordered:
        pair = by_id[pair_id]
        if pair.kind == "local_vs_premium":
            items.append(
                CalibrationItem(
                    pair=replace(
                        pair,
                        pair_id=f"cal:{pair.pair_id}",
                        right=replace(pair.right, text=pair.left.text),
                    ),
                    expected_substitutable=True,
                    kind="identical",
                    why="These two responses are identical.",
                )
            )
            break

    # The axis a topic heuristic cannot pass. Off-topic items are a different
    # subject, so "same topic?" rejects them correctly and the shortcut
    # survives the round. This one is the same subject, answering the same
    # question, and still cannot stand in: it stops partway.
    for pair_id in ordered:
        pair = by_id[pair_id]
        if pair.kind != "local_vs_premium":
            continue
        full = pair.left.text
        truncated = full[: max(1, len(full) // 5)]
        if len(truncated) >= len(full):
            continue
        items.append(
            CalibrationItem(
                pair=replace(
                    pair,
                    pair_id=f"cal-trunc:{pair.pair_id}",
                    right=replace(pair.right, text=truncated),
                ),
                expected_substitutable=False,
                kind="truncated",
                why=(
                    "Same subject, same question, but one side stops partway "
                    "through. Sharing a topic is not the test — the test is "
                    "whether the person who asked would have been just as well "
                    "served by either one."
                ),
            )
        )
        break

    return items


def calibration_failures(
    items: list[CalibrationItem], answers: dict[str, str]
) -> list[CalibrationItem]:
    """Which calibration items the rater got wrong, on the binary verdict."""
    return [
        item
        for item in items
        if item.pair.pair_id in answers
        and rubric.is_substitutable(answers[item.pair.pair_id])
        != item.expected_substitutable
    ]


def scored_queue(
    pairs: list[corpus.Pair],
    label_path: Path,
    *,
    rater_id: str,
    calibration: list[CalibrationItem],
) -> list[str]:
    """The pairs this rater still has to grade blind.

    Calibration pairs are dropped: a pair shown with its answer attached cannot
    also be one of the rater's blind grades.
    """
    shown = {
        item.pair.pair_id.removeprefix("cal:").removeprefix("cal-trunc:")
        for item in calibration
    }
    remaining = labels.remaining(
        [pair.pair_id for pair in pairs], label_path, rater_id=rater_id
    )
    return [pair_id for pair_id in remaining if pair_id not in shown]


NATURAL_KINDS: tuple[str, ...] = ("local_vs_premium", "premium_vs_premium")
ORDINAL_SPLIT = 2


def informative_pairs(
    pairs: list[corpus.Pair],
    judge_grades: dict[str, dict[str, str]],
    *,
    kinds: tuple[str, ...] = NATURAL_KINDS,
) -> list[str]:
    """Pairs where the judges read the same evidence differently.

    A human's attention is the scarce resource in this study, and spending it
    where two judges already agree buys nothing. These are the pairs where a
    third reading breaks a tie: the binary verdicts differ, or the ordinal
    grades sit two or more steps apart.

    Planted pairs are excluded — they are not traffic, and the judges do not
    disagree about them anyway.
    """
    if len(judge_grades) < 2:
        raise ValueError("Comparing judges needs at least two of them.")

    candidates = [pair.pair_id for pair in pairs if pair.kind in kinds]
    informative: list[str] = []
    for pair_id in candidates:
        graded = [g[pair_id] for g in judge_grades.values() if pair_id in g]
        if len(graded) < 2:
            continue
        binaries = {rubric.is_substitutable(grade) for grade in graded}
        positions = [rubric.SCALE.index(grade) for grade in graded]
        if len(binaries) > 1 or max(positions) - min(positions) >= ORDINAL_SPLIT:
            informative.append(pair_id)
    return informative


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


def run_calibration(pairs: list[corpus.Pair], *, rater_id: str) -> bool:
    """Walk the rater through items with known answers. Returns True to proceed.

    Nothing here is recorded. The point is to surface a misread of the task
    while it still costs three pairs instead of a whole session.
    """
    items = calibration_items(pairs, rater_id=rater_id)
    if not items:
        return True

    print(_RULE)
    print(f"Calibration — {len(items)} pairs with known answers. Nothing is recorded.")
    print(_RULE)

    answers: dict[str, str] = {}
    for position, item in enumerate(items, start=1):
        payload = blinding.blinded_payload(item.pair, rater_id=rater_id)
        print(render_pair(payload, position=position, total=len(items)))
        while True:
            try:
                grade = parse_response(input("grade> "))
            except ValueError as error:
                print(f"  {error}")
                continue
            except (EOFError, KeyboardInterrupt):
                print("\nStopped.")
                return False
            break
        if grade is not None:
            answers[item.pair.pair_id] = grade

    failures = calibration_failures(items, answers)
    if not failures:
        print("\nCalibration passed. Starting the real session.\n")
        return True

    print(f"\n{len(failures)} of {len(items)} calibration items were graded the other way:")
    for item in failures:
        expected = "substitutable (1 or 2)" if item.expected_substitutable else "not substitutable (3 or 4)"
        print(f"  - {item.pair.pair_id}: expected {expected}. {item.why}")
    print("\nRe-read the scale above and run the session again.")
    return False


def run_session(
    *,
    rater_id: str,
    pairs_path: Path,
    label_dir: Path,
    only_informative: bool = False,
) -> int:
    pairs = corpus.read_pairs(pairs_path)
    by_id = {pair.pair_id: pair for pair in pairs}
    label_path = label_dir / f"{rater_id}.jsonl"

    calibration = calibration_items(pairs, rater_id=rater_id)
    if not labels.read(label_path) and not run_calibration(pairs, rater_id=rater_id):
        return 1

    queue = scored_queue(pairs, label_path, rater_id=rater_id, calibration=calibration)
    if only_informative:
        judge_grades = {
            path.stem: {label.pair_id: label.grade for label in labels.read(path)}
            for path in sorted(label_dir.glob("llm-*.jsonl"))
        }
        wanted = set(informative_pairs(pairs, judge_grades))
        queue = [pair_id for pair_id in queue if pair_id in wanted]
        print(
            f"Informative subset: {len(wanted)} pairs the judges read differently.\n"
        )
    if not queue:
        print(f"Nothing left to label for {rater_id}.")
        return 0

    scored_total = len(pairs) - len({i.pair.pair_id.removeprefix("cal:") for i in calibration})
    done = scored_total - len(queue)
    print(f"{len(queue)} pairs left for {rater_id} ({done} already graded). Ctrl-C to stop.\n")

    for offset, pair_id in enumerate(queue, start=1):
        payload = blinding.blinded_payload(by_id[pair_id], rater_id=rater_id)
        print(render_pair(payload, position=done + offset, total=scored_total))
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
    parser.add_argument(
        "--only-informative",
        action="store_true",
        help="grade only the pairs the auxiliary judges disagree about",
    )
    args = parser.parse_args()
    return run_session(
        rater_id=args.rater,
        pairs_path=args.pairs,
        label_dir=args.labels,
        only_informative=args.only_informative,
    )


if __name__ == "__main__":
    raise SystemExit(main())
