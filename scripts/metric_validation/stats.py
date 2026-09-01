"""Agreement and separation statistics for the metric-validation study.

Pure stdlib on purpose. The gateway ships ten runtime dependencies and none of
them are numeric; pulling numpy/scipy in so a one-off study can call two
functions would be a poor trade. Every estimator here is short enough to audit
against the definition it implements, which is what a thesis reviewer needs.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass


def cohens_kappa(rater_a: Sequence[object], rater_b: Sequence[object]) -> float:
    """Cohen's kappa for two raters over the same items."""
    if len(rater_a) != len(rater_b):
        raise ValueError("Raters must label the same number of items.")
    if not rater_a:
        raise ValueError("Cohen's kappa needs at least one labelled item.")

    total = len(rater_a)
    observed = sum(1 for a, b in zip(rater_a, rater_b, strict=True) if a == b) / total

    categories = set(rater_a) | set(rater_b)
    expected = sum(
        (list(rater_a).count(category) / total) * (list(rater_b).count(category) / total)
        for category in categories
    )

    if expected == 1.0:
        raise ValueError("Chance agreement is 1.0; kappa is undefined for a single category.")

    return (observed - expected) / (1.0 - expected)


def quadratic_weighted_kappa(
    rater_a: Sequence[int],
    rater_b: Sequence[int],
    *,
    categories: Sequence[int],
) -> float:
    """Cohen's kappa with quadratic disagreement weights over an ordinal scale.

    ``categories`` is the declared scale, not the observed one. A rubric that
    spans 1-4 keeps that width even in a sample where nobody used a 4;
    inferring the scale from the data would silently rescale the weights.
    """
    if len(rater_a) != len(rater_b):
        raise ValueError("Raters must label the same number of items.")
    if not rater_a:
        raise ValueError("Weighted kappa needs at least one labelled item.")
    if len(categories) < 2:
        raise ValueError("An ordinal scale needs at least two categories.")

    unknown = (set(rater_a) | set(rater_b)) - set(categories)
    if unknown:
        raise ValueError(f"Labels outside the declared scale: {sorted(unknown)}")

    total = len(rater_a)
    width = (len(categories) - 1) ** 2
    index = {category: position for position, category in enumerate(categories)}

    observed = sum(
        (index[a] - index[b]) ** 2 for a, b in zip(rater_a, rater_b, strict=True)
    ) / width

    counts_a = {category: list(rater_a).count(category) for category in categories}
    counts_b = {category: list(rater_b).count(category) for category in categories}
    expected = sum(
        (index[c] - index[k]) ** 2 * counts_a[c] * counts_b[k] / total
        for c in categories
        for k in categories
    ) / width

    if expected == 0.0:
        raise ValueError("Expected disagreement is zero; weighted kappa is undefined.")

    return 1.0 - observed / expected


def _ordinal_delta_squared(
    left: int,
    right: int,
    counts: Sequence[int],
) -> float:
    """Krippendorff's ordinal difference between two scale positions."""
    if left == right:
        return 0.0
    low, high = (left, right) if left < right else (right, left)
    span = sum(counts[low : high + 1]) - (counts[low] + counts[high]) / 2.0
    return span**2


def krippendorff_alpha_ordinal(
    units: Sequence[Sequence[object]],
    *,
    categories: Sequence[object],
) -> float:
    """Krippendorff's alpha with the ordinal difference function.

    ``units`` is one sequence of labels per item, so a unit may carry two, three
    or one rating. Units rated once are dropped before anything is counted:
    they say nothing about agreement, and Krippendorff excludes them from the
    marginals that define expected disagreement too.
    """
    index = {category: position for position, category in enumerate(categories)}
    scored = [
        [index[label] for label in unit]
        for unit in units
        if len(unit) > 1
    ]
    if not scored:
        raise ValueError("Krippendorff's alpha needs at least one unit rated twice.")

    counts = [0] * len(categories)
    for unit in scored:
        for position in unit:
            counts[position] += 1
    total = sum(counts)
    if total < 2:
        raise ValueError("Krippendorff's alpha needs at least two ratings.")

    observed = 0.0
    for unit in scored:
        pairs = len(unit) - 1
        for left in unit:
            for right in unit:
                observed += _ordinal_delta_squared(left, right, counts) / pairs
    observed /= total

    expected = 0.0
    for left in range(len(categories)):
        for right in range(len(categories)):
            expected += counts[left] * counts[right] * _ordinal_delta_squared(
                left, right, counts
            )
    expected /= total * (total - 1)

    if expected == 0.0:
        raise ValueError("Expected disagreement is zero; alpha is undefined.")

    return 1.0 - observed / expected


