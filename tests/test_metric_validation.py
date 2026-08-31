from __future__ import annotations

import pytest

from collections import Counter

from scripts.metric_validation import (
    analysis,
    blinding,
    capture,
    corpus,
    labels,
    rubric,
    stats,
)


def test_cohens_kappa_matches_hand_worked_confusion_matrix() -> None:
    # 50 items, binary. Both-yes 20, both-no 15, disagreements 5 and 10.
    # Po = 35/50 = 0.70; Pe = 0.5*0.6 + 0.5*0.4 = 0.50; kappa = 0.20/0.50 = 0.40
    rater_a = ["yes"] * 20 + ["yes"] * 5 + ["no"] * 10 + ["no"] * 15
    rater_b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15

    assert stats.cohens_kappa(rater_a, rater_b) == pytest.approx(0.40)


def test_quadratic_weighted_kappa_matches_hand_worked_ordinal_example() -> None:
    # Ordinal 1-4 over 10 items. Observed squared deviations sum to 3 and the
    # expected weighted disagreement to 25.4/9, so kappa = 1 - 3/25.4. The
    # quadratic normaliser cancels in the ratio, which is why the scale width
    # never appears in the expected value.
    rater_a = [1, 1, 2, 2, 3, 3, 4, 4, 1, 2]
    rater_b = [1, 2, 2, 3, 3, 4, 4, 4, 1, 2]

    kappa = stats.quadratic_weighted_kappa(rater_a, rater_b, categories=(1, 2, 3, 4))

    assert kappa == pytest.approx(1 - 3 / 25.4)


RUBRIC_ORDER = ("equivalent", "minor_loss", "partial", "divergent")


def test_quadratic_weighted_kappa_takes_its_ordinal_order_from_the_declared_scale() -> None:
    # The rubric labels are strings whose ordinal order is not their alphabetical
    # order. Ranking them by anything but the declared sequence would put
    # "divergent" adjacent to "equivalent" and shrink a maximal disagreement to
    # a minimal one.
    numeric_a = [1, 1, 2, 2, 3, 3, 4, 4, 1, 2]
    numeric_b = [1, 2, 2, 3, 3, 4, 4, 4, 1, 2]
    labelled_a = [RUBRIC_ORDER[value - 1] for value in numeric_a]
    labelled_b = [RUBRIC_ORDER[value - 1] for value in numeric_b]

    declared = stats.quadratic_weighted_kappa(labelled_a, labelled_b, categories=RUBRIC_ORDER)
    alphabetical = stats.quadratic_weighted_kappa(
        labelled_a, labelled_b, categories=tuple(sorted(RUBRIC_ORDER))
    )

    assert declared == pytest.approx(
        stats.quadratic_weighted_kappa(numeric_a, numeric_b, categories=(1, 2, 3, 4))
    )
    assert declared != pytest.approx(alphabetical)


def test_quadratic_weighted_kappa_rejects_labels_outside_the_declared_scale() -> None:
    with pytest.raises(ValueError, match="outside the declared scale"):
        stats.quadratic_weighted_kappa([1, 2], [1, 9], categories=(1, 2, 3, 4))


def test_krippendorff_alpha_ordinal_matches_hand_worked_example() -> None:
    # Four units, two raters each, scale 1-4. Value counts are 2/1/3/2 over
    # eight ratings. Observed ordinal disagreement is 1.0, expected is 624/56,
    # so alpha = 1 - 56/624.
    units = [[1, 1], [2, 3], [3, 3], [4, 4]]

    alpha = stats.krippendorff_alpha_ordinal(units, categories=(1, 2, 3, 4))

    assert alpha == pytest.approx(1 - 56 / 624)


