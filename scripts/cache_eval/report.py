"""The cache measurement's report: the pre-registered verdict, its curves and the saving.

    python -m scripts.cache_eval.report

computes everything ``benchmarks/cache/v1/preregistration.md`` registers and writes
``benchmarks/cache/v1/report.json`` and ``report.md``.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import math
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from nebula.services.learned_router import LearnedRouterModel
from nebula.services.semantic_cache_service import TIER_RANK
from scripts.cache_eval import embed, replay
from scripts.cache_eval.neighbors import find_pairs
from scripts.cache_eval.replay import TRACE_LENGTH, Original, Paraphrase, Prices
from scripts.ground_truth.records import PromptRow, read_rows

# The registered threshold grid: 0.80 to 0.99 in hundredths (exact decimal-nearest floats).
GRID: tuple[float, ...] = tuple(i / 100 for i in range(80, 100))
# Production model first; the second is the sensitivity model, which never enters the verdict.
MODEL_KEYS: dict[str, str] = {"nomic_v1": "nomic-embed-text", "nomic_v2": "nomic-embed-text-v2-moe"}
# Ollama digests: the production one is the pre-registered model (artifacts/router-embeddings/
# provenance.json); the sensitivity one is what the local Ollama served on 2026-10-22.
MODELS: dict[str, dict] = {
    "nomic_v1": {
        "name": "nomic-embed-text",
        "role": "production",
        "prefix": "none",
        "digest": "0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f",
    },
    "nomic_v2": {
        "name": "nomic-embed-text-v2-moe",
        "role": "sensitivity",
        "prefix": "none",
        "digest": "ff9c2f10ef5e3722623a1b396e1e04efc27a93112c83e9b7b7b9ca1d05620965",
    },
}


# The pre-registered criterion: precision >= 0.95 on both (a) and (c), reported at t = 0.90; a
# grid point counts only with >= 20 hits in each set.
CRITERION = 0.95
DEFAULT_T = 0.90
MIN_HITS = 20


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def t_key(t: float) -> str:
    """A threshold as a report key: two decimals, "0.90"."""
    return f"{t:.2f}"


def f05(precision: float | None, recall: float | None) -> float | None:
    """F0.5: precision weighted over recall. Undefined when precision is."""
    if precision is None or recall is None:
        return None
    if precision == 0 and recall == 0:
        return 0.0
    return 1.25 * precision * recall / (0.25 * precision + recall)


def pawsx_curve(
    pairs: Sequence[dict], *, model_key: str, grid: Sequence[float] = GRID
) -> list[dict]:
    """Set (a): "cosine >= t" as a paraphrase classifier against the human label, per t.

    A hit is a positive prediction (TP + FP). Precision = TP / hits, recall = TP / label-1 pairs.
    """
    column = f"cos_{model_key}"
    positives = sum(1 for pair in pairs if pair["label"] == 1)
    rows = []
    for t in grid:
        hits = [pair for pair in pairs if pair[column] >= t]
        tp = sum(1 for pair in hits if pair["label"] == 1)
        precision = _ratio(tp, len(hits))
        recall = _ratio(tp, positives)
        rows.append(
            {
                "t": t,
                "hits": len(hits),
                "tp": tp,
                "precision": precision,
                "recall": recall,
                "f05": f05(precision, recall),
            }
        )
    return rows


CORPUS_PATH = Path("benchmarks/ground-truth/v1/prompts.es.jsonl")
TIERS_PATH = Path("benchmarks/ground-truth/v1/tiers.jsonl")
ROUTER_PATH = Path("src/nebula/data/learned_router_v1.json")
ROUTER_REPLAY_PATH = Path("src/nebula/data/router_replay_v1.json")
PRODUCTION_VECTORS_PATH = Path("artifacts/router-embeddings/none.json")
# The router's quality target the cache is measured under (the product default).
TIER_TARGET = 0.95


def load_prices(replay_rows: Sequence[dict], tier_labels: Sequence[dict]) -> Prices:
    """Per Spanish corpus prompt: the captured cost of each tier (local is free at the margin)
    and the ground-truth substitutability of each tier's answer (the frontier is the reference)."""
    cost = {
        row["key"].removeprefix("es:"): {
            "local": 0.0,
            "economy": float(row["cost_economy"]),
            "frontier": float(row["cost_frontier"]),
        }
        for row in replay_rows
        if row["key"].startswith("es:")
    }
    quality = {
        row["prompt_id"]: {
            "local": float(bool(row["local_substitutable"])),
            "economy": float(bool(row["economy_substitutable"])),
            "frontier": 1.0,
        }
        for row in tier_labels
        if row["lang"] == "es"
    }
    return Prices(cost=cost, quality=quality)


def router_only_check(
    *, router: LearnedRouterModel, replay_payload: dict, vectors: Mapping[str, list[float]]
) -> dict:
    """The router-only cost per 1000 prompts with the shipped router at the target, on the whole
    corpus (as the thesis cites it) and on its Spanish part (what the cache replay serves), next
    to the cited figures from ``router_replay_v1.json``."""

    def cost_per_1000(rows: Sequence[dict]) -> float:
        total = 0.0
        for row in rows:
            tier = router.choose(vectors[row["key"]], TIER_TARGET).tier
            total += {
                "local": 0.0,
                "economy": row["cost_economy"],
                "frontier": row["cost_frontier"],
            }[tier]
        return total * 1000 / len(rows)

    rows = replay_payload["rows"]
    spanish = [row for row in rows if row["key"].startswith("es:")]
    point = router.operating_point(TIER_TARGET)
    return {
        "target": TIER_TARGET,
        "corpus_prompts": len(rows),
        "spanish_prompts": len(spanish),
        "corpus_cost_per_1000": cost_per_1000(rows),
        "spanish_cost_per_1000": cost_per_1000(spanish),
        "cited_cost_per_1000": replay_payload["nested"][str(TIER_TARGET)]["cost"] * 1000,
        "cited_spanish_cost_per_1000": (
            replay_payload["nested"][str(TIER_TARGET)]["by_lang"]["es"]["cost"] * 1000
        ),
        "operating_point_cost_per_1000": point.cost_per_prompt * 1000,
        "operating_point": {"tau_local": point.tau_local, "tau_economy": point.tau_economy},
    }


