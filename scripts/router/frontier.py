"""Cost/quality of a routing, the sweep that traces the learned router's
frontier, and the baselines it has to beat.

Quality is the share of prompts served by a tier whose answer can replace the
frontier model's, per the phase-2 labels; the frontier tier is the reference,
so it counts as sufficient by definition. Cost is what the answer actually
cost at capture time; the local model costs nothing at the margin.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
from math import ceil

import numpy as np

from scripts.router.data import Example

HEURISTIC_HINTS = ("analyze", "reason", "contract", "debug", "architecture", "design")
GRID = np.linspace(0.0, 1.0, 51)


def route(p_local: np.ndarray, p_economy: np.ndarray, tau_local: float, tau_economy: float) -> list[str]:
    tiers = np.where(p_local >= tau_local, "local", np.where(p_economy >= tau_economy, "economy", "frontier"))
    return tiers.tolist()


def _arrays(examples: Sequence[Example]) -> dict[str, np.ndarray]:
    return {
        "local_ok": np.array([e.local_ok for e in examples], dtype=float),
        "economy_ok": np.array([e.economy_ok for e in examples], dtype=float),
        "ce": np.array([e.cost_economy for e in examples]),
        "cf": np.array([e.cost_frontier for e in examples]),
    }


def evaluate(tiers: Sequence[str], examples: Sequence[Example]) -> tuple[float, float]:
    a = _arrays(examples)
    t = np.asarray(tiers)
    cost = np.where(t == "economy", a["ce"], np.where(t == "frontier", a["cf"], 0.0))
    quality = np.where(t == "local", a["local_ok"], np.where(t == "economy", a["economy_ok"], 1.0))
    return float(cost.mean()), float(quality.mean())


def sweep(
    p_local: np.ndarray, p_economy: np.ndarray, examples: Sequence[Example], grid: np.ndarray = GRID
) -> list[dict]:
    points = []
    for tau_l in grid:
        for tau_e in grid:
            tiers = route(p_local, p_economy, float(tau_l), float(tau_e))
            cost, quality = evaluate(tiers, examples)
            points.append({
                "tau_local": float(tau_l), "tau_economy": float(tau_e), "cost": cost, "quality": quality,
                "share": {t: tiers.count(t) / len(tiers) for t in ("local", "economy", "frontier")},
            })
    return points


def pareto(points: Sequence[dict]) -> list[dict]:
    ordered = sorted(points, key=lambda p: (p["cost"], -p["quality"]))
    front: list[dict] = []
    best = -1.0
    for p in ordered:
        if p["quality"] > best:
            front.append(p)
            best = p["quality"]
    return front


def cost_at_quality(front: Sequence[dict], q: float) -> float | None:
    feasible = [p["cost"] for p in front if p["quality"] >= q]
    return min(feasible) if feasible else None


def heuristic_tiers(examples: Sequence[Example], premium_tier: str = "frontier") -> list[str]:
    out = []
    for e in examples:
        low = ceil(len(e.text) / 4) < 500
        keyword = any(h in e.text.lower() for h in HEURISTIC_HINTS)
        out.append("local" if low and not keyword else premium_tier)
    return out


def oracle_tiers(examples: Sequence[Example]) -> list[str]:
    out = []
    for e in examples:
        if e.local_ok:
            out.append("local")
        elif e.economy_ok and e.cost_economy <= e.cost_frontier:
            out.append("economy")
        else:
            out.append("frontier")
    return out


def corner_points(examples: Sequence[Example]) -> dict[str, tuple[float, float]]:
    n = len(examples)
    return {
        "all_local": evaluate(["local"] * n, examples),
        "all_economy": evaluate(["economy"] * n, examples),
        "all_frontier": evaluate(["frontier"] * n, examples),
        "oracle": evaluate(oracle_tiers(examples), examples),
    }


def random_cost_at_quality(examples: Sequence[Example], q: float) -> float | None:
    """Cheapest random mixture of the three single-tier policies reaching q."""
    corners = corner_points(examples)
    pts = [corners[k] for k in ("all_local", "all_economy", "all_frontier")]
    best: float | None = None
    for cost, quality in pts:
        if quality >= q:
            best = cost if best is None else min(best, cost)
    for (c1, q1), (c2, q2) in combinations(pts, 2):
        (ca, qa), (cb, qb) = sorted([(c1, q1), (c2, q2)], key=lambda p: p[1])
        if qa < q <= qb:
            t = (q - qa) / (qb - qa)
            mix = (1 - t) * ca + t * cb
            best = mix if best is None else min(best, mix)
    return best