def test_krippendorff_alpha_ordinal_ignores_units_rated_only_once() -> None:
    # A pair nobody double-rated carries no information about agreement, and
    # its value must not leak into the expected-disagreement marginals either.
    rated_twice = [[1, 1], [2, 3], [3, 3], [4, 4]]

    with_singleton = stats.krippendorff_alpha_ordinal(
        [*rated_twice, [4]], categories=(1, 2, 3, 4)
    )

    assert with_singleton == pytest.approx(
        stats.krippendorff_alpha_ordinal(rated_twice, categories=(1, 2, 3, 4))
    )


def test_roc_auc_counts_correctly_ordered_positive_negative_pairs() -> None:
    # Positives 0.9/0.8/0.4 against negatives 0.6/0.3: five of the six pairs
    # are ordered correctly.
    scores = [0.9, 0.8, 0.4, 0.6, 0.3]
    labels = [True, True, True, False, False]

    assert stats.roc_auc(scores, labels) == pytest.approx(5 / 6)


def test_roc_auc_scores_ties_as_half_a_pair() -> None:
    # A metric that cannot separate the classes at all must land on 0.5, not on
    # 1.0 or 0.0 depending on which way the comparison happens to be written.
    assert stats.roc_auc([0.5, 0.5], [True, False]) == pytest.approx(0.5)


def test_roc_auc_refuses_a_single_class_sample() -> None:
    with pytest.raises(ValueError, match="both classes"):
        stats.roc_auc([0.9, 0.1], [True, True])


def test_bootstrap_ci_is_reproducible_from_its_seed() -> None:
    sample = [0.1, 0.4, 0.4, 0.7, 0.9, 0.2, 0.6, 0.5]

    first = stats.bootstrap_ci(sample, _mean, seed=1234, resamples=200)
    second = stats.bootstrap_ci(sample, _mean, seed=1234, resamples=200)

    assert (first.low, first.high) == (second.low, second.high)


def test_bootstrap_ci_brackets_the_point_estimate() -> None:
    sample = [0.1, 0.4, 0.4, 0.7, 0.9, 0.2, 0.6, 0.5]

    interval = stats.bootstrap_ci(sample, _mean, seed=7, resamples=500)

    assert interval.point == pytest.approx(_mean(sample))
    assert interval.low <= interval.point <= interval.high


def test_bootstrap_ci_collapses_on_a_constant_sample() -> None:
    interval = stats.bootstrap_ci([0.3] * 6, _mean, seed=7, resamples=100)

    assert (interval.low, interval.point, interval.high) == pytest.approx((0.3, 0.3, 0.3))


def test_bootstrap_ci_reports_resamples_the_statistic_could_not_score() -> None:
    # Kappa and AUC are undefined on a resample that lost a class. Those draws
    # have to be dropped and counted, because an interval built on 40% of the
    # requested resamples is a different claim than one built on all of them.
    sample = [1, 1, 1, 2]

    interval = stats.bootstrap_ci(sample, _fails_without_both_values, seed=3, resamples=100)

    assert interval.resamples_skipped > 0
    assert interval.resamples_used + interval.resamples_skipped == 100


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _fails_without_both_values(values: list[int]) -> float:
    if len(set(values)) < 2:
        raise ValueError("needs both values")
    return _mean(values)


# --- blinding -----------------------------------------------------------------


def _pair(pair_id: str = "p0001") -> corpus.Pair:
    return corpus.Pair(
        pair_id=pair_id,
        kind="local_vs_premium",
        task_type="factual_qa",
        prompt="Why is the sky blue?",
        left=corpus.ResponseSide(origin="local", model="llama3.2:3b", text="Rayleigh scattering."),
        right=corpus.ResponseSide(
            origin="premium_a", model="openai/gpt-4o-mini", text="Short wavelengths scatter."
        ),
        cosine={"none": 0.83, "search_query": 0.86},
        band="0.80-0.90",
    )


def test_blinding_assigns_the_same_sides_every_time_for_one_rater() -> None:
    # Labelling runs over several sittings. If the sides moved between
    # sittings, a resumed session would relabel a different pair.
    first = blinding.blind(_pair(), rater_id="human-1")
    second = blinding.blind(_pair(), rater_id="human-1")

    assert first == second


