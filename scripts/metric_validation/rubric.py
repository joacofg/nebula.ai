"""The labelling rubric for the metric-validation study.

The scale is ordinal and the question put to the rater is symmetric, so the
grade does not depend on which response is shown first. That is what lets the
protocol randomise the sides without having to unblind anything afterwards.
"""

from __future__ import annotations

SCALE: tuple[str, ...] = ("equivalent", "minor_loss", "partial", "divergent")

# Grades at or below this position count as "the reader would have been served
# just as well". Everything past it counts as a substantive difference.
SUBSTITUTABLE_THROUGH = "minor_loss"

QUESTION = (
    "Could either response have replaced the other for the person who asked "
    "this question, without them being worse off?"
)

DESCRIPTIONS: dict[str, str] = {
    "equivalent": (
        "Same substance. Wording, ordering or length may differ, but a reader "
        "would take away the same answer from either one."
    ),
    "minor_loss": (
        "Same substance, one side slightly poorer: an omitted caveat, a thinner "
        "example, a clumsier structure. A reader would still be served."
    ),
    "partial": (
        "Overlapping but materially different: one side answers only part of "
        "the question, or adds a claim the other does not support."
    ),
    "divergent": (
        "Different answers, or one side is wrong, off-topic, or unusable. A "
        "reader would notice the swap immediately."
    ),
}


def is_substitutable(grade: str) -> bool:
    """The binary the routing decision actually cares about."""
    if grade not in SCALE:
        raise ValueError(f"Grade {grade!r} is not on the rubric.")
    return SCALE.index(grade) <= SCALE.index(SUBSTITUTABLE_THROUGH)