def roc_auc(scores: Sequence[float], labels: Sequence[bool]) -> float:
    """Area under the ROC curve, as the rank-order interpretation.

    This is the probability that a randomly chosen positive outscores a
    randomly chosen negative, with ties worth half a pair. It is the criterion
    the prefix sweep is decided on, so it has to treat a metric that cannot
    separate the classes as 0.5 rather than as an artefact of comparison order.
    """
    if len(scores) != len(labels):
        raise ValueError("Scores and labels must be the same length.")

    positives = [score for score, label in zip(scores, labels, strict=True) if label]
    negatives = [score for score, label in zip(scores, labels, strict=True) if not label]
    if not positives or not negatives:
        raise ValueError("ROC AUC needs both classes present in the sample.")

    ordered = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return ordered / (len(positives) * len(negatives))


@dataclass(frozen=True)
class BootstrapInterval:
    point: float
    low: float
    high: float
    confidence: float
    resamples_used: int
    resamples_skipped: int


def bootstrap_ci[T](
    sample: Sequence[T],
    statistic: Callable[[list[T]], float],
    *,
    seed: int,
    resamples: int = 2000,
    confidence: float = 0.95,
) -> BootstrapInterval:
    """Percentile bootstrap interval for ``statistic`` over ``sample``.

    Resamples on which the statistic is undefined are dropped and counted
    rather than swallowed. Kappa and AUC both raise when a draw loses a class,
    and an interval built on a fraction of the requested resamples is a
    materially weaker claim than one built on all of them.
    """
    if not sample:
        raise ValueError("Bootstrap needs a non-empty sample.")
    if resamples < 1:
        raise ValueError("Bootstrap needs at least one resample.")
    if not 0.0 < confidence < 1.0:
        raise ValueError("Confidence must lie strictly between 0 and 1.")

    rng = random.Random(seed)
    size = len(sample)
    estimates: list[float] = []
    skipped = 0
    for _ in range(resamples):
        draw = [sample[rng.randrange(size)] for _ in range(size)]
        try:
            estimates.append(statistic(draw))
        except (ValueError, ZeroDivisionError):
            skipped += 1

    if not estimates:
        raise ValueError("The statistic was undefined on every resample.")

    estimates.sort()
    tail = (1.0 - confidence) / 2.0
    return BootstrapInterval(
        point=statistic(list(sample)),
        low=_percentile(estimates, tail),
        high=_percentile(estimates, 1.0 - tail),
        confidence=confidence,
        resamples_used=len(estimates),
        resamples_skipped=skipped,
    )


def _percentile(ordered: Sequence[float], fraction: float) -> float:
    """Linear-interpolated percentile of an already-sorted sequence."""
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _midranks(values: Sequence[float]) -> list[float]:
    """Ranks with tied values sharing the average of the ranks they span."""
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        shared = (position + end) / 2.0 + 1.0
        for index in order[position : end + 1]:
            ranks[index] = shared
        position = end + 1
    return ranks


def spearman(left: Sequence[float], right: Sequence[float]) -> float:
    """Spearman rank correlation, with midranks for ties.

    Ordinal grades tie heavily — a four-point scale over a hundred-odd pairs is
    four large tie groups — so tie handling is not an edge case here.
    """
    if len(left) != len(right):
        raise ValueError("Both sequences must be the same length.")
    if len(left) < 2:
        raise ValueError("Rank correlation needs at least two observations.")

    ranks_left = _midranks(left)
    ranks_right = _midranks(right)
    mean_left = sum(ranks_left) / len(ranks_left)
    mean_right = sum(ranks_right) / len(ranks_right)

    covariance = sum(
        (a - mean_left) * (b - mean_right)
        for a, b in zip(ranks_left, ranks_right, strict=True)
    )
    spread_left = sum((a - mean_left) ** 2 for a in ranks_left)
    spread_right = sum((b - mean_right) ** 2 for b in ranks_right)
    if spread_left == 0.0 or spread_right == 0.0:
        raise ValueError("Rank correlation is undefined: one side has no variance.")

    return covariance / (spread_left * spread_right) ** 0.5