def test_blinding_is_stable_across_processes() -> None:
    # Python salts hash() per process. A blinding built on it would silently
    # differ between the first sitting and the resumed one. One pair is not
    # enough to detect that: a coin flip agrees half the time. Compare the
    # whole orientation vector and the whole presentation order.
    import os
    import subprocess
    import sys

    probe = (
        "from tests.test_metric_validation import _pair;"
        "from scripts.metric_validation import blinding;"
        "ids=[f'p{i:04d}' for i in range(40)];"
        "print(''.join('1' if blinding.blind(_pair(i), rater_id='human-1').swapped"
        " else '0' for i in ids));"
        "print(','.join(blinding.presentation_order(ids, rater_id='human-1')))"
    )

    def fingerprint(hash_seed: str) -> str:
        return subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": hash_seed},
        ).stdout

    assert fingerprint("0") == fingerprint("12345")


def test_blinding_differs_between_raters() -> None:
    # Two raters must not receive the same orientation, or a shared positional
    # bias would inflate their agreement.
    pairs = [_pair(f"p{index:04d}") for index in range(40)]

    human = [blinding.blind(pair, rater_id="human-1").swapped for pair in pairs]
    judge = [blinding.blind(pair, rater_id="llm-judge").swapped for pair in pairs]

    assert human != judge


def test_blinding_uses_both_orientations_across_a_corpus() -> None:
    orientations = {
        blinding.blind(_pair(f"p{index:04d}"), rater_id="human-1").swapped
        for index in range(40)
    }

    assert orientations == {True, False}


def test_presentation_order_is_a_permutation_that_differs_between_raters() -> None:
    pair_ids = [f"p{index:04d}" for index in range(40)]

    human = blinding.presentation_order(pair_ids, rater_id="human-1")
    judge = blinding.presentation_order(pair_ids, rater_id="llm-judge")

    assert sorted(human) == sorted(pair_ids)
    assert human != judge


def test_blinded_payload_carries_no_provenance() -> None:
    # This is the whole point of the protocol: the rater must not be able to
    # infer which side is local, how similar the metric thinks they are, or
    # which band the pair was sampled from.
    payload = blinding.blinded_payload(_pair(), rater_id="human-1")

    assert set(payload) == {"pair_id", "prompt", "response_a", "response_b"}
    leaked = {"local", "premium_a", "llama3.2:3b", "openai/gpt-4o-mini", "0.80-0.90", "0.83"}
    assert not any(secret in repr(payload) for secret in leaked)


# --- rubric and label store ----------------------------------------------------


def test_the_derived_binary_cuts_the_ordinal_scale_between_minor_loss_and_partial() -> None:
    substitutable = [
        grade for grade in rubric.SCALE if rubric.is_substitutable(grade)
    ]

    assert substitutable == ["equivalent", "minor_loss"]


def test_labels_round_trip_through_the_store(tmp_path) -> None:
    path = tmp_path / "human-1.jsonl"

    labels.append(
        labels.Label(pair_id="p0001", rater_id="human-1", grade="minor_loss", notes="tone"),
        path,
    )

    assert labels.read(path) == [
        labels.Label(pair_id="p0001", rater_id="human-1", grade="minor_loss", notes="tone")
    ]


def test_a_relabelled_pair_keeps_the_last_grade_and_the_earlier_line(tmp_path) -> None:
    # Raters correct themselves. The corrected grade has to win, and the
    # superseded one has to stay on disk so the study can be audited.
    path = tmp_path / "human-1.jsonl"
    labels.append(labels.Label(pair_id="p0001", rater_id="human-1", grade="partial"), path)
    labels.append(labels.Label(pair_id="p0001", rater_id="human-1", grade="minor_loss"), path)

    assert [label.grade for label in labels.read(path)] == ["minor_loss"]
    assert len(path.read_text(encoding="utf-8").strip().splitlines()) == 2