PENDING = "pendiente"
# Cosine bands of the neighbor pairs (b), highest first: [0.95, ...), [0.90, 0.95), [0.85, 0.90).
NEIGHBOR_BANDS: tuple[float, ...] = (0.95, 0.90, 0.85)


def read_labels(path: Path) -> dict[str, str] | None:
    """A rater's labels by pair id, the last row of a pair winning; None when the file is absent."""
    if not path.exists():
        return None
    labels: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            labels[row["pair_id"]] = row["label"]
    return labels


def _label_counts(ids: Sequence[str], labels: Mapping[str, str]) -> dict:
    values = [labels.get(pair_id) for pair_id in ids]
    si, no = values.count("sí"), values.count("no")
    return {
        "si": si,
        "no": no,
        "unsure": values.count("?"),
        "unlabeled": values.count(None),
        "acceptable_share": _ratio(si, si + no),
    }


def neighbors_section(
    pairs: Sequence[dict],
    labels: Mapping[str, str] | None,
    *,
    thresholds: Sequence[float],
    column: str = "cos_nomic_v1",
) -> dict:
    """Set (b), descriptive only: pairs per cosine band (``column``, the production model's by
    default) and, once labeled, the share a human finds acceptable ("¿Una respuesta a A sirve
    para B?" = sí) per band, and how often the cache's decision at each threshold (serve when
    cosine >= t) agrees with the human."""
    bands = []
    upper: float | None = None
    for lower in NEIGHBOR_BANDS:
        members = [p for p in pairs if p[column] >= lower and (upper is None or p[column] < upper)]
        band = {"from": lower, "to": upper, "pairs": len(members)}
        if labels is not None:
            band |= _label_counts([p["pair_id"] for p in members], labels)
        bands.append(band)
        upper = lower
    section: dict = {"pairs": len(pairs), "bands": bands}
    if labels is None:
        section["human_labels"] = PENDING
        return section
    decided = [p for p in pairs if labels.get(p["pair_id"]) in ("sí", "no")]
    agreement = {}
    for t in thresholds:
        agree = sum(1 for p in decided if (p[column] >= t) == (labels[p["pair_id"]] == "sí"))
        agreement[t_key(t)] = _ratio(agree, len(decided))
    section["human_labels"] = {
        "pairs": len(pairs),
        "labeled": sum(1 for p in pairs if p["pair_id"] in labels),
        "decided": len(decided),
        "agreement": agreement,
    }
    return section


def paraphrase_validation(sample: Sequence[dict], labels: Mapping[str, str] | None) -> dict | str:
    """The 40-pair human check ("¿B pide lo mismo que A?"): the faithful share of the decided
    labels ("?" left out), or "pendiente" before any label exists. Never enters the verdict."""
    if labels is None:
        return PENDING
    ids = [row["pair_id"] for row in sample]
    counts = _label_counts(ids, labels)
    return {
        "sample": len(ids),
        "labeled": len(ids) - counts["unlabeled"],
        "si": counts["si"],
        "no": counts["no"],
        "unsure": counts["unsure"],
        "faithful_rate": counts["acceptable_share"],
    }


def verdict(
    points: Sequence[dict],
    *,
    default_t: float = DEFAULT_T,
    criterion: float = CRITERION,
    min_hits: int = MIN_HITS,
) -> dict:
    """The pre-registered verdict over grid points ``{t, precision_a, precision_c, hits_a, hits_c}``.

    - Only a point with >= ``min_hits`` hits in both sets is eligible.
    - ``pass``: the point at ``default_t`` is eligible and both precisions reach the criterion.
    - ``fail``: otherwise, when some eligible t reaches it on both; the smallest one is recommended.
    - ``no_safe_threshold``: no eligible t reaches it; the eligible t with the highest
      min(precision_a, precision_c) is recommended, the smallest t among ties.
    - ``not_measurable``: no point is eligible.
    Precisions are compared as given, never rounded. A recommended t becomes the product default
    (new tenants); a pass or "not measurable" keeps ``default_t``.
    """
    ordered = sorted(points, key=lambda p: p["t"])
    eligible = [p for p in ordered if p["hits_a"] >= min_hits and p["hits_c"] >= min_hits]

    def safe(point: dict) -> bool:
        return point["precision_a"] >= criterion and point["precision_c"] >= criterion

    outcome: str
    recommended: float | None = None
    if not eligible:
        outcome = "not_measurable"
    elif any(p["t"] == default_t and safe(p) for p in eligible):
        outcome = "pass"
    elif safe_points := [p for p in eligible if safe(p)]:
        outcome, recommended = "fail", safe_points[0]["t"]
    else:
        # max() keeps the first of equal keys, and the points are in increasing t.
        best = max(eligible, key=lambda p: min(p["precision_a"], p["precision_c"]))
        outcome, recommended = "no_safe_threshold", best["t"]
    return {
        "verdict": outcome,
        "recommended_t": recommended,
        "product_default_t": default_t if recommended is None else recommended,
        "eligible_t": [p["t"] for p in eligible],
        "criterion": criterion,
        "default_t": default_t,
        "min_hits": min_hits,
    }


# --- Assembly ---------------------------------------------------------------------------------

