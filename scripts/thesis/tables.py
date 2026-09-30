"""Regenerate every generated block of the thesis from the committed reports.

    python -m scripts.thesis.tables [--check]

Reads only what is versioned under ``benchmarks/``: no network, no training.
``--check`` writes nothing and exits 1 when a block is stale.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.metric_validation import rubric
from scripts.thesis import blocks

THESIS_DIR = Path("docs/tfc/tesis")
GT_ROOT = Path("benchmarks/ground-truth/v1")
ROUTER = Path("benchmarks/router/v1")
RESULTS = Path("benchmarks/results")
METRIC = Path("benchmarks/metric-validation")
BASELINE_RUNS = ("20260819T225557Z", "20260819T225703Z", "20260819T225713Z")
POLICY_NAMES = {
    "all_local": "todo local (qwen2.5:7b)",
    "all_economy": "todo económico (claude-haiku-4.5)",
    "all_frontier": "todo frontier (gpt-4.1)",
    "oracle": "oráculo",
    "heuristic_premium_frontier": "heurística de dos reglas → frontier",
    "heuristic_premium_economy": "heurística de dos reglas → económico",
}
LABEL_RULES = {"tiers.R1_unanimous.jsonl": "R1 unanimidad", "tiers.R2_majority.jsonl": "R2 mayoría"}
FRONTIER_LEVELS = (0.80, 0.85, 0.90, 0.95, 0.98)


def _json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing report {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f} %"


def _usd(cost_per_prompt: float) -> str:
    return f"{cost_per_prompt * 1000:.2f}"


def baseline_savings(runs_dir: Path) -> str:
    parts, served = [], set()
    for run_id in BASELINE_RUNS:
        s = _json(runs_dir / run_id / "report.json")["summary"]
        avoided, spent = s["estimated_premium_cost_avoided"], s["estimated_premium_cost"]
        parts.append(f"{_pct(avoided / (spent + avoided))} (corrida {run_id})")
        routes = s["route_distribution"]
        served.add((s["passed"], s["total_requests"], routes.get("local", 0) + routes.get("cache", 0)))
    if len(served) != 1:
        raise ValueError(f"baseline runs disagree on scenarios or routes: {sorted(served)}")
    passed, total, cheap = served.pop()
    return (f"Línea de base (heurística de dos reglas, {total} escenarios, 2026-08-19): "
            f"{', '.join(parts)} de gasto premium evitado. En cada corrida pasaron "
            f"{passed}/{total} escenarios y {cheap} de {total} pedidos se sirvieron por el modelo "
            f"local o por el caché. Estas corridas no miden la calidad de lo que se sirvió.")


def _labels(root: Path, rater: str) -> dict[str, str]:
    path = root / "labels" / f"{rater}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"missing labels {path}")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["pair_id"]: row["grade"] for row in rows}


def metric_validation(root: Path) -> str:
    r = _json(root / "report.json")
    raters = _json(root / "raters.json")
    chosen = r["chosen_prefix"]
    natural = next(p for p in r["prefix_sweep_natural"] if p["prefix"] == chosen)
    ci = natural["auc_ci"]
    scale = {s["kind"]: s for s in r["scale_by_kind"]}
    labels = {rater: _labels(root, rater) for rater in r["raters"]}
    shared = sorted(labels[r["reference_rater"]])
    rates = []
    for rater in r["raters"]:
        info = raters[rater]
        who = "el lector humano" if info["kind"] == "human" else info["note"].split(",")[0]
        subs = sum(rubric.is_substitutable(labels[rater][p]) for p in shared)
        rates.append(f"{who} {_pct(subs / len(shared), 0)}")
    return (f"Sobre {natural['pairs']} pares en inglés con nota humana, la similitud coseno del "
            f"embedding (prefijo `{chosen}`) separó las respuestas sustituibles de las que no lo eran "
            f"con AUC {natural['auc']:.2f} (IC 95 % {ci['low']:.2f}–{ci['high']:.2f}), por debajo "
            f"del azar. La mediana del coseno entre una respuesta local y una premium fue "
            f"{scale['local_vs_premium']['median']:.3f}, prácticamente la misma que entre dos modelos "
            f"premium ({scale['premium_vs_premium']['median']:.3f}): en ese rango la métrica está "
            f"saturada y no distingue calidad. En esos mismos pares, la proporción juzgada sustituible "
            f"fue {', '.join(rates)}.")


def router_fixed_policies(report: dict) -> str:
    rows = ["| Política | Costo (USD cada 1000 prompts) | Calidad |", "|---|---|---|"]
    for key, label in POLICY_NAMES.items():
        p = report["baselines"][key]
        rows.append(f"| {label} | {_usd(p['cost'])} | {p['quality']:.3f} |")
    n = report["nested"]["0.95"]
    rows.append(f"| router aprendido, objetivo 0.95 (estimación anidada) | {_usd(n['cost'])} | "
                f"{n['quality']:.3f} |")
    return "\n".join(rows)


def router_sensitivity(report: dict) -> str:
    levels = sorted(report["learned"]["cost_at"], key=float)
    rows = ["| Regla de etiquetado | " + " | ".join(f"calidad ≥ {float(q):.2f}" for q in levels)
            + " | todo frontier |", "|---|" + "---|" * (len(levels) + 1)]
    for key, v in report["sensitivity"].items():
        rows.append(f"| {LABEL_RULES.get(key, key)} | "
                    + " | ".join(_usd(v["cost_at"][q]) for q in levels)
                    + f" | {_usd(v['all_frontier_cost'])} |")
    main = report["learned"]["cost_at"]
    rows.append("| R3 media ordinal (elegida) | " + " | ".join(_usd(main[q]) for q in levels)
                + f" | {_usd(report['baselines']['all_frontier']['cost'])} |")
    return "\n".join(rows)


def router_latency(latency: dict) -> str:
    rows = ["| Modelo | Mediana (s) | p90 (s) | Respuestas |", "|---|---|---|---|"]
    for v in sorted(latency.values(), key=lambda v: v["median_s"]):
        rows.append(f"| {v['model']} | {v['median_s']:.1f} | {v['p90_s']:.1f} | {v['n']} |")
    return "\n".join(rows)


def router_frontier_points(report: dict) -> str:
    pareto = report["learned"]["pareto"]
    rows = ["| Calidad mínima | τ local | τ económico | Costo (USD cada 1000) | Local | Económico | "
            "Frontier |", "|---|---|---|---|---|---|---|"]
    for q in FRONTIER_LEVELS:
        p = min((p for p in pareto if p["quality"] >= q), key=lambda p: p["cost"])
        s = p["share"]
        rows.append(f"| {q:.2f} | {p['tau_local']:.2f} | {p['tau_economy']:.2f} | {_usd(p['cost'])} | "
                    f"{_pct(s['local'], 0)} | {_pct(s['economy'], 0)} | {_pct(s['frontier'], 0)} |")
    return "\n".join(rows)


def render_all() -> dict[str, str]:
    from scripts.ground_truth import report as gt_report
    from scripts.router import train

    summary = gt_report.summarise(GT_ROOT)
    router = _json(ROUTER / "report.json")
    latency = _json(ROUTER / "latency.json")
    return {
        "corpus-fase2": gt_report.thesis_corpus(summary),
        "judges-fase2": gt_report.thesis_judges(summary),
        "router-fase3": train.thesis_block(router),
        "baseline-savings": baseline_savings(RESULTS),
        "metric-validation": metric_validation(METRIC),
        "router-fixed-policies": router_fixed_policies(router),
        "router-sensitivity": router_sensitivity(router),
        "router-latency": router_latency(latency),
        "router-frontier-points": router_frontier_points(router),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if stale")
    args = parser.parse_args(argv)
    try:
        stale = blocks.apply(render_all(), THESIS_DIR, write=not args.check)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"thesis-tables: {exc}", file=sys.stderr)
        return 2
    if args.check and stale:
        print("stale GEN blocks: " + ", ".join(stale), file=sys.stderr)
        return 1
    print(("updated: " + ", ".join(stale)) if stale else "thesis tables up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