def test_the_store_refuses_a_grade_outside_the_rubric(tmp_path) -> None:
    # A typo must never reach the file; a bad grade found at report time means
    # the rater has to be recalled.
    with pytest.raises(ValueError, match="not on the rubric"):
        labels.append(
            labels.Label(pair_id="p0001", rater_id="human-1", grade="pretty_good"),
            tmp_path / "human-1.jsonl",
        )


def test_remaining_pairs_resume_in_the_raters_presentation_order(tmp_path) -> None:
    path = tmp_path / "human-1.jsonl"
    pair_ids = [f"p{index:04d}" for index in range(10)]
    order = blinding.presentation_order(pair_ids, rater_id="human-1")
    labels.append(labels.Label(pair_id=order[0], rater_id="human-1", grade="equivalent"), path)
    labels.append(labels.Label(pair_id=order[1], rater_id="human-1", grade="divergent"), path)

    assert labels.remaining(pair_ids, path, rater_id="human-1") == order[2:]


def test_spearman_is_minus_one_for_a_perfectly_reversed_ranking() -> None:
    assert stats.spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == pytest.approx(-1.0)


def test_spearman_averages_the_ranks_of_tied_values() -> None:
    # Ordinal grades tie constantly: with a four-point scale over 130 pairs,
    # every grade is a large tie group. Ranking them arbitrarily instead of by
    # midrank would make the correlation depend on file order.
    assert stats.spearman([1, 1, 2, 3], [1, 2, 3, 4]) == pytest.approx(0.9486832980505138)


def test_spearman_is_undefined_when_one_side_is_constant() -> None:
    with pytest.raises(ValueError, match="no variance"):
        stats.spearman([1, 1, 1, 1], [1, 2, 3, 4])


# --- analysis ------------------------------------------------------------------


def _graded_corpus() -> tuple[list[corpus.Pair], dict[str, dict[str, str]]]:
    """Eight pairs whose cosines separate well under one prefix and not another."""
    specs = [
        ("p0001", "local_vs_premium", 0.95, 0.50, "equivalent"),
        ("p0002", "local_vs_premium", 0.92, 0.55, "equivalent"),
        ("p0003", "local_vs_premium", 0.88, 0.52, "minor_loss"),
        ("p0004", "local_vs_premium", 0.85, 0.58, "minor_loss"),
        ("p0005", "cross_prompt", 0.40, 0.54, "divergent"),
        ("p0006", "cross_prompt", 0.35, 0.51, "divergent"),
        ("p0007", "local_vs_premium", 0.55, 0.53, "partial"),
        ("p0008", "local_vs_premium", 0.60, 0.56, "partial"),
    ]
    pairs = [
        corpus.Pair(
            pair_id=pair_id,
            kind=kind,
            task_type="factual_qa",
            prompt=f"prompt for {pair_id}",
            left=corpus.ResponseSide(origin="local", model="llama3.2:3b", text="left"),
            right=corpus.ResponseSide(origin="premium_a", model="gpt-4o-mini", text="right"),
            cosine={"none": sharp, "clustering": flat},
            band=corpus.band_for(sharp),
        )
        for pair_id, kind, sharp, flat, _ in specs
    ]
    grades = {"human-1": {pair_id: grade for pair_id, _, _, _, grade in specs}}
    return pairs, grades


def test_prefix_sweep_ranks_variants_by_how_well_the_cosine_separates_the_labels() -> None:
    pairs, grades = _graded_corpus()

    sweep = analysis.prefix_sweep(pairs, grades["human-1"], seed=1, resamples=100)

    assert [result.prefix for result in sweep] == ["none", "clustering"]
    assert sweep[0].auc == pytest.approx(1.0)
    assert sweep[0].auc > sweep[1].auc


