"""The pre-registered rules that turn four judge grades into one verdict.

See benchmarks/ground-truth/v1/preregistration.md. Changing a rule here after
the corpus was judged invalidates the pre-registration.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from scripts.ground_truth import records
from scripts.metric_validation import rubric

RULES: tuple[str, ...] = ("R1_unanimous", "R2_majority", "R3_ordinal_mean")  # most conservative first
GRADES_PER_PAIR = 4
_CUT = rubric.SCALE.index(rubric.SUBSTITUTABLE_THROUGH)


def substitutable(rule: str, grades: Sequence[str]) -> bool:
    if len(grades) != GRADES_PER_PAIR:
        raise ValueError(f"A verdict needs {GRADES_PER_PAIR} grades, got {len(grades)}.")
    positions = [rubric.SCALE.index(grade) for grade in grades]
    passing = sum(1 for p in positions if p <= _CUT)
    if rule == "R1_unanimous":
        return passing == GRADES_PER_PAIR
    if rule == "R2_majority":
        return passing >= 3
    if rule == "R3_ordinal_mean":
        return sum(positions) / len(positions) <= 1.5
    raise ValueError(f"Unknown rule {rule!r}.")


def grades_by_pair(
    judgements: Iterable[records.Judgement], *, judges: Sequence[str], orientations: Sequence[str]
) -> dict[str, list[str]]:
    """Pairs with every (judge, orientation) graded, grades in a fixed order."""
    latest = records.latest(judgements, key=lambda r: (r.pair_id, r.judge, r.orientation))
    out: dict[str, list[str]] = {}
    for pair_id in sorted({key[0] for key in latest}):
        grades = []
        for judge in judges:
            for orientation in orientations:
                row = latest.get((pair_id, judge, orientation))
                if row is None or row.status != "ok" or row.grade is None:
                    break
                grades.append(row.grade)
        if len(grades) == len(judges) * len(orientations):
            out[pair_id] = grades
    return out


def choose_rule(kappas: dict[str, float | None]) -> str:
    defined = {rule: k for rule, k in kappas.items() if k is not None}
    if not defined:
        raise ValueError("Kappa is undefined for every rule; no rule can be chosen.")
    best = max(defined.values())
    return next(rule for rule in RULES if rule in defined and abs(defined[rule] - best) < 1e-12)