# Repetition rates of the savings trace: 0 to 40 % in steps of 5 %, plus the two cited ones, each
# checked in its source. 12.1 %: FactBench (Fatahi Bayat et al., ACL 2025, App. A.1) removed that
# share of duplicated prompts from LMSYS-Chat-1M's first-turn English prompts. 31 %: MeanCache's
# study of 20 ChatGPT users found that share of queries similar to earlier ones. (A 3.7 % rate once
# attributed to WildChat was dropped: in that paper it is the share of conversations longer than
# ten turns.)
CITED_RATES: dict[str, float] = {
    "factbench_lmsys_duplicates": 0.121,
    "meancache": 0.31,
}
CITED_RATE_SOURCES: dict[str, str] = {
    "factbench_lmsys_duplicates": "FactBench's de-duplication of LMSYS-Chat-1M first-turn English prompts",
    "meancache": "MeanCache's study of 20 ChatGPT users",
}
RATES: tuple[float, ...] = tuple(
    sorted({i / 100 for i in range(0, 45, 5)} | set(CITED_RATES.values()))
)
REGISTERED_PARAPHRASES = 200
MIN_VALID_PARAPHRASES = 150
DECIMALS = 6


@dataclass(frozen=True)
class Inputs:
    """Everything the report is computed from, loaded (``load_inputs``) or hand-made (tests)."""

    originals: list[Original]
    paraphrases: list[Paraphrase]
    paraphrase_rows: list[dict]
    dropped: list[dict]
    pawsx: list[dict]
    neighbors: list[dict]
    sample: list[dict]
    neighbor_labels: dict[str, str] | None
    paraphrase_labels: dict[str, str] | None
    prices: Prices
    router_check: dict
    provenance: dict
    model_keys: tuple[str, ...] = tuple(MODEL_KEYS)
    rates: tuple[float, ...] = RATES
    trace_length: int = TRACE_LENGTH


def _rounded(value):
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"The report cannot hold a non-finite number: {value!r}.")
        return round(value, DECIMALS) + 0.0  # + 0.0 turns -0.0 into 0.0
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_rounded(item) for item in value]
    return value