def test_prefix_sweep_only_scores_pairs_the_reference_rater_actually_graded() -> None:
    # An ungraded pair has no ground truth. Counting it would score the metric
    # against a label nobody produced.
    pairs, grades = _graded_corpus()
    partial_grades = {
        pair_id: grade
        for pair_id, grade in grades["human-1"].items()
        if pair_id in {"p0001", "p0005"}
    }

    sweep = analysis.prefix_sweep(pairs, partial_grades, seed=1, resamples=100)

    assert all(result.pairs == 2 for result in sweep)


def test_prefix_sweep_reports_no_measurable_separation_instead_of_inventing_an_auc() -> None:
    # Every graded pair on the same side of the binary cut leaves AUC
    # undefined. Reporting 0.5, or 1.0, would be a fabricated number.
    pairs, _ = _graded_corpus()
    one_sided = {"p0001": "equivalent", "p0002": "equivalent"}

    sweep = analysis.prefix_sweep(pairs, one_sided, seed=1, resamples=100)

    assert all(result.auc is None for result in sweep)
    assert all("no measurable separation" in result.note for result in sweep)


def test_separation_by_band_reports_the_substitutable_rate_per_band() -> None:
    pairs, grades = _graded_corpus()

    rows = analysis.separation_by_band(pairs, grades["human-1"], prefix="none")

    top = next(row for row in rows if row.band == "0.90-1.00")
    bottom = next(row for row in rows if row.band == "0.00-0.50")
    assert (top.pairs, top.substitutable_rate) == (2, pytest.approx(1.0))
    assert (bottom.pairs, bottom.substitutable_rate) == (2, pytest.approx(0.0))


def test_separation_by_band_can_exclude_the_planted_negative_pairs() -> None:
    # cross_prompt pairs are planted anchors, not traffic Nebula would ever
    # route. The headline separation has to be reportable without them.
    pairs, grades = _graded_corpus()

    rows = analysis.separation_by_band(
        pairs, grades["human-1"], prefix="none", kinds=("local_vs_premium",)
    )

    assert sum(row.pairs for row in rows) == 6


def test_agreement_is_computed_on_the_pairs_both_raters_graded() -> None:
    pairs, grades = _graded_corpus()
    grades["llm-judge"] = {
        pair_id: grade for pair_id, grade in list(grades["human-1"].items())[:6]
    }

    agreements = analysis.pairwise_agreement(grades, seed=1, resamples=100)

    assert len(agreements) == 1
    assert agreements[0].pairs == 6
    assert agreements[0].quadratic_weighted_kappa == pytest.approx(1.0)


def test_the_report_marks_human_to_human_agreement_pending_with_one_human_rater() -> None:
    # The plan's rigour point 3 asks for two humans. One human plus an LLM is
    # not that, and the report must not let the number pass for it.
    pairs, grades = _graded_corpus()
    grades["llm-judge"] = dict(grades["human-1"])

    report = analysis.build_report(pairs, grades, reference_rater="human-1", seed=1, resamples=100)

    assert report.human_to_human_pending is True
    assert report.human_raters == ["human-1"]


# --- capture -------------------------------------------------------------------


def test_cosine_of_a_vector_with_itself_is_one() -> None:
    assert capture.cosine([0.3, 0.4], [0.3, 0.4]) == pytest.approx(1.0)


def test_cosine_of_orthogonal_vectors_is_zero() -> None:
    assert capture.cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_refuses_a_zero_norm_vector() -> None:
    # An empty completion embeds to a zero vector. Dividing by its norm would
    # hand the study a NaN that silently poisons every downstream average.
    with pytest.raises(ValueError, match="zero-norm"):
        capture.cosine([0.0, 0.0], [1.0, 0.0])


def test_apply_prefix_leaves_the_provisional_variant_untouched() -> None:
    assert capture.apply_prefix("why is the sky blue", "none") == "why is the sky blue"


