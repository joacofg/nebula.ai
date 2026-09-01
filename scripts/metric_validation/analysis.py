"""Turn a graded pilot corpus into the metric-validation findings.

Three questions, in order of what the rest of Phase 1 depends on:

1. Which nomic-embed-text task prefix best separates the grades? Everything
   downstream embeds under whichever one wins, so it has to be decided here,
   after the labels exist, not before.
2. Does the cosine separate substitutable responses from divergent ones at all,
   and where does it stop separating them?
3. Do the raters agree well enough for their grades to count as ground truth?
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from scripts.metric_validation import rubric
from scripts.metric_validation.corpus import PAIR_KINDS, PREFIX_VARIANTS, Pair
from scripts.metric_validation.stats import (
    BootstrapInterval,
    bootstrap_ci,
    cohens_kappa,
    krippendorff_alpha_ordinal,
    quadratic_weighted_kappa,
    roc_auc,
    spearman,
)

NO_SEPARATION = (
    "no measurable separation: every graded pair fell on one side of the "
    "substitutable cut, so AUC is undefined"
)

Grades = dict[str, str]

# The pairs the metric is actually used on. cross_prompt is planted: separating
# an answer to a different question is trivial, and including it in the sweep
# answers a question nobody asked.
NATURAL_KINDS: tuple[str, ...] = ("local_vs_premium", "premium_vs_premium")


@dataclass(frozen=True)
class PrefixResult:
    prefix: str
    pairs: int
    auc: float | None
    auc_ci: BootstrapInterval | None
    spearman: float | None
    note: str


@dataclass(frozen=True)
class BandRow:
    band: str
    pairs: int
    substitutable: int
    substitutable_rate: float


@dataclass(frozen=True)
class ScaleRow:
    kind: str
    prefix: str
    pairs: int
    minimum: float
    median: float
    maximum: float


@dataclass(frozen=True)
class RaterAgreement:
    left_rater: str
    right_rater: str
    pairs: int
    cohens_kappa_binary: float | None
    quadratic_weighted_kappa: float | None
    kappa_ci: BootstrapInterval | None
    note: str


@dataclass(frozen=True)
class ValidationReport:
    reference_rater: str
    raters: list[str]
    human_raters: list[str]
    human_to_human_pending: bool
    prefix_sweep: list[PrefixResult]
    prefix_sweep_natural: list[PrefixResult]
    chosen_prefix: str | None
    chosen_prefix_basis: str
    chosen_prefix_tied_with: list[str]
    scale_by_kind: list[ScaleRow]
    bands_all: list[BandRow]
    bands_local_vs_premium: list[BandRow]
    agreements: list[RaterAgreement]
    krippendorff_alpha: float | None


def _graded(pairs: list[Pair], grades: Grades) -> list[Pair]:
    return [pair for pair in pairs if pair.pair_id in grades]


def prefix_sweep(
    pairs: list[Pair],
    grades: Grades,
    *,
    seed: int,
    resamples: int = 2000,
    kinds: tuple[str, ...] | None = None,
) -> list[PrefixResult]:
    """Score every task prefix against the reference rater's grades.

    Ranked by AUC of the cosine against the derived binary. Variants that
    cannot be scored keep their place in the output with an explicit note
    rather than a stand-in number.
    """
    scored = [
        pair
        for pair in _graded(pairs, grades)
        if kinds is None or pair.kind in kinds
    ]
    variants = [
        prefix for prefix in PREFIX_VARIANTS if any(prefix in pair.cosine for pair in scored)
    ]

    results: list[PrefixResult] = []
    for prefix in variants:
        usable = [pair for pair in scored if prefix in pair.cosine]
        similarities = [pair.cosine[prefix] for pair in usable]
        binary = [rubric.is_substitutable(grades[pair.pair_id]) for pair in usable]
        ordinal = [rubric.SCALE.index(grades[pair.pair_id]) for pair in usable]

        try:
            auc = roc_auc(similarities, binary)
        except ValueError:
            results.append(
                PrefixResult(
                    prefix=prefix,
                    pairs=len(usable),
                    auc=None,
                    auc_ci=None,
                    spearman=None,
                    note=NO_SEPARATION,
                )
            )
            continue

        interval = bootstrap_ci(
            list(zip(similarities, binary, strict=True)),
            lambda draw: roc_auc([s for s, _ in draw], [b for _, b in draw]),
            seed=seed,
            resamples=resamples,
        )
        try:
            # Negated: the grade scale runs best-to-worst, so a metric that
            # works correlates negatively with the grade index.
            rank_correlation = -spearman(similarities, ordinal)
        except ValueError:
            rank_correlation = None

        results.append(
            PrefixResult(
                prefix=prefix,
                pairs=len(usable),
                auc=auc,
                auc_ci=interval,
                spearman=rank_correlation,
                note="",
            )
        )

    return sorted(results, key=lambda result: (result.auc is None, -(result.auc or 0.0)))


def metric_scale(pairs: list[Pair], *, prefix: str) -> list[ScaleRow]:
    """Where each kind of pair sits on the cosine, at one prefix.

    The noise floor lives here. cos(premium_a, premium_b) is the ceiling the
    metric can reach when both answers are good, so a local-vs-premium median
    means nothing until it is read against it: if the two medians coincide, the
    cosine is not resolving quality in that range, it is saturating.
    """
    rows: list[ScaleRow] = []
    for kind in PAIR_KINDS:
        scores = [pair.cosine[prefix] for pair in pairs if pair.kind == kind and prefix in pair.cosine]
        if not scores:
            continue
        rows.append(
            ScaleRow(
                kind=kind,
                prefix=prefix,
                pairs=len(scores),
                minimum=min(scores),
                median=median(scores),
                maximum=max(scores),
            )
        )
    return rows


def separation_by_band(
    pairs: list[Pair],
    grades: Grades,
    *,
    prefix: str,
    kinds: tuple[str, ...] | None = None,
) -> list[BandRow]:
    """How often graded pairs in each similarity band were judged substitutable."""
    from scripts.metric_validation.corpus import band_for

    selected = [
        pair
        for pair in _graded(pairs, grades)
        if prefix in pair.cosine and (kinds is None or pair.kind in kinds)
    ]

    buckets: dict[str, list[bool]] = {}
    for pair in selected:
        band = band_for(pair.cosine[prefix])
        buckets.setdefault(band, []).append(rubric.is_substitutable(grades[pair.pair_id]))

    return [
        BandRow(
            band=band,
            pairs=len(verdicts),
            substitutable=sum(verdicts),
            substitutable_rate=sum(verdicts) / len(verdicts),
        )
        for band, verdicts in sorted(buckets.items())
    ]


def pairwise_agreement(
    grades_by_rater: dict[str, Grades],
    *,
    seed: int,
    resamples: int = 2000,
) -> list[RaterAgreement]:
    """Agreement for every rater pair, over the pairs both of them graded."""
    raters = sorted(grades_by_rater)
    agreements: list[RaterAgreement] = []

    for position, left_rater in enumerate(raters):
        for right_rater in raters[position + 1 :]:
            left_grades = grades_by_rater[left_rater]
            right_grades = grades_by_rater[right_rater]
            shared = sorted(set(left_grades) & set(right_grades))
            if not shared:
                agreements.append(
                    RaterAgreement(
                        left_rater=left_rater,
                        right_rater=right_rater,
                        pairs=0,
                        cohens_kappa_binary=None,
                        quadratic_weighted_kappa=None,
                        kappa_ci=None,
                        note="no pair was graded by both raters",
                    )
                )
                continue

            left_ordinal = [left_grades[pair_id] for pair_id in shared]
            right_ordinal = [right_grades[pair_id] for pair_id in shared]
            left_binary = [rubric.is_substitutable(grade) for grade in left_ordinal]
            right_binary = [rubric.is_substitutable(grade) for grade in right_ordinal]

            note = ""
            try:
                binary_kappa = cohens_kappa(left_binary, right_binary)
            except ValueError:
                binary_kappa = None
                note = "binary kappa undefined: both raters used a single category"

            try:
                weighted = quadratic_weighted_kappa(
                    left_ordinal, right_ordinal, categories=rubric.SCALE
                )
            except ValueError:
                weighted = None
                note = note or "weighted kappa undefined: no expected disagreement"

            interval = None
            if weighted is not None:
                interval = bootstrap_ci(
                    list(zip(left_ordinal, right_ordinal, strict=True)),
                    lambda draw: quadratic_weighted_kappa(
                        [a for a, _ in draw], [b for _, b in draw], categories=rubric.SCALE
                    ),
                    seed=seed,
                    resamples=resamples,
                )

            agreements.append(
                RaterAgreement(
                    left_rater=left_rater,
                    right_rater=right_rater,
                    pairs=len(shared),
                    cohens_kappa_binary=binary_kappa,
                    quadratic_weighted_kappa=weighted,
                    kappa_ci=interval,
                    note=note,
                )
            )

    return agreements


def build_report(
    pairs: list[Pair],
    grades_by_rater: dict[str, Grades],
    *,
    reference_rater: str,
    seed: int,
    resamples: int = 2000,
) -> ValidationReport:
    if reference_rater not in grades_by_rater:
        raise ValueError(f"Reference rater {reference_rater!r} has no grades.")

    reference = grades_by_rater[reference_rater]
    sweep = prefix_sweep(pairs, reference, seed=seed, resamples=resamples)
    natural = prefix_sweep(
        pairs, reference, seed=seed, resamples=resamples, kinds=NATURAL_KINDS
    )

    # Chosen on the natural pairs. Choosing on all pairs would let the planted
    # negatives — which every prefix separates easily — decide a question about
    # resolution among real answers.
    scorable = [result for result in natural if result.auc is not None]
    basis = ", ".join(NATURAL_KINDS)
    if not scorable:
        scorable = [result for result in sweep if result.auc is not None]
        basis = "all pairs (natural pairs were unscorable)"
    chosen = scorable[0].prefix if scorable else None
    # Two prefixes that separate the grades equally well are a tie, not a
    # ranking. The winner is the first in declared variant order, and the
    # report has to say so rather than let the order pass for a finding.
    tied_with = (
        [result.prefix for result in scorable[1:] if result.auc == scorable[0].auc]
        if scorable
        else []
    )

    # An LLM standing in for the missing second human is an auxiliary rater. It
    # is recorded as one so the report cannot be read as satisfying the
    # two-human requirement.
    human_raters = sorted(rater for rater in grades_by_rater if not rater.startswith("llm-"))

    alpha = None
    if len(grades_by_rater) > 1:
        units = [
            [grades[pair.pair_id] for grades in grades_by_rater.values() if pair.pair_id in grades]
            for pair in pairs
        ]
        if any(len(unit) > 1 for unit in units):
            try:
                alpha = krippendorff_alpha_ordinal(units, categories=rubric.SCALE)
            except ValueError:
                alpha = None

    return ValidationReport(
        reference_rater=reference_rater,
        raters=sorted(grades_by_rater),
        human_raters=human_raters,
        human_to_human_pending=len(human_raters) < 2,
        prefix_sweep=sweep,
        prefix_sweep_natural=natural,
        chosen_prefix=chosen,
        chosen_prefix_basis=basis,
        chosen_prefix_tied_with=tied_with,
        scale_by_kind=metric_scale(pairs, prefix=chosen) if chosen else [],
        bands_all=separation_by_band(pairs, reference, prefix=chosen) if chosen else [],
        bands_local_vs_premium=(
            separation_by_band(pairs, reference, prefix=chosen, kinds=("local_vs_premium",))
            if chosen
            else []
        ),
        agreements=pairwise_agreement(grades_by_rater, seed=seed, resamples=resamples),
        krippendorff_alpha=alpha,
    )
