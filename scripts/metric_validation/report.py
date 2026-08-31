"""Render the metric-validation findings.

Everything here exists to stop one misreading: that an LLM agreeing with the
single human rater is the inter-rater agreement the study set out to report.
The auxiliary rater is named as auxiliary everywhere it appears, and the
human-to-human slot stays visibly empty until a second person fills it.
"""

from __future__ import annotations

from dataclasses import asdict

from scripts.metric_validation.analysis import RaterAgreement, ValidationReport

AUXILIARY_PREFIX = "llm-"

PENDING_NOTE = (
    "**Human-to-human agreement: PENDING.** Rigour point 3 of the Phase 1 plan asks "
    "for two human evaluators. This run has {count}. The LLM rater below is an "
    "auxiliary rater: it followed the same rubric on the same blinded pairs, and its "
    "agreement with the human rater is evidence that the rubric can be applied "
    "consistently — it is not the inter-rater agreement the plan requires, and it "
    "must not be reported as such."
)

PLANTED_NOTE = (
    "`cross_prompt` pairs are planted negatives: a premium answer to a *different* "
    "prompt of the same task type. They anchor the low band so AUC is measurable, "
    "but they are not traffic Nebula would ever route. The `local_vs_premium only` "
    "table below is the honest one."
)


def _is_auxiliary(rater: str) -> bool:
    return rater.startswith(AUXILIARY_PREFIX)


def _rater_label(rater: str) -> str:
    return f"{rater} (auxiliary)" if _is_auxiliary(rater) else rater


def _number(value: float | None, digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _agreement_row(agreement: RaterAgreement) -> str:
    interval = agreement.kappa_ci
    ci = (
        "—"
        if interval is None
        else f"[{interval.low:.3f}, {interval.high:.3f}]"
    )
    return (
        f"| {_rater_label(agreement.left_rater)} | {_rater_label(agreement.right_rater)} "
        f"| {agreement.pairs} | {_number(agreement.cohens_kappa_binary)} "
        f"| {_number(agreement.quadratic_weighted_kappa)} | {ci} | {agreement.note or '—'} |"
    )


def render_markdown(report: ValidationReport) -> str:
    lines = [
        "# Metric validation — pilot study",
        "",
        f"Reference rater: `{report.reference_rater}`. "
        f"Raters: {', '.join(f'`{_rater_label(r)}`' for r in report.raters)}.",
        "",
    ]

    if report.human_to_human_pending:
        lines += [PENDING_NOTE.format(count=len(report.human_raters)), ""]

    lines += [
        "## Task prefix sweep",
        "",
        "Which `nomic-embed-text` task prefix best separates the grades. Decided "
        "after labelling, on the labels, so the choice cannot be read off the "
        "stratification.",
        "",
        "| prefix | pairs | AUC | 95% CI | resamples used/skipped | Spearman | note |",
        "|---|---|---|---|---|---|---|",
    ]
    for result in report.prefix_sweep:
        interval = result.auc_ci
        ci = "—" if interval is None else f"[{interval.low:.3f}, {interval.high:.3f}]"
        used = (
            "—"
            if interval is None
            else f"{interval.resamples_used}/{interval.resamples_skipped}"
        )
        lines.append(
            f"| `{result.prefix}` | {result.pairs} | {_number(result.auc)} | {ci} "
            f"| {used} | {_number(result.spearman)} | {result.note or '—'} |"
        )

    chosen = f"`{report.chosen_prefix}`" if report.chosen_prefix else "none — unmeasurable"
    lines += ["", f"**Chosen prefix: {chosen}.**"]
    if report.chosen_prefix_tied_with:
        tied = ", ".join(f"`{prefix}`" for prefix in report.chosen_prefix_tied_with)
        lines += [
            "",
            f"This is a **tie** with {tied} on AUC, broken by declared variant "
            "order. The ranking above is not evidence that the chosen prefix "
            "separates the grades better than the ones it tied with.",
        ]
    lines += [""]

    lines += ["## Separation by similarity band", "", PLANTED_NOTE, ""]
    for title, rows in (
        ("all pairs", report.bands_all),
        ("local_vs_premium only", report.bands_local_vs_premium),
    ):
        lines += [
            f"### {title}",
            "",
            "| band | pairs | substitutable | rate |",
            "|---|---|---|---|",
        ]
        lines += [
            f"| {row.band} | {row.pairs} | {row.substitutable} | {row.substitutable_rate:.2f} |"
            for row in rows
        ] or ["| — | 0 | 0 | — |"]
        lines.append("")

    lines += [
        "## Inter-rater agreement",
        "",
        "| rater | rater | shared pairs | Cohen κ (binary) | quadratic-weighted κ "
        "| 95% CI | note |",
        "|---|---|---|---|---|---|---|",
    ]
    lines += [_agreement_row(agreement) for agreement in report.agreements]
    lines += [
        "",
        f"Krippendorff's ordinal α across all raters: {_number(report.krippendorff_alpha)}.",
        "",
    ]

    return "\n".join(lines)


def to_payload(report: ValidationReport) -> dict[str, object]:
    """The machine-readable form, keeping every losing prefix variant."""
    payload = asdict(report)
    payload["auxiliary_raters"] = [r for r in report.raters if _is_auxiliary(r)]
    return payload