def test_apply_prefix_prepends_the_nomic_task_prefix() -> None:
    assert capture.apply_prefix("why is the sky blue", "clustering") == (
        "clustering: why is the sky blue"
    )


def _prompt_records() -> list[capture.PromptRecord]:
    return [
        capture.PromptRecord(prompt_id=f"q{index:03d}", task_type=task, prompt=f"ask {index}")
        for index, task in enumerate(["factual_qa"] * 4 + ["code"] * 4)
    ]


def _fake_similarity(left: str, right: str, prefix: str) -> float:
    return 0.9 if left == right else 0.6


def test_build_pairs_produces_the_requested_mix_of_pair_kinds() -> None:
    records = _prompt_records()
    responses = {record.prompt_id: f"answer {record.prompt_id}" for record in records}

    pairs = capture.build_pairs(
        records,
        local=responses,
        premium_a=responses,
        premium_b=responses,
        similarity=_fake_similarity,
        noise_floor_count=3,
        cross_prompt_count=2,
    )

    counts = Counter(pair.kind for pair in pairs)
    assert counts == Counter(local_vs_premium=8, premium_vs_premium=3, cross_prompt=2)


def test_cross_prompt_pairs_borrow_an_answer_to_a_different_prompt_of_the_same_task() -> None:
    # The planted negatives anchor the low band. Borrowing across task types
    # would make them trivially detectable and stop anchoring anything.
    records = _prompt_records()
    responses = {record.prompt_id: f"answer {record.prompt_id}" for record in records}
    task_of = {record.prompt_id: record.task_type for record in records}

    pairs = capture.build_pairs(
        records,
        local=responses,
        premium_a=responses,
        premium_b=responses,
        similarity=_fake_similarity,
        noise_floor_count=0,
        cross_prompt_count=4,
    )

    for pair in (pair for pair in pairs if pair.kind == "cross_prompt"):
        borrowed = pair.right.text.removeprefix("answer ")
        own = pair.pair_id.split(":")[-1]
        assert borrowed != own
        assert task_of[borrowed] == task_of[own]


def test_build_pairs_is_deterministic() -> None:
    records = _prompt_records()
    responses = {record.prompt_id: f"answer {record.prompt_id}" for record in records}
    kwargs = dict(
        local=responses,
        premium_a=responses,
        premium_b=responses,
        similarity=_fake_similarity,
        noise_floor_count=3,
        cross_prompt_count=2,
    )

    assert capture.build_pairs(records, **kwargs) == capture.build_pairs(records, **kwargs)


def test_build_pairs_bands_each_pair_under_the_provisional_prefix() -> None:
    records = _prompt_records()[:1]
    responses = {"q000": "answer q000"}

    pair = capture.build_pairs(
        records,
        local=responses,
        premium_a=responses,
        premium_b=responses,
        similarity=_fake_similarity,
        noise_floor_count=0,
        cross_prompt_count=0,
    )[0]

    assert pair.band == corpus.band_for(pair.cosine[corpus.PROVISIONAL_PREFIX])


def test_capture_refuses_to_run_against_the_mock_premium_provider() -> None:
    # The mock echoes the prompt back. Every reference it produced would score
    # as a near-duplicate of the prompt rather than as a premium answer, and
    # the whole study would read as a success.
    with pytest.raises(RuntimeError, match="mock"):
        capture.ensure_real_premium(provider="mock", base_url="", model="mock")


def test_capture_accepts_a_configured_openai_compatible_premium_provider() -> None:
    capture.ensure_real_premium(
        provider="openai_compatible",
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-4o-mini",
    )


def test_capture_refuses_a_premium_provider_with_no_base_url() -> None:
    with pytest.raises(RuntimeError, match="base URL"):
        capture.ensure_real_premium(
            provider="openai_compatible", base_url="", model="openai/gpt-4o-mini"
        )
