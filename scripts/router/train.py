"""Train the learned router, trace its frontier, and write the artifact and report.

    python -m scripts.router.train

Everything reported comes from out-of-fold predictions (5 folds grouped by
prompt). The shipped weights are refit on all data; the operating points they
carry are the out-of-fold ones, so a tenant's quality target is backed by
held-out evidence rather than by the training fit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.ground_truth import report as gt_report
from scripts.router import cv, data, embed, frontier, knn, logreg

PREFIX_MARGIN = 0.02
TARGETS = ("local", "economy")
MAIN_LABELS = "tiers.R3_ordinal_mean.jsonl"
SENSITIVITY_LABELS = ("tiers.R1_unanimous.jsonl", "tiers.R2_majority.jsonl")
QUALITY_LEVELS = (0.85, 0.90, 0.95)
DEFAULT_TARGET = 0.95
ARTIFACT = Path("src/nebula/data/learned_router_v1.json")
OUT = Path("benchmarks/router/v1")
THESIS = Path("docs/tfc/tesis/06-evaluacion.md")


def choose_prefix(aucs: dict[str, float]) -> str:
    return "classification" if aucs["classification"] - aucs["none"] > PREFIX_MARGIN else "none"


def operating_points(front: list[dict]) -> list[dict]:
    return [
        {"tau_local": p["tau_local"], "tau_economy": p["tau_economy"],
         "quality": p["quality"], "cost_per_prompt": p["cost"]}
        for p in front
    ]


def artifact(*, weights: dict, lambdas: dict, prefix: str, points: list[dict], labels: dict) -> dict:
    return {
        "version": 1,
        "label": "v1",
        "embedding_model": embed.EMBEDDING_MODEL,
        "prefix": prefix,
        "lambda": lambdas,
        "labels": labels,
        "models": {
            name: {"weights": [float(v) for v in w], "bias": float(b)} for name, (w, b) in weights.items()
        },
        "operating_points": points,
    }


def _labels(examples: list[data.Example], target: str) -> np.ndarray:
    return np.array([e.local_ok if target == "local" else e.economy_ok for e in examples], dtype=float)


def _matrix(examples: list[data.Example], prefix: str) -> np.ndarray:
    vectors = embed.load_embeddings(prefix)
    return np.array([vectors[e.key] for e in examples])


def _oof(examples, X, fold_of, lambdas=None):
    out, lam_used, losses = {}, {}, {}
    for target in TARGETS:
        y = _labels(examples, target)
        if lambdas is None:
            lam, losses[target] = cv.choose_lambda(X, y, fold_of)
        else:
            lam = lambdas[target]
        lam_used[target] = lam
        out[target] = cv.out_of_fold(X, y, fold_of, lam)
    return out, lam_used, losses


def _aucs(examples, probs) -> dict:
    result = {}
    for target in TARGETS:
        y = _labels(examples, target)
        result[target] = {"all": cv.auc(y, probs[target])}
        for lang in ("es", "en"):
            mask = np.array([e.lang == lang for e in examples])
            result[target][lang] = cv.auc(y[mask], probs[target][mask])
    return result


def _summary_at(front, q):
    feasible = [p for p in front if p["quality"] >= q]
    return min(feasible, key=lambda p: p["cost"]) if feasible else None


def _frontier_block(examples, probs) -> dict:
    points = frontier.sweep(probs["local"], probs["economy"], examples)
    front = frontier.pareto(points)
    return {"pareto": front, "cost_at": {str(q): frontier.cost_at_quality(front, q) for q in QUALITY_LEVELS}}


def run(root: Path = data.GROUND_TRUTH) -> dict:
    examples = data.load_examples(root, MAIN_LABELS)
    fold_of = cv.folds(examples)

    prefix_results = {}
    for prefix in embed.PREFIXES:
        X = _matrix(examples, prefix)
        probs, lambdas, losses = _oof(examples, X, fold_of)
        aucs = _aucs(examples, probs)
        prefix_results[prefix] = {"lambdas": lambdas, "log_loss": losses, "auc": aucs,
                                  "mean_auc": float(np.mean([aucs[t]["all"] for t in TARGETS]))}
    prefix = choose_prefix({p: r["mean_auc"] for p, r in prefix_results.items()})
    lambdas = prefix_results[prefix]["lambdas"]
    X = _matrix(examples, prefix)
    probs, _, _ = _oof(examples, X, fold_of, lambdas)
    main = _frontier_block(examples, probs)

    knn_probs = {t: knn.oof_probabilities(X, _labels(examples, t), fold_of) for t in TARGETS}
    knn_block = _frontier_block(examples, knn_probs)
    knn_block["auc"] = _aucs(examples, knn_probs)

    corners = frontier.corner_points(examples)
    baselines = {name: {"cost": c, "quality": q} for name, (c, q) in corners.items()}
    for tier in ("frontier", "economy"):
        c, q = frontier.evaluate(frontier.heuristic_tiers(examples, premium_tier=tier), examples)
        baselines[f"heuristic_premium_{tier}"] = {"cost": c, "quality": q}
    random_at = {str(q): frontier.random_cost_at_quality(examples, q) for q in QUALITY_LEVELS}
    for name in ("heuristic_premium_frontier", "heuristic_premium_economy"):
        q = baselines[name]["quality"]
        baselines[name]["learned_cost_at_same_quality"] = frontier.cost_at_quality(main["pareto"], q)
        baselines[name]["random_cost_at_same_quality"] = frontier.random_cost_at_quality(examples, q)

    by_lang = {}
    point = _summary_at(main["pareto"], DEFAULT_TARGET)
    if point is not None:
        tiers = frontier.route(probs["local"], probs["economy"], point["tau_local"], point["tau_economy"])
        for lang in ("es", "en"):
            idx = [i for i, e in enumerate(examples) if e.lang == lang]
            sub = [examples[i] for i in idx]
            c, q = frontier.evaluate([tiers[i] for i in idx], sub)
            share = {t: sum(1 for i in idx if tiers[i] == t) / len(idx) for t in ("local", "economy", "frontier")}
            by_lang[lang] = {"cost": c, "quality": q, "share": share}

    sensitivity = {}
    for labels_file in SENSITIVITY_LABELS:
        ex_s = data.load_examples(root, labels_file)
        probs_s, _, _ = _oof(ex_s, X, fold_of, lambdas)
        block = _frontier_block(ex_s, probs_s)
        sensitivity[labels_file] = {
            "cost_at": block["cost_at"],
            "all_frontier_cost": frontier.corner_points(ex_s)["all_frontier"][0],
            "random_at": {str(q): frontier.random_cost_at_quality(ex_s, q) for q in QUALITY_LEVELS},
        }

    weights = {}
    for target in TARGETS:
        weights[target] = logreg.fit(X, _labels(examples, target), lambdas[target])
    labels_path = root / MAIN_LABELS
    raw = artifact(
        weights=weights, lambdas=lambdas, prefix=prefix, points=operating_points(main["pareto"]),
        labels={"file": MAIN_LABELS, "sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest()},
    )

    return {
        "examples": len(examples),
        "folds": 5,
        "prefix": {"chosen": prefix, "margin": PREFIX_MARGIN, "results": prefix_results},
        "learned": {"auc": _aucs(examples, probs), **main, "default_target": DEFAULT_TARGET,
                    "default_point": point, "by_lang_at_default": by_lang},
        "knn": knn_block,
        "baselines": baselines,
        "random_cost_at": random_at,
        "sensitivity": sensitivity,
        "artifact": raw,
    }


def _usd(v: float | None, per: int = 1000) -> str:
    return "—" if v is None else f"{v * per:.3f}"


def render_markdown(r: dict) -> str:
    b, learned = r["baselines"], r["learned"]
    out = [
        "# Learned router — v1", "",
        f"{r['examples']} prompts, {r['folds']}-fold CV grouped by prompt. Costs in USD per 1000 prompts.", "",
        "## Classifiers (out-of-fold AUC)", "", "| prefix | target | all | es | en | λ |", "|---|---|---|---|---|---|",
    ]
    for prefix, res in r["prefix"]["results"].items():
        for t in TARGETS:
            a = res["auc"][t]
            out.append(f"| {prefix} | {t} | {a['all']:.3f} | {a['es']:.3f} | {a['en']:.3f} | {res['lambdas'][t]} |")
    out += ["", f"Chosen prefix: `{r['prefix']['chosen']}` (needs > {PREFIX_MARGIN} mean AUC to switch).", "",
            "## Cost at a quality level", "", "| policy | " + " | ".join(f"q ≥ {q}" for q in QUALITY_LEVELS) + " |",
            "|---|" + "---|" * len(QUALITY_LEVELS)]
    out.append("| learned (logistic) | " + " | ".join(_usd(learned["cost_at"][str(q)]) for q in QUALITY_LEVELS) + " |")
    out.append("| kNN (k=20) | " + " | ".join(_usd(r["knn"]["cost_at"][str(q)]) for q in QUALITY_LEVELS) + " |")
    out.append("| random mixture | " + " | ".join(_usd(r["random_cost_at"][str(q)]) for q in QUALITY_LEVELS) + " |")
    out += ["", "## Fixed policies", "", "| policy | cost | quality | learned at same quality | random at same quality |",
            "|---|---|---|---|---|"]
    for name, v in b.items():
        out.append(f"| {name} | {_usd(v['cost'])} | {v['quality']:.3f} | {_usd(v.get('learned_cost_at_same_quality'))} "
                   f"| {_usd(v.get('random_cost_at_same_quality'))} |")
    p = learned["default_point"]
    if p:
        out += ["", f"## Default target q ≥ {learned['default_target']}", "",
                f"τ_local {p['tau_local']:.2f}, τ_economy {p['tau_economy']:.2f}: cost {_usd(p['cost'])}, "
                f"quality {p['quality']:.3f}, share " + ", ".join(f"{k} {v:.0%}" for k, v in p["share"].items()), ""]
        for lang, v in learned["by_lang_at_default"].items():
            out.append(f"- {lang}: cost {_usd(v['cost'])}, quality {v['quality']:.3f}, share "
                       + ", ".join(f"{k} {s:.0%}" for k, s in v["share"].items()))
    out += ["", "## Label-rule sensitivity", "", "| labels | " + " | ".join(f"learned q≥{q}" for q in QUALITY_LEVELS)
            + " | all-frontier |", "|---|" + "---|" * (len(QUALITY_LEVELS) + 1)]
    for name, v in r["sensitivity"].items():
        out.append(f"| {name} | " + " | ".join(_usd(v["cost_at"][str(q)]) for q in QUALITY_LEVELS)
                   + f" | {_usd(v['all_frontier_cost'])} |")
    out += ["", "## Pareto frontier (learned)", "", "| τ_local | τ_economy | cost | quality | local | economy | frontier |",
            "|---|---|---|---|---|---|---|"]
    for p in learned["pareto"]:
        out.append(f"| {p['tau_local']:.2f} | {p['tau_economy']:.2f} | {_usd(p['cost'])} | {p['quality']:.3f} | "
                   f"{p['share']['local']:.0%} | {p['share']['economy']:.0%} | {p['share']['frontier']:.0%} |")
    return "\n".join(out) + "\n"


def thesis_block(r: dict) -> str:
    b, learned = r["baselines"], r["learned"]
    af = b["all_frontier"]["cost"]
    c95 = learned["cost_at"]["0.95"]
    r95 = r["random_cost_at"]["0.95"]
    h = b["heuristic_premium_frontier"]
    text = (
        f"El router aprendido son dos regresiones logísticas sobre el embedding del prompt "
        f"(prefijo `{r['prefix']['chosen']}`), evaluadas con validación cruzada de 5 folds agrupada por prompt "
        f"sobre {r['examples']} prompts. AUC fuera de fold: local {learned['auc']['local']['all']:.2f}, "
        f"economy {learned['auc']['economy']['all']:.2f}. "
    )
    if c95 is not None:
        text += (f"Con calidad ≥ 0.95, cuesta USD {c95 * 1000:.2f} cada mil prompts, contra USD {af * 1000:.2f} "
                 f"de enviar todo al modelo frontier ({1 - c95 / af:.0%} menos) y USD {r95 * 1000:.2f} de la mejor "
                 f"mezcla aleatoria de niveles a igual calidad. ")
    lh = h.get("learned_cost_at_same_quality")
    if lh is not None:
        text += (f"La heurística de dos reglas logra calidad {h['quality']:.2f} a USD {h['cost'] * 1000:.2f}; el router "
                 f"aprendido alcanza esa calidad a USD {lh * 1000:.2f}. ")
    text += ("El costo local se cuenta en cero y la latencia se reporta aparte. Los resultados bajo las reglas "
             "de etiquetado R1 y R2 se reportan como sensibilidad.")
    return text


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    r = run()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(r["artifact"]) + "\n", encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(
        json.dumps({k: v for k, v in r.items() if k != "artifact"}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(render_markdown(r), encoding="utf-8")
    THESIS.write_text(gt_report.replace_block(THESIS.read_text(encoding="utf-8"), "router-fase3", thesis_block(r)),
                      encoding="utf-8")
    print(render_markdown(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