def dumps(report: dict) -> str:
    """The report as committed: sorted keys, floats rounded to six decimals, one trailing newline.
    Equal inputs give byte-identical text (no timestamp anywhere)."""
    return json.dumps(_rounded(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _grid_points(curve_a: list[dict], curve_c: list[dict]) -> list[dict]:
    """Set (a) and set (c) side by side per t, as the verdict reads them."""
    return [
        {
            "t": a["t"],
            "eligible": a["hits"] >= MIN_HITS and c["hits"] >= MIN_HITS,
            "hits_a": a["hits"],
            "tp_a": a["tp"],
            "precision_a": a["precision"],
            "recall_a": a["recall"],
            "hits_c": c["hits"],
            "correct_c": c["correct_hits"],
            "precision_c": c["precision"],
            "recall_c": c["recall"],
        }
        for a, c in zip(curve_a, curve_c, strict=True)
    ]


def _at(points: list[dict], t: float | None) -> dict | None:
    return None if t is None else next(p for p in points if p["t"] == t)


def _quantiles(values: Sequence[float]) -> dict:
    ordered = sorted(values)
    if not ordered:
        return {}

    def q(p: float) -> float:
        return ordered[round(p * (len(ordered) - 1))]

    return {"min": ordered[0], "p25": q(0.25), "median": q(0.5), "p75": q(0.75), "max": ordered[-1]}


def _drop_kind(row: dict) -> str:
    if "below" in row["reason"]:
        return "too_short"
    if "above" in row["reason"]:
        return "too_long"
    return "empty_or_identical"


def _tier_relation(inputs: Inputs) -> dict:
    """How each paraphrase's own tier compares with its original's (a higher one cannot take the
    original's answer while the tier rule is on)."""
    by_id = {o.prompt_id: o for o in inputs.originals}
    relation = Counter()
    for p in inputs.paraphrases:
        own, original = TIER_RANK[p.tier], TIER_RANK[by_id[p.prompt_id].tier]
        relation["same" if own == original else "higher" if own > original else "lower"] += 1
    return {key: relation[key] for key in ("same", "higher", "lower")}


def _v2_neighbor_bands(originals: Sequence[Original]) -> dict:
    vectors = {o.prompt_id: o.vectors["nomic_v2"] for o in originals}
    pairs = find_pairs(vectors, min_cos=NEIGHBOR_BANDS[-1])
    return neighbors_section(
        [{"pair_id": f"{p.a_id}|{p.b_id}", "cos_nomic_v2": p.cosine} for p in pairs],
        None,
        thresholds=(),
        column="cos_nomic_v2",
    )["bands"]


async def _replay_model(inputs: Inputs, model_key: str) -> dict:
    cache = await replay.build_cache(inputs.originals, model_key=model_key)
    rule_off = await replay.replay_candidates(
        cache, inputs.paraphrases, inputs.originals, model_key=model_key
    )
    rule_on = await replay.replay_candidates(
        cache, inputs.paraphrases, inputs.originals, model_key=model_key, tier_rule=True
    )
    curve_a = pawsx_curve(inputs.pawsx, model_key=model_key)
    curve_c = [replay.replay_metrics(rule_off, t=t) for t in GRID]
    points = _grid_points(curve_a, curve_c)
    return {
        "curve_a": curve_a,
        "curve_c": curve_c,
        "rule_on": rule_on,
        "points": points,
        "verdict": verdict(points),
    }


async def _savings(inputs: Inputs, model_key: str, thresholds: Sequence[float]) -> dict:
    out = {}
    for t in thresholds:
        curve = await replay.savings_curve(
            inputs.originals,
            inputs.paraphrases,
            inputs.prices,
            model_key=model_key,
            rates=inputs.rates,
            t=t,
            n=inputs.trace_length,
        )
        by_rate = {row["r"]: row for row in curve}
        out[t_key(t)] = {
            "t": t,
            "curve": curve,
            "cited": {name: by_rate[rate] for name, rate in CITED_RATES.items() if rate in by_rate},
        }
    return out


def _consistency(inputs: Inputs, savings: dict) -> dict:
    """The savings trace without repeats against the router's own cost (raises on a mismatch)."""
    check = inputs.router_check
    corpus_gap = check["corpus_cost_per_1000"] - check["cited_cost_per_1000"]
    if abs(corpus_gap) > 0.01:
        raise ValueError(
            f"The shipped router's router-only cost on the corpus (USD "
            f"{check['corpus_cost_per_1000']:.4f} per 1000) is not within 0.01 of the cited "
            f"{check['cited_cost_per_1000']:.4f}."
        )
    result = dict(check) | {"corpus_minus_cited": corpus_gap}
    if 0.0 not in inputs.rates or inputs.trace_length != len(inputs.originals):
        return result | {"r0_router_only_cost_per_1000": None}
    r0 = {key: block["curve"][inputs.rates.index(0.0)] for key, block in savings.items()}
    trace_router_only = {row["router_only_cost_per_1000"] for row in r0.values()}
    for value in trace_router_only:
        if abs(value - check["spanish_cost_per_1000"]) > 1e-9:
            raise ValueError(
                f"Without repeats the trace's router-only cost (USD {value:.6f} per 1000) is not "
                f"the shipped router's cost on the Spanish prompts "
                f"({check['spanish_cost_per_1000']:.6f})."
            )
    return result | {
        "r0_router_only_cost_per_1000": check["spanish_cost_per_1000"],
        "r0_cost_per_1000": {key: row["cost_per_1000"] for key, row in r0.items()},
        "r0_false_hits": {key: row["false_hits"] for key, row in r0.items()},
    }


async def build(inputs: Inputs) -> dict:
    """The whole report from its inputs (no I/O)."""
    production, *sensitivity = inputs.model_keys
    replays = {key: await _replay_model(inputs, key) for key in inputs.model_keys}
    main = replays[production]
    v = main["verdict"]
    reported_t = {
        key: [DEFAULT_T]
        + (
            [r["verdict"]["recommended_t"]]
            if r["verdict"]["recommended_t"] not in (None, DEFAULT_T)
            else []
        )
        for key, r in replays.items()
    }
    valid = len(inputs.paraphrases)

    preregistration = {
        **v,
        "model": MODEL_KEYS[production],
        "at_default": _at(main["points"], DEFAULT_T),
        "at_recommended": _at(main["points"], v["recommended_t"]),
        "grid": main["points"],
        "valid_paraphrases": valid,
        "registered_paraphrases": REGISTERED_PARAPHRASES,
        "fewer_than_150_valid": valid < MIN_VALID_PARAPHRASES,
        "leave_one_out_originals": len(inputs.originals),
        "tier_rule": "off: every original is stored at its router tier and looked up with "
        "min_tier_rank=0, so every entry (rank 0, 1 or 2) is eligible",
    }

    savings = {key: await _savings(inputs, key, reported_t[key]) for key in inputs.model_keys}
    paraphrase_block = {
        "valid": valid,
        "registered": REGISTERED_PARAPHRASES,
        "dropped": len(inputs.dropped),
        "dropped_by_kind": dict(sorted(Counter(_drop_kind(d) for d in inputs.dropped).items())),
        "valid_by_task": dict(
            sorted(Counter(r["task_type"] for r in inputs.paraphrase_rows).items())
        ),
        "tier_vs_original": _tier_relation(inputs),
    }
    for key, r in replays.items():
        paraphrase_block[key] = {
            "own_original_cosine": _quantiles(
                [row[f"cos_{key}"] for row in inputs.paraphrase_rows]
            ),
            "curve": r["curve_c"],
            "tier_rule_on": {
                t_key(t): replay.replay_metrics(r["rule_on"], t=t) for t in reported_t[key]
            },
        }

    neighbors = neighbors_section(
        inputs.neighbors, inputs.neighbor_labels, thresholds=reported_t[production]
    )
    if "nomic_v2" in inputs.model_keys:
        neighbors["nomic_v2_bands"] = _v2_neighbor_bands(inputs.originals)

    tiers = Counter(o.tier for o in inputs.originals)
    return {
        "preregistration": preregistration,
        "pawsx": {
            key: {
                "pairs": len(inputs.pawsx),
                "paraphrases": sum(1 for p in inputs.pawsx if p["label"] == 1),
                "curve": r["curve_a"],
            }
            for key, r in replays.items()
        },
        "paraphrases": paraphrase_block,
        "neighbors": neighbors,
        "paraphrase_validation": paraphrase_validation(inputs.sample, inputs.paraphrase_labels),
        "savings": {
            **savings,
            "rates": list(inputs.rates),
            "cited_rates": CITED_RATES,
            "trace": {
                "length": inputs.trace_length,
                "seed": replay.SEED,
                "exact_share_of_repeats": 0.5,
                "tier_rule": "on",
                "cache_starts": "empty",
            },
            "consistency": _consistency(inputs, savings[production]),
        },
        "router": {
            "target": TIER_TARGET,
            "spanish_tiers": {tier: tiers[tier] for tier in ("local", "economy", "frontier")},
            "paraphrase_tiers": dict(sorted(Counter(p.tier for p in inputs.paraphrases).items())),
        },
        "models": {
            "production": {"key": production, **MODELS[production]},
            "sensitivity": [
                {
                    "key": key,
                    **MODELS[key],
                    # The rule's outcome for this model; it never sets the product default.
                    "verdict": {
                        k: value
                        for k, value in replays[key]["verdict"].items()
                        if k != "product_default_t"
                    },
                    "at_default": _at(replays[key]["points"], DEFAULT_T),
                    "at_recommended": _at(
                        replays[key]["points"], replays[key]["verdict"]["recommended_t"]
                    ),
                    "grid": replays[key]["points"],
                }
                for key in sensitivity
            ],
        },
        "provenance": inputs.provenance,
    }


# --- Markdown -----------------------------------------------------------------------------------

VERDICT_TEXT = {
    "pass": "**pass**: both precisions reach {criterion} at t = {default}",
    "fail": "**fail** at t = {default}. Recommended t = **{rec}**, the smallest eligible t where both "
    "precisions reach {criterion}",
    "no_safe_threshold": "**no safe threshold on the grid**: no eligible t reaches {criterion} on "
    "both sets. Recommended t = **{rec}**, the eligible t with the highest "
    "min(precision_a, precision_c), which does not meet {criterion}",
    "not_measurable": "**not measurable with these data**: no grid point has {min_hits} hits in "
    "both sets",
}
# What the verdict does to the product (the production model's verdict only).
CONSEQUENCE_TEXT = {
    "pass": "; the product default stays {default}.",
    "fail": "; the product default for new tenants becomes {rec}.",
    "no_safe_threshold": "; the product default for new tenants becomes {rec}.",
    "not_measurable": "; the product default stays {default}.",
}


def _num(value, digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _pct(value) -> str:
    return "—" if value is None else f"{value * 100:.1f} %"


def _usd(value) -> str:
    return "—" if value is None else f"{value:.3f}"


def _verdict_line(v: dict, *, consequence: bool = True) -> str:
    template = VERDICT_TEXT[v["verdict"]] + (CONSEQUENCE_TEXT[v["verdict"]] if consequence else ".")
    return template.format(
        criterion=v["criterion"],
        default=_num(v["default_t"], 2),
        rec=_num(v["recommended_t"], 2),
        min_hits=v["min_hits"],
    )


def _point_table(points: Sequence[dict | None]) -> list[str]:
    out = [
        "| t | eligible | (a) hits | (a) precision | (a) recall | (c) hits | (c) correct | "
        "(c) precision | (c) recall |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for p in points:
        if p is None:
            continue
        out.append(
            f"| {_num(p['t'], 2)} | {'yes' if p['eligible'] else 'no'} | {p['hits_a']} | "
            f"{_num(p['precision_a'])} | {_num(p['recall_a'])} | {p['hits_c']} | {p['correct_c']} | "
            f"{_num(p['precision_c'])} | {_num(p['recall_c'])} |"
        )
    return out


def _savings_table(rows: Sequence[dict]) -> list[str]:
    out = [
        "| r | repeats (exact + paraphrase) | hit rate | false-hit rate | tier blocks | "
        "cost / 1000 | router only / 1000 | saving vs frontier | extra saving vs router | "
        "quality | router-only quality |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        out.append(
            f"| {row['r']:.3f} | {row['repeats_exact']} + {row['repeats_paraphrase']} | "
            f"{_pct(row['hit_rate'])} | {_pct(row['false_hit_rate'])} | {row['tier_blocked']} | "
            f"{_usd(row['cost_per_1000'])} | {_usd(row['router_only_cost_per_1000'])} | "
            f"{_pct(row['saving_vs_frontier'])} | {_pct(row['extra_saving_vs_router'])} | "
            f"{_num(row['quality'])} | {_num(row['router_only_quality'])} |"
        )
    return out


def _labels_lines(data: dict) -> list[str]:
    out = ["## Human checks (descriptive; never adjust the verdict)", ""]
    validation = data["paraphrase_validation"]
    if validation == PENDING:
        out.append('- Paraphrase sample (40 pairs, "¿B pide lo mismo que A?"): pendiente.')
    else:
        out.append(
            f"- Paraphrase sample: {validation['labeled']} of {validation['sample']} labeled; "
            f"sí {validation['si']}, no {validation['no']}, ? {validation['unsure']}; faithful rate "
            f"{_num(validation['faithful_rate'])} (sí / (sí + no))."
        )
    human = data["neighbors"]["human_labels"]
    if human == PENDING:
        out.append('- Neighbor pairs (b) ("¿Una respuesta a A sirve para B?"): pendiente.')
    else:
        agreement = ", ".join(f"t = {t}: {_num(a)}" for t, a in human["agreement"].items())
        out.append(
            f"- Neighbor pairs (b): {human['labeled']} of {human['pairs']} labeled, {human['decided']} "
            f"sí/no; agreement of the cache's decision (serve when cosine >= t) with the label: "
            f"{agreement}."
        )
    return out + [""]


def render_markdown(data: dict) -> str:
    """``report.md`` from the report as written to ``report.json``."""
    pre = data["preregistration"]
    production = data["models"]["production"]
    out = [
        "# Semantic cache measurement — v1",
        "",
        "Generated by `make cache-eval` from the data in this directory; the definitions, criterion",
        "and verdict rule are fixed in `preregistration.md` (with its amendments). Point estimates",
        "only; no confidence intervals (declared). Every lookup goes through the gateway's own",
        "`SemanticCacheService` over an in-memory Qdrant.",
        "",
        "## Verdict (pre-registered)",
        "",
        f"Production embedding `{production['name']}` (digest `{production['digest'][:12]}`). "
        f"Criterion: precision >= {pre['criterion']} on both (a) PAWS-X and (c) the paraphrase replay; "
        f"a grid point counts only with >= {pre['min_hits']} hits in each set; tier rule {pre['tier_rule']}.",
        "",
        _verdict_line(pre),
        "",
        *_point_table([pre["at_default"], pre["at_recommended"]]),
        "",
        f"(c) counts {pre['valid_paraphrases']} valid paraphrases (of {pre['registered_paraphrases']} "
        f"registered) and the {pre['leave_one_out_originals']} originals leave-one-out; a hit of a "
        "leave-one-out original is always a false hit.",
    ]
    production_paws = data["pawsx"][production["key"]]
    precisions_a = [p["precision_a"] for p in pre["grid"] if p["precision_a"] is not None]
    if precisions_a:
        out += [
            "",
            f"In (a), {production_paws['paraphrases']} of {production_paws['pairs']} pairs are "
            f"paraphrases ({_num(production_paws['paraphrases'] / production_paws['pairs'])}), and "
            f"(a)'s precision stays between {_num(min(precisions_a))} and {_num(max(precisions_a))} "
            "over the grid: PAWS-X pairs are adversarial word swaps of the same words, which this "
            "embedding scores as near-identical whether or not the meaning changed.",
        ]
    if pre["fewer_than_150_valid"]:
        out.append(f"**Fewer than 150 paraphrases are valid ({pre['valid_paraphrases']}).**")
    out += ["", "### Grid (production model)", "", *_point_table(pre["grid"]), ""]

    out += ["## (a) PAWS-X `es` test", ""]
    for key, block in data["pawsx"].items():
        out += [
            f"`{MODEL_KEYS.get(key, key)}`: {block['pairs']} pairs, {block['paraphrases']} "
            "labeled paraphrases.",
            "",
            "| t | hits | precision | recall | F0.5 |",
            "|---|---|---|---|---|",
        ]
        out += [
            f"| {_num(r['t'], 2)} | {r['hits']} | {_num(r['precision'])} | {_num(r['recall'])} | "
            f"{_num(r['f05'])} |"
            for r in block["curve"]
        ]
        out.append("")

    para = data["paraphrases"]
    out += [
        "## (c) Paraphrase replay",
        "",
        f"{para['valid']} valid paraphrases of {para['registered']} registered; dropped: "
        + ", ".join(f"{kind} {n}" for kind, n in para["dropped_by_kind"].items())
        + ". Valid per task: "
        + ", ".join(f"{task} {n}" for task, n in para["valid_by_task"].items())
        + ".",
        "",
        "Each paraphrase is routed on its own vector: its tier is the same as its original's for "
        f"{para['tier_vs_original']['same']}, higher for {para['tier_vs_original']['higher']}, lower "
        f"for {para['tier_vs_original']['lower']}.",
        "",
    ]
    for key in data["pawsx"]:
        block = para[key]
        cos = block["own_original_cosine"]
        out += [
            f"`{MODEL_KEYS.get(key, key)}`: cosine of a paraphrase to its own original: min "
            f"{_num(cos.get('min'))}, p25 {_num(cos.get('p25'))}, median {_num(cos.get('median'))}, "
            f"p75 {_num(cos.get('p75'))}, max {_num(cos.get('max'))}.",
            "",
            "| t | hits (paraphrase + leave-one-out) | correct | false | precision | recall |",
            "|---|---|---|---|---|---|",
        ]
        out += [
            f"| {_num(r['t'], 2)} | {r['paraphrase_hits']} + {r['loo_hits']} | {r['correct_hits']} | "
            f"{r['false_hits']} | {_num(r['precision'])} | {_num(r['recall'])} |"
            for r in block["curve"]
        ]
        out += ["", "With the tier rule on (each query looked up with its own tier's rank):", ""]
        out += [
            f"- t = {t}: correct {m['correct_hits']}, false {m['false_hits']}, tier blocks "
            f"{m['tier_blocked']}, precision {_num(m['precision'])}, recall {_num(m['recall'])}."
            for t, m in block["tier_rule_on"].items()
        ]
        out.append("")

    savings = data["savings"]
    trace = savings["trace"]
    out += [
        "## Saving vs repetition rate",
        "",
        f"A trace of {trace['length']} requests per rate r (seed {trace['seed']}), served in order "
        "through a gateway cache that starts empty, tier rule on. Exactly round(r × 1000) requests, "
        "at seeded positions, nested across rates (the repeats of a lower rate are among those of "
        "a higher one), repeat a prompt asked earlier: half exact repeats (same text and vector), "
        "half its valid paraphrase. The "
        "other requests are new Spanish corpus prompts, each at most once (at r = 0 every one of "
        "the 1000 is sent once). A first version of the trace drew each request's repeat "
        "independently; with this seed that gave 61 repeats at r = 0.037 (a rate the trace no longer "
        "uses) instead of 37, so the count is now fixed and the rate on the axis is the rate in the "
        "trace. A miss is served at "
        "the request's router tier "
        "(target 0.95) at the cost captured for that prompt and tier "
        "(`src/nebula/data/router_replay_v1.json`; local = 0) and stored; a hit costs 0. A correct hit "
        "keeps the quality of the cached answer's tier for that prompt "
        "(`benchmarks/ground-truth/v1/tiers.jsonl`); a false hit is worth 0. Costs in USD per 1000 "
        "requests.",
        "",
    ]
    for key in data["pawsx"]:
        for t, block in savings[key].items():
            out += [
                f"### `{MODEL_KEYS.get(key, key)}`, t = {t}",
                "",
                *_savings_table(block["curve"]),
                "",
            ]
            out += ["Cited repetition rates:", ""]
            out += [
                f"- {CITED_RATE_SOURCES.get(name, name)} (r = {row['r']}): cost "
                f"{_usd(row['cost_per_1000'])} per 1000, "
                f"{_pct(row['saving_vs_frontier'])} below all-frontier, "
                f"{_pct(row['extra_saving_vs_router'])} below the router alone, quality "
                f"{_num(row['quality'])} (router alone {_num(row['router_only_quality'])})."
                for name, row in block["cited"].items()
            ]
            out.append("")

    c = savings["consistency"]
    out += [
        "### Consistency with the router's cited cost",
        "",
        f"- The shipped router at target {c.get('target', TIER_TARGET)} on the whole corpus "
        f"({c.get('corpus_prompts', '—')} prompts) costs USD {_usd(c['corpus_cost_per_1000'])} per 1000; "
        f"the thesis cites the nested estimate, USD {_usd(c['cited_cost_per_1000'])} (difference "
        f"{c['corpus_minus_cited']:+.4f}, within 0.01: the shipped weights are refit on all data, the "
        "nested estimate routes each fold with weights and thresholds chosen without it).",
        f"- The trace serves only the Spanish prompts, which cost more to route: the shipped router "
        f"costs USD {_usd(c['spanish_cost_per_1000'])} per 1000 on them (the nested estimate for "
        f"Spanish is USD {_usd(c.get('cited_spanish_cost_per_1000'))}). At r = 0 the trace's "
        f"router-only cost equals it exactly (checked when the report is built).",
    ]
    if c.get("r0_cost_per_1000"):
        out.append(
            "- At r = 0 the cache still serves some requests: distinct prompts close enough to an "
            "earlier one are false hits ("
            + ", ".join(
                f"t = {t}: false hits {n}, cost {_usd(c['r0_cost_per_1000'][t])}"
                for t, n in c["r0_false_hits"].items()
            )
            + ")."
        )
    out.append("")

    neighbors = data["neighbors"]
    out += [
        "## (b) Corpus neighbors (descriptive)",
        "",
        f"{neighbors['pairs']} pairs of distinct Spanish prompts at production cosine >= 0.85:",
        "",
    ]
    out += [
        f"- [{b['from']:.2f}, {'…' if b['to'] is None else format(b['to'], '.2f')}): {b['pairs']} pairs"
        for b in neighbors["bands"]
    ]
    if "nomic_v2_bands" in neighbors:
        out += ["", "Under `nomic-embed-text-v2-moe`, pairs among the same 1000 prompts:", ""]
        out += [
            f"- [{b['from']:.2f}, {'…' if b['to'] is None else format(b['to'], '.2f')}): {b['pairs']} pairs"
            for b in neighbors["nomic_v2_bands"]
        ]
    out.append("")
    out += _labels_lines(data)

    for s in data["models"]["sensitivity"]:
        out += [
            f"## Sensitivity: `{s['name']}` (does not enter the verdict)",
            "",
            "The same rule applied to this model would give "
            + _verdict_line(s["verdict"], consequence=False)
            + " It changes nothing in the product.",
            "",
            *_point_table([s["at_default"], s["at_recommended"]]),
            "",
        ]

    out += [
        "## Limitations",
        "",
        "- **The validity rule has a known blind spot.** It keeps any rewrite whose length is 0.5 to "
        "2.0 times the original's, so it cannot see what a rewrite says. An automated review (an AI "
        "code-review agent, not a human rater) read about 75 of the valid paraphrases and flagged 4 "
        "that answer the prompt instead of rewriting it, 1 corrupted with CJK characters, and 2 code "
        "prompts whose rewrite renamed the identifier the test asserts on; these counts are not a "
        "human check. They stay in (c) because the rule was fixed before the rewrites were seen "
        "and is not changed after. Such a rewrite that misses its original lowers the replay's "
        "recall; one that still matches its original counts as a correct hit although the cached "
        "answer may not serve it. The 40-pair human check measures how faithful the set is.",
        "- **Router tiers are in-sample.** The shipped router's weights were fit on these prompts' "
        "labels, so the router-only quality in the savings table is optimistic for the Spanish set; "
        "the cache's effect is read as the change from that baseline, not as an absolute quality.",
        "- A paraphrase is priced at its original's captured cost on the same tier, and is assumed to "
        "need the same answer (the human check tests that assumption).",
        "- A hit on a different corpus prompt is a false hit with quality 0, even when the two prompts "
        "are near-identical (the MBPP pair `es:code-0113` / `es:code-0138`, disclosed in the "
        "pre-registration).",
        "- One tenant, single-turn requests, entries never expire within a trace: the cache's "
        "context key and TTL never block a hit here.",
        "- Scores are Qdrant's (single-precision vectors); PAWS-X uses the committed cosines.",
        "- `nomic-embed-text` is an English model; the multilingual model is reported as sensitivity.",
        "",
        "## Provenance",
        "",
        *_provenance_lines(data["provenance"]),
        "",
    ]
    return "\n".join(out)


def _provenance_lines(provenance: dict) -> list[str]:
    differing = provenance.get("files_differing_from_git_sha")
    if differing is None:
        state = "whether any input differed from it is unknown (git was not available)"
    elif differing:
        state = "these inputs differed from it when the report was generated: " + ", ".join(
            f"`{path}`" for path in differing
        )
    else:
        state = "no tracked input differed from it when the report was generated"
    return [
        f"Git commit checked out at generation: `{provenance.get('git_sha', 'unknown')}`; {state}. "
        "The SHA-256 of each file in report.json is the authority (`provenance.files`, with the "
        "untracked corpus vectors too), and `provenance.vectors` hashes the vectors used."
    ]


# --- Loading and the command ----------------------------------------------------------------------

DATA_DIR = Path("benchmarks/cache/v1")
LABELS_FILE = "human-es-1.jsonl"
INPUT_FILES: tuple[Path, ...] = (
    DATA_DIR / "preregistration.md",
    DATA_DIR / "pawsx" / "pairs.jsonl",
    DATA_DIR / "neighbors" / "pairs.jsonl",
    DATA_DIR / "paraphrases" / "paraphrases.jsonl",
    DATA_DIR / "paraphrases" / "dropped.jsonl",
    DATA_DIR / "paraphrases" / "sample.jsonl",
    CORPUS_PATH,
    TIERS_PATH,
    ROUTER_PATH,
    ROUTER_REPLAY_PATH,
    PRODUCTION_VECTORS_PATH,
    Path("scripts/cache_eval/replay.py"),
    Path("scripts/cache_eval/report.py"),
    Path("scripts/cache_eval/embed.py"),
    Path("src/nebula/services/semantic_cache_service.py"),
    Path("src/nebula/services/learned_router.py"),
)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout


def _git_sha() -> str:
    out = _git("rev-parse", "HEAD")
    return "unknown" if out is None else out.strip()


def _files_differing_from_head(files: Sequence[Path]) -> list[str] | None:
    """Tracked inputs that were modified or new against the checked-out commit (None if unknown)."""
    out = _git("status", "--porcelain", "--untracked-files=all", "--", *map(str, files))
    if out is None:
        return None
    return sorted(line[3:] for line in out.splitlines() if line.strip())


def provenance(files: Sequence[Path], vectors: Mapping[str, Sequence[Sequence[float]]]) -> dict:
    """Git commit and which inputs differed from it, SHA-256 of each input file, and of each set
    of vectors (canonical JSON). The file hashes are the authority; the commit is context."""
    return {
        "git_sha": _git_sha(),
        "files_differing_from_git_sha": _files_differing_from_head(files),
        "files": {str(path): _sha256(path.read_bytes()) for path in files},
        "vectors": {
            name: _sha256(json.dumps([list(v) for v in vs]).encode("utf-8"))
            for name, vs in vectors.items()
        },
        "qdrant_client": importlib.metadata.version("qdrant-client"),
    }


def load_inputs() -> Inputs:
    """The committed data, the corpus vectors, both models' vectors (cached Ollama embeddings)
    and the router's tiers at the target."""
    if not PRODUCTION_VECTORS_PATH.exists():
        raise SystemExit(
            f"{PRODUCTION_VECTORS_PATH} is missing: run `python -m scripts.router.embed` (or copy it "
            "from a checkout that has it)."
        )
    corpus = sorted(read_rows(CORPUS_PATH, PromptRow), key=lambda row: row.prompt_id)
    stored = json.loads(PRODUCTION_VECTORS_PATH.read_text())
    router = LearnedRouterModel.from_file(ROUTER_PATH)
    replay_payload = json.loads(ROUTER_REPLAY_PATH.read_text())
    paraphrase_rows = _read_jsonl(DATA_DIR / "paraphrases" / "paraphrases.jsonl")

    v1_originals = [stored[f"es:{row.prompt_id}"] for row in corpus]
    texts = [row["paraphrase"] for row in paraphrase_rows]
    v1_paraphrases = embed.embed_texts(texts, model=MODEL_KEYS["nomic_v1"])
    v2_originals = embed.embed_texts([row.prompt for row in corpus], model=MODEL_KEYS["nomic_v2"])
    v2_paraphrases = embed.embed_texts(texts, model=MODEL_KEYS["nomic_v2"])

    def tier(vector: list[float]) -> str:
        return router.choose(vector, TIER_TARGET).tier

    originals = [
        Original(row.prompt_id, row.prompt, tier(v1), {"nomic_v1": v1, "nomic_v2": v2})
        for row, v1, v2 in zip(corpus, v1_originals, v2_originals, strict=True)
    ]
    paraphrases = [
        Paraphrase(row["prompt_id"], row["paraphrase"], tier(v1), {"nomic_v1": v1, "nomic_v2": v2})
        for row, v1, v2 in zip(paraphrase_rows, v1_paraphrases, v2_paraphrases, strict=True)
    ]
    neighbor_labels_path = DATA_DIR / "neighbors" / "labels" / LABELS_FILE
    paraphrase_labels_path = DATA_DIR / "paraphrases" / "labels" / LABELS_FILE
    labels = [p for p in (neighbor_labels_path, paraphrase_labels_path) if p.exists()]
    return Inputs(
        originals=originals,
        paraphrases=paraphrases,
        paraphrase_rows=paraphrase_rows,
        dropped=_read_jsonl(DATA_DIR / "paraphrases" / "dropped.jsonl"),
        pawsx=_read_jsonl(DATA_DIR / "pawsx" / "pairs.jsonl"),
        neighbors=_read_jsonl(DATA_DIR / "neighbors" / "pairs.jsonl"),
        sample=_read_jsonl(DATA_DIR / "paraphrases" / "sample.jsonl"),
        neighbor_labels=read_labels(neighbor_labels_path),
        paraphrase_labels=read_labels(paraphrase_labels_path),
        prices=load_prices(replay_payload["rows"], _read_jsonl(TIERS_PATH)),
        router_check=router_only_check(
            router=router, replay_payload=replay_payload, vectors=stored
        ),
        provenance=provenance(
            [*INPUT_FILES, *labels],
            {
                "nomic_v1/originals": v1_originals,
                "nomic_v1/paraphrases": v1_paraphrases,
                "nomic_v2/originals": v2_originals,
                "nomic_v2/paraphrases": v2_paraphrases,
            },
        ),
    )


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    data = json.loads(dumps(asyncio.run(build(load_inputs()))))
    (DATA_DIR / "report.json").write_text(dumps(data), encoding="utf-8")
    (DATA_DIR / "report.md").write_text(render_markdown(data), encoding="utf-8")
    pre = data["preregistration"]
    print(
        f"verdict: {pre['verdict']}, recommended t: {pre['recommended_t']} "
        f"-> {DATA_DIR / 'report.json'}, {DATA_DIR / 'report.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
